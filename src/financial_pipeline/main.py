from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import date, timedelta
from math import ceil
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

import polars as pl

from financial_pipeline.charts import (
    compute_stats,
    monthly_income_expenses_chart,
    top_expenses_chart,
    weekly_spending_chart,
)
from financial_pipeline.db import async_session, create_tables, seed_accounts
from financial_pipeline.ingest import _resolve_account, discover_importers, ingest
from financial_pipeline.models import Account, Transaction
from financial_pipeline.schemas import ImportedTransaction

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    await create_tables()
    await seed_accounts()
    yield


app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory=PROJECT_ROOT / "static"), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)


@app.get("/")
async def index():
    return RedirectResponse(url="/dashboard")


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    async with async_session() as session:
        result = await session.execute(
            select(Transaction)
            .where(Transaction.status == "approved")
            .options(selectinload(Transaction.internal), selectinload(Transaction.external))
        )
        transactions = result.scalars().all()

    if not transactions:
        return templates.TemplateResponse(request, "dashboard.html", {
            "has_data": False,
        })

    df = pl.DataFrame({
        "date": [t.date for t in transactions],
        "amount_cents": [t.amount_cents for t in transactions],
        "description": [t.description or t.raw_description for t in transactions],
        "external_name": [t.external.name for t in transactions],
        "internal_name": [t.internal.name for t in transactions],
    })

    stats = compute_stats(df)
    monthly_chart = monthly_income_expenses_chart(df)
    top_chart = top_expenses_chart(df)
    weekly_chart = weekly_spending_chart(df)

    return templates.TemplateResponse(request, "dashboard.html", {
        "has_data": True,
        "stats": stats,
        "monthly_chart": monthly_chart,
        "top_chart": top_chart,
        "weekly_chart": weekly_chart,
    })


@app.get("/upload", response_class=HTMLResponse)
async def upload_page(request: Request):
    importers = discover_importers()
    async with async_session() as session:
        result = await session.execute(select(Account).where(Account.kind != "external"))
        accounts = result.scalars().all()
    return templates.TemplateResponse(request, "upload.html", {
        "importers": importers,
        "accounts": accounts,
    })


@app.post("/upload")
async def upload_file(request: Request):
    form = await request.form()
    importer_key = form.get("importer")
    account = form.get("account")
    file: UploadFile = form.get("file")

    try:
        importers = discover_importers()
        if importer_key not in importers:
            raise ValueError(f"Unknown importer: {importer_key}")

        importer_info = importers[importer_key]
        blob = await file.read()
        df = importer_info.parse(blob)
        df = ImportedTransaction.validate(df)
        await ingest(df, internal_account=account, importer_name=importer_info.name, filename=file.filename)

        return Response(status_code=200, headers={"HX-Redirect": "/inbox"})
    except Exception as e:
        return HTMLResponse(
            f'<div class="alert alert-error">{e}</div>',
            status_code=422,
        )


@app.get("/inbox", response_class=HTMLResponse)
async def inbox_page(request: Request):
    async with async_session() as session:
        result = await session.execute(
            select(Transaction)
            .where(Transaction.status == "pending")
            .options(selectinload(Transaction.internal), selectinload(Transaction.external))
            .order_by(Transaction.date)
        )
        transactions = result.scalars().all()
    return templates.TemplateResponse(request, "inbox.html", {"transactions": transactions})


@app.patch("/transactions/{txn_id}", response_class=HTMLResponse)
async def update_transaction(txn_id: int, request: Request):
    form = await request.form()
    async with async_session() as session:
        txn = await session.get(Transaction, txn_id, options=[selectinload(Transaction.internal), selectinload(Transaction.external)])
        if txn is None:
            return HTMLResponse("Not found", status_code=404)

        if "description" in form:
            txn.description = form["description"] or None

        if "external" in form:
            new_name = form["external"].strip()
            if new_name and new_name != txn.external.name:
                account = await _resolve_account(session, new_name)
                txn.external_id = account.id
                txn.external = account

        if "marked_for_approval" in form:
            if form["marked_for_approval"] == "toggle":
                txn.marked_for_approval = not txn.marked_for_approval
            else:
                txn.marked_for_approval = form["marked_for_approval"] == "true"

        await session.commit()
        await session.refresh(txn, ["internal", "external"])
        return templates.TemplateResponse(request, "_inbox_row.html", {"txn": txn})


@app.get("/transactions/{txn_id}/edit-description", response_class=HTMLResponse)
async def edit_description(txn_id: int):
    async with async_session() as session:
        txn = await session.get(Transaction, txn_id)
    return HTMLResponse(f'''<input type="text" class="input input-bordered input-sm w-full"
        name="description" value="{txn.description or ''}"
        hx-patch="/transactions/{txn_id}" hx-target="#txn-{txn_id}" hx-swap="outerHTML"
        hx-trigger="blur, keyup[key=='Enter']" autofocus>''')


@app.get("/transactions/{txn_id}/edit-external", response_class=HTMLResponse)
async def edit_external(txn_id: int):
    async with async_session() as session:
        txn = await session.get(Transaction, txn_id, options=[selectinload(Transaction.external)])
    return HTMLResponse(f'''<input type="text" class="input input-bordered input-sm w-full"
        name="external" value="{txn.external.name}"
        hx-patch="/transactions/{txn_id}" hx-target="#txn-{txn_id}" hx-swap="outerHTML"
        hx-trigger="blur, keyup[key=='Enter']" autofocus>''')


@app.post("/inbox/commit", response_class=HTMLResponse)
async def commit_inbox(request: Request):
    async with async_session() as session:
        result = await session.execute(
            select(Transaction).where(
                Transaction.status == "pending",
                Transaction.marked_for_approval == True,
            )
        )
        marked = result.scalars().all()

        if not marked:
            return HTMLResponse('<div class="alert alert-warning my-2">Nothing to commit — no transactions marked for approval.</div>')

        for txn in marked:
            txn.status = "approved"
            txn.marked_for_approval = False
        await session.commit()

        # Prune orphaned external accounts
        from sqlalchemy import exists as sa_exists
        orphans = (await session.execute(
            select(Account).where(
                Account.kind == "external",
                ~sa_exists(select(Transaction.id).where(Transaction.external_id == Account.id)),
                ~sa_exists(select(Transaction.id).where(Transaction.internal_id == Account.id)),
            )
        )).scalars().all()
        for orphan in orphans:
            await session.delete(orphan)
        await session.commit()

    # Re-render remaining pending transactions
    async with async_session() as session:
        result = await session.execute(
            select(Transaction)
            .where(Transaction.status == "pending")
            .options(selectinload(Transaction.internal), selectinload(Transaction.external))
            .order_by(Transaction.date)
        )
        transactions = result.scalars().all()

    if not transactions:
        return HTMLResponse('<tr><td colspan="7" class="text-center py-8">Inbox is empty. <a href="/upload" class="link link-primary">Upload transactions</a></td></tr>')

    rows = ""
    for txn in transactions:
        rows += templates.get_template("_inbox_row.html").render({"txn": txn})
    return HTMLResponse(rows)


def _compute_date_range(preset: str, date_from: str | None, date_to: str | None) -> tuple[date, date]:
    today = date.today()
    if preset == "last_month":
        first_of_this_month = today.replace(day=1)
        last_month_end = first_of_this_month - timedelta(days=1)
        return last_month_end.replace(day=1), last_month_end
    elif preset == "last_3_months":
        three_months_ago = today.replace(day=1)
        for _ in range(3):
            three_months_ago = (three_months_ago - timedelta(days=1)).replace(day=1)
        return three_months_ago, today
    elif preset == "custom" and date_from and date_to:
        return date.fromisoformat(date_from), date.fromisoformat(date_to)
    # Default: YTD
    return today.replace(month=1, day=1), today


SORT_COLUMNS = {
    "date": Transaction.date,
    "amount": Transaction.amount_cents,
    "description": Transaction.raw_description,
}


@app.get("/transactions", response_class=HTMLResponse)
async def transactions_page(request: Request):
    params = request.query_params

    preset = params.get("preset", "ytd")
    date_from_str = params.get("date_from")
    date_to_str = params.get("date_to")
    sort_col = params.get("sort", "date")
    sort_dir = params.get("dir", "desc")
    internal_filter = params.get("internal", "")
    external_filter = params.get("external", "")
    page = int(params.get("page", "1"))
    page_size = int(params.get("page_size", "25"))

    date_from, date_to = _compute_date_range(preset, date_from_str, date_to_str)

    async with async_session() as session:
        query = (
            select(Transaction)
            .where(Transaction.status == "approved")
            .where(Transaction.date >= date_from)
            .where(Transaction.date <= date_to)
            .options(selectinload(Transaction.internal), selectinload(Transaction.external))
        )

        if internal_filter:
            query = query.join(Transaction.internal).where(Account.name == internal_filter)
        if external_filter:
            query = query.join(Transaction.external).where(Account.name == external_filter)

        col = SORT_COLUMNS.get(sort_col, Transaction.date)
        if sort_dir == "asc":
            query = query.order_by(col.asc())
        else:
            query = query.order_by(col.desc())

        # Count total for pagination
        count_query = (
            select(func.count())
            .select_from(Transaction)
            .where(Transaction.status == "approved")
            .where(Transaction.date >= date_from)
            .where(Transaction.date <= date_to)
        )
        if internal_filter:
            count_query = count_query.join(Transaction.internal).where(Account.name == internal_filter)
        if external_filter:
            count_query = count_query.join(Transaction.external).where(Account.name == external_filter)
        total_count = await session.scalar(count_query)

        total_pages = max(1, ceil(total_count / page_size))
        page = min(page, total_pages)
        offset = (page - 1) * page_size

        result = await session.execute(query.offset(offset).limit(page_size))
        transactions = result.scalars().all()

        # Get account lists for filter dropdowns
        int_result = await session.execute(
            select(Account.name).where(Account.kind != "external").order_by(Account.name)
        )
        internal_accounts = [r[0] for r in int_result]

        ext_result = await session.execute(
            select(Account.name).where(Account.kind == "external").order_by(Account.name)
        )
        external_accounts = [r[0] for r in ext_result]

    ctx = {
        "request": request,
        "transactions": transactions,
        "preset": preset,
        "date_from": str(date_from),
        "date_to": str(date_to),
        "sort": sort_col,
        "dir": sort_dir,
        "internal_filter": internal_filter,
        "external_filter": external_filter,
        "internal_accounts": internal_accounts,
        "external_accounts": external_accounts,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "total_count": total_count,
    }

    is_htmx = request.headers.get("HX-Request") == "true"
    if is_htmx:
        return templates.TemplateResponse(request, "_txn_table_body.html", ctx)
    return templates.TemplateResponse(request, "transactions.html", ctx)


if __name__ == "__main__":
    uvicorn.run("financial_pipeline.main:app", host="127.0.0.1", port=8097, reload=True)
