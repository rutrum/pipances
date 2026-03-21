from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import date, timedelta
from math import ceil
from pathlib import Path

import polars as pl
import uvicorn
from fastapi import FastAPI, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from financial_pipeline.charts import (
    compute_stats,
    monthly_income_expenses_chart,
    top_expenses_chart,
    weekly_spending_chart,
)
from financial_pipeline.db import async_session, create_tables
from financial_pipeline.ingest import _resolve_account, discover_importers, ingest
from financial_pipeline.models import Account, Category, Transaction
from financial_pipeline.schemas import ImportedTransaction

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    await create_tables()
    yield


app = FastAPI(lifespan=lifespan)
app.mount(
    "/static",
    StaticFiles(directory=PROJECT_ROOT / "static", follow_symlink=True),
    name="static",
)
templates = Jinja2Templates(directory=TEMPLATES_DIR)


async def shared_context(active_page: str, session) -> dict:
    """Return shared template context: active page and inbox count."""
    count = await session.scalar(
        select(func.count())
        .select_from(Transaction)
        .where(Transaction.status == "pending")
    )
    return {"active_page": active_page, "inbox_count": count}


@app.get("/")
async def index():
    return RedirectResponse(url="/dashboard")


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    async with async_session() as session:
        shared = await shared_context("dashboard", session)
        result = await session.execute(
            select(Transaction)
            .where(Transaction.status == "approved")
            .options(
                selectinload(Transaction.internal), selectinload(Transaction.external)
            )
        )
        transactions = result.scalars().all()

    if not transactions:
        return templates.TemplateResponse(
            request,
            "dashboard.html",
            {
                "has_data": False,
                **shared,
            },
        )

    df = pl.DataFrame(
        {
            "date": [t.date for t in transactions],
            "amount_cents": [t.amount_cents for t in transactions],
            "description": [t.description or t.raw_description for t in transactions],
            "external_name": [t.external.name for t in transactions],
            "internal_name": [t.internal.name for t in transactions],
        }
    )

    stats = compute_stats(df)
    monthly_chart = monthly_income_expenses_chart(df)
    top_chart = top_expenses_chart(df)
    weekly_chart = weekly_spending_chart(df)

    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "has_data": True,
            "stats": stats,
            "monthly_chart": monthly_chart,
            "top_chart": top_chart,
            "weekly_chart": weekly_chart,
            **shared,
        },
    )


@app.get("/upload", response_class=HTMLResponse)
async def upload_page(request: Request):
    importers = discover_importers()
    async with async_session() as session:
        shared = await shared_context("upload", session)
        result = await session.execute(
            select(Account).where(Account.kind != "external", Account.active == True)
        )
        accounts = result.scalars().all()
    return templates.TemplateResponse(
        request,
        "upload.html",
        {
            "importers": importers,
            "accounts": accounts,
            **shared,
        },
    )


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
        await ingest(
            df,
            internal_account=account,
            importer_name=importer_info.name,
            filename=file.filename,
        )

        return Response(
            status_code=200, headers={"HX-Redirect": "/inbox?toast=upload_success"}
        )
    except Exception as e:
        return HTMLResponse(
            f'<div class="alert alert-error">{e}</div>',
            status_code=422,
        )


@app.get("/settings")
async def settings_redirect():
    return RedirectResponse(url="/settings/accounts")


@app.get("/settings/accounts", response_class=HTMLResponse)
async def settings_accounts_page(request: Request):
    show_closed = request.query_params.get("show_closed", "false") == "true"
    async with async_session() as session:
        shared = await shared_context("settings", session)
        query = select(Account).where(Account.kind != "external").order_by(Account.name)
        if not show_closed:
            query = query.where(Account.active == True)
        result = await session.execute(query)
        accounts = result.scalars().all()

    is_htmx = request.headers.get("HX-Request") == "true"
    if is_htmx:
        rows = ""
        for account in accounts:
            rows += templates.get_template("_account_row.html").render(
                {"account": account, "show_closed": show_closed}
            )
        rows += templates.get_template("_account_input_row.html").render()
        return HTMLResponse(rows)

    return templates.TemplateResponse(
        request,
        "settings_accounts.html",
        {
            "accounts": accounts,
            "settings_tab": "accounts",
            "show_closed": show_closed,
            **shared,
        },
    )


@app.post("/settings/accounts", response_class=HTMLResponse)
async def create_account(request: Request):
    form = await request.form()
    name = form.get("name", "").strip()
    kind = form.get("kind", "").strip()
    balance_str = form.get("starting_balance", "").strip()
    balance_date_str = form.get("balance_date", "").strip()

    if not name or not kind:
        return HTMLResponse(
            '<div class="alert alert-error alert-sm">Name and type are required.</div>',
            status_code=422,
        )

    if kind.lower() == "external":
        return HTMLResponse(
            '<div class="alert alert-error alert-sm">Account type cannot be "external".</div>',
            status_code=422,
        )

    starting_balance_cents = 0
    if balance_str:
        starting_balance_cents = int(round(float(balance_str) * 100))

    balance_date = None
    if balance_date_str:
        balance_date = date.fromisoformat(balance_date_str)

    async with async_session() as session:
        account = Account(
            name=name,
            kind=kind,
            starting_balance_cents=starting_balance_cents,
            balance_date=balance_date,
            active=True,
        )
        session.add(account)
        try:
            await session.commit()
        except IntegrityError:
            return HTMLResponse(
                '<div class="alert alert-error alert-sm">An account with that name already exists.</div>',
                status_code=422,
            )
        await session.refresh(account)

    return HTMLResponse(
        templates.get_template("_account_row.html").render({"account": account})
    )


@app.patch("/accounts/{account_id}", response_class=HTMLResponse)
async def update_account(account_id: int, request: Request):
    form = await request.form()
    async with async_session() as session:
        account = await session.get(Account, account_id)
        if account is None:
            return HTMLResponse("Not found", status_code=404)

        if "name" in form:
            new_name = form["name"].strip()
            if new_name:
                account.name = new_name

        if "kind" in form:
            new_kind = form["kind"].strip()
            if new_kind.lower() == "external":
                return HTMLResponse(
                    '<div class="alert alert-error alert-sm">Account type cannot be "external".</div>',
                    status_code=422,
                )
            if new_kind:
                account.kind = new_kind

        if "starting_balance" in form:
            bal = form["starting_balance"].strip()
            if bal:
                account.starting_balance_cents = int(round(float(bal) * 100))
            else:
                account.starting_balance_cents = 0

        if "balance_date" in form:
            bd = form["balance_date"].strip()
            account.balance_date = date.fromisoformat(bd) if bd else None

        if "active" in form:
            account.active = form["active"] == "true"

        try:
            await session.commit()
        except IntegrityError:
            await session.rollback()
            return HTMLResponse(
                '<div class="alert alert-error alert-sm">An account with that name already exists.</div>',
                status_code=422,
            )
        await session.refresh(account)

    show_closed = request.query_params.get("show_closed", "false") == "true"
    if not account.active and not show_closed:
        return HTMLResponse("")

    return HTMLResponse(
        templates.get_template("_account_row.html").render(
            {"account": account, "show_closed": show_closed}
        )
    )


@app.get("/accounts/{account_id}/edit-name", response_class=HTMLResponse)
async def edit_account_name(account_id: int):
    async with async_session() as session:
        account = await session.get(Account, account_id)
    return HTMLResponse(
        f'<input type="text" class="input input-bordered input-sm w-full" '
        f'name="name" value="{account.name}" '
        f'hx-patch="/accounts/{account_id}" hx-target="#account-{account_id}" hx-swap="outerHTML" '
        f"hx-trigger=\"blur, keyup[key=='Enter']\" autofocus>"
    )


@app.get("/accounts/{account_id}/edit-type", response_class=HTMLResponse)
async def edit_account_type(account_id: int):
    async with async_session() as session:
        account = await session.get(Account, account_id)
    return HTMLResponse(
        f'<input type="text" class="input input-bordered input-sm w-full" '
        f'name="kind" value="{account.kind}" '
        f'hx-patch="/accounts/{account_id}" hx-target="#account-{account_id}" hx-swap="outerHTML" '
        f"hx-trigger=\"blur, keyup[key=='Enter']\" autofocus>"
    )


@app.get("/accounts/{account_id}/edit-balance", response_class=HTMLResponse)
async def edit_account_balance(account_id: int):
    async with async_session() as session:
        account = await session.get(Account, account_id)
    value = f"{account.starting_balance_cents / 100:.2f}"
    return HTMLResponse(
        f'<input type="number" step="0.01" class="input input-bordered input-sm w-full" '
        f'name="starting_balance" value="{value}" '
        f'hx-patch="/accounts/{account_id}" hx-target="#account-{account_id}" hx-swap="outerHTML" '
        f"hx-trigger=\"blur, keyup[key=='Enter']\" autofocus>"
    )


@app.get("/accounts/{account_id}/edit-balance-date", response_class=HTMLResponse)
async def edit_account_balance_date(account_id: int):
    async with async_session() as session:
        account = await session.get(Account, account_id)
    value = str(account.balance_date) if account.balance_date else ""
    return HTMLResponse(
        f'<input type="date" class="input input-bordered input-sm w-full" '
        f'name="balance_date" value="{value}" '
        f'hx-patch="/accounts/{account_id}" hx-target="#account-{account_id}" hx-swap="outerHTML" '
        f'hx-trigger="blur, change" autofocus>'
    )


@app.get("/settings/categories", response_class=HTMLResponse)
async def settings_categories_page(request: Request):
    async with async_session() as session:
        shared = await shared_context("settings", session)
        result = await session.execute(select(Category).order_by(Category.name))
        categories = result.scalars().all()

    return templates.TemplateResponse(
        request,
        "settings_categories.html",
        {
            "categories": categories,
            "settings_tab": "categories",
            **shared,
        },
    )


@app.post("/settings/categories", response_class=HTMLResponse)
async def create_category(request: Request):
    form = await request.form()
    name = form.get("name", "").strip()

    if not name:
        return HTMLResponse(
            '<div class="alert alert-error alert-sm">Name is required.</div>',
            status_code=422,
        )

    async with async_session() as session:
        category = Category(name=name)
        session.add(category)
        try:
            await session.commit()
        except IntegrityError:
            return HTMLResponse(
                '<div class="alert alert-error alert-sm">A category with that name already exists.</div>',
                status_code=422,
            )
        await session.refresh(category)

    return HTMLResponse(
        templates.get_template("_category_row.html").render({"category": category})
    )


@app.patch("/categories/{category_id}", response_class=HTMLResponse)
async def update_category(category_id: int, request: Request):
    form = await request.form()
    async with async_session() as session:
        category = await session.get(Category, category_id)
        if category is None:
            return HTMLResponse("Not found", status_code=404)

        if "name" in form:
            new_name = form["name"].strip()
            if new_name:
                category.name = new_name

        try:
            await session.commit()
        except IntegrityError:
            await session.rollback()
            return HTMLResponse(
                '<div class="alert alert-error alert-sm">A category with that name already exists.</div>',
                status_code=422,
            )
        await session.refresh(category)

    return HTMLResponse(
        templates.get_template("_category_row.html").render({"category": category})
    )


@app.delete("/categories/{category_id}", response_class=HTMLResponse)
async def delete_category(category_id: int):
    async with async_session() as session:
        category = await session.get(Category, category_id)
        if category is None:
            return HTMLResponse("Not found", status_code=404)

        # Set NULL on transactions referencing this category
        await session.execute(
            Transaction.__table__.update()
            .where(Transaction.category_id == category_id)
            .values(category_id=None)
        )
        await session.delete(category)
        await session.commit()

    return HTMLResponse("")


@app.get("/categories/{category_id}/edit-name", response_class=HTMLResponse)
async def edit_category_name(category_id: int):
    async with async_session() as session:
        category = await session.get(Category, category_id)
    return HTMLResponse(
        f'<input type="text" class="input input-bordered input-sm w-full" '
        f'name="name" value="{category.name}" '
        f'hx-patch="/categories/{category_id}" hx-target="#category-{category_id}" hx-swap="outerHTML" '
        f"hx-trigger=\"blur, keyup[key=='Enter']\" autofocus>"
    )


@app.get("/api/combo/{entity}", response_class=HTMLResponse)
async def combo_search(entity: str, request: Request):
    q = request.query_params.get("q", "").strip()
    txn_id = request.query_params.get("txn_id", "")
    field_name = request.query_params.get("field", "")

    async with async_session() as session:
        if entity == "categories":
            query = select(Category).order_by(Category.name)
            if q:
                query = query.where(Category.name.ilike(f"%{q}%"))
            result = await session.execute(query.limit(5))
            items = [{"id": c.id, "name": c.name} for c in result.scalars().all()]
            exact_match = (
                any(item["name"].lower() == q.lower() for item in items) if q else True
            )
        elif entity == "external-accounts":
            query = (
                select(Account).where(Account.kind == "external").order_by(Account.name)
            )
            if q:
                query = query.where(Account.name.ilike(f"%{q}%"))
            result = await session.execute(query.limit(5))
            items = [{"id": a.id, "name": a.name} for a in result.scalars().all()]
            exact_match = (
                any(item["name"].lower() == q.lower() for item in items) if q else True
            )
        else:
            return HTMLResponse("Unknown entity", status_code=404)

    return templates.TemplateResponse(
        request,
        "_combo_results.html",
        {
            "items": items,
            "query": q,
            "exact_match": exact_match,
            "txn_id": txn_id,
            "field_name": field_name,
            "entity": entity,
        },
    )


@app.get("/inbox", response_class=HTMLResponse)
async def inbox_page(request: Request):
    async with async_session() as session:
        shared = await shared_context("inbox", session)
        result = await session.execute(
            select(Transaction)
            .where(Transaction.status == "pending")
            .options(
                selectinload(Transaction.internal),
                selectinload(Transaction.external),
                selectinload(Transaction.category),
            )
            .order_by(Transaction.date)
        )
        transactions = result.scalars().all()
    toast = request.query_params.get("toast")
    return templates.TemplateResponse(
        request,
        "inbox.html",
        {
            "transactions": transactions,
            "toast": toast,
            **shared,
        },
    )


@app.patch("/transactions/{txn_id}", response_class=HTMLResponse)
async def update_transaction(txn_id: int, request: Request):
    form = await request.form()
    async with async_session() as session:
        txn = await session.get(
            Transaction,
            txn_id,
            options=[
                selectinload(Transaction.internal),
                selectinload(Transaction.external),
                selectinload(Transaction.category),
            ],
        )
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

        if "category" in form:
            cat_name = form["category"].strip()
            if cat_name:
                result = await session.execute(
                    select(Category).where(
                        func.lower(Category.name) == cat_name.lower()
                    )
                )
                category = result.scalar_one_or_none()
                if category is None:
                    category = Category(name=cat_name)
                    session.add(category)
                    await session.flush()
                txn.category_id = category.id
                txn.category = category
            else:
                txn.category_id = None
                txn.category = None

        if "marked_for_approval" in form:
            if form["marked_for_approval"] == "toggle":
                txn.marked_for_approval = not txn.marked_for_approval
            else:
                txn.marked_for_approval = form["marked_for_approval"] == "true"

        await session.commit()
        await session.refresh(txn, ["internal", "external", "category"])
        return templates.TemplateResponse(request, "_inbox_row.html", {"txn": txn})


@app.get("/transactions/{txn_id}/edit-description", response_class=HTMLResponse)
async def edit_description(txn_id: int):
    async with async_session() as session:
        txn = await session.get(Transaction, txn_id)
    return HTMLResponse(f'''<input type="text" class="input input-bordered input-sm w-full"
        name="description" value="{txn.description or ""}"
        hx-patch="/transactions/{txn_id}" hx-target="#txn-{txn_id}" hx-swap="outerHTML"
        hx-trigger="blur, keyup[key=='Enter']" autofocus>''')


@app.get("/transactions/{txn_id}/edit-external", response_class=HTMLResponse)
async def edit_external(txn_id: int, request: Request):
    async with async_session() as session:
        txn = await session.get(
            Transaction, txn_id, options=[selectinload(Transaction.external)]
        )
    return templates.TemplateResponse(
        request,
        "_combo_edit.html",
        {
            "current_value": txn.external.name,
            "entity": "external-accounts",
            "txn_id": txn_id,
            "field_name": "external",
        },
    )


@app.get("/transactions/{txn_id}/edit-category", response_class=HTMLResponse)
async def edit_category(txn_id: int, request: Request):
    async with async_session() as session:
        txn = await session.get(
            Transaction, txn_id, options=[selectinload(Transaction.category)]
        )
    current_value = txn.category.name if txn.category else ""
    return templates.TemplateResponse(
        request,
        "_combo_edit.html",
        {
            "current_value": current_value,
            "entity": "categories",
            "txn_id": txn_id,
            "field_name": "category",
        },
    )


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
            toast = '<div id="toast-container" hx-swap-oob="innerHTML:#toast-container"><div class="alert alert-warning"><span>Nothing to commit — no transactions are marked.</span></div></div>'
            remaining = await session.execute(
                select(Transaction)
                .where(Transaction.status == "pending")
                .options(
                    selectinload(Transaction.internal),
                    selectinload(Transaction.external),
                    selectinload(Transaction.category),
                )
                .order_by(Transaction.date)
            )
            rows = ""
            for txn in remaining.scalars().all():
                rows += templates.get_template("_inbox_row.html").render({"txn": txn})
            return HTMLResponse(rows + toast)

        committed_count = len(marked)
        for txn in marked:
            txn.status = "approved"
            txn.marked_for_approval = False
        await session.commit()

        # Prune orphaned external accounts
        from sqlalchemy import exists as sa_exists

        orphans = (
            (
                await session.execute(
                    select(Account).where(
                        Account.kind == "external",
                        ~sa_exists(
                            select(Transaction.id).where(
                                Transaction.external_id == Account.id
                            )
                        ),
                        ~sa_exists(
                            select(Transaction.id).where(
                                Transaction.internal_id == Account.id
                            )
                        ),
                    )
                )
            )
            .scalars()
            .all()
        )
        for orphan in orphans:
            await session.delete(orphan)
        await session.commit()

    # Re-render remaining pending transactions
    async with async_session() as session:
        result = await session.execute(
            select(Transaction)
            .where(Transaction.status == "pending")
            .options(
                selectinload(Transaction.internal),
                selectinload(Transaction.external),
                selectinload(Transaction.category),
            )
            .order_by(Transaction.date)
        )
        transactions = result.scalars().all()

    remaining_count = len(transactions)
    badge_html = (
        f'<span class="badge badge-sm badge-primary">{remaining_count}</span>'
        if remaining_count
        else ""
    )
    badge_oob = f'<span id="inbox-badge" hx-swap-oob="innerHTML:#inbox-badge">{badge_html}</span>'
    toast = f'<div id="toast-container" hx-swap-oob="innerHTML:#toast-container"><div class="alert alert-success"><span>Committed {committed_count} transaction{"s" if committed_count != 1 else ""}.</span></div></div>'
    oob = toast + badge_oob

    if not transactions:
        return HTMLResponse(
            f'<tr><td colspan="8" class="text-center py-8">Inbox is empty. <a href="/upload" class="link link-primary">Upload transactions</a></td></tr>{oob}'
        )

    rows = ""
    for txn in transactions:
        rows += templates.get_template("_inbox_row.html").render({"txn": txn})
    return HTMLResponse(rows + oob)


def _compute_date_range(
    preset: str, date_from: str | None, date_to: str | None
) -> tuple[date, date]:
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
    category_filter = params.get("category", "")
    page = int(params.get("page", "1"))
    page_size = int(params.get("page_size", "25"))

    date_from, date_to = _compute_date_range(preset, date_from_str, date_to_str)

    async with async_session() as session:
        query = (
            select(Transaction)
            .where(Transaction.status == "approved")
            .where(Transaction.date >= date_from)
            .where(Transaction.date <= date_to)
            .options(
                selectinload(Transaction.internal),
                selectinload(Transaction.external),
                selectinload(Transaction.category),
            )
        )

        if internal_filter:
            query = query.join(Transaction.internal).where(
                Account.name == internal_filter
            )
        if external_filter:
            query = query.join(Transaction.external).where(
                Account.name == external_filter
            )
        if category_filter == "__uncategorized__":
            query = query.where(Transaction.category_id.is_(None))
        elif category_filter:
            query = query.join(Transaction.category).where(
                Category.name == category_filter
            )

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
            count_query = count_query.join(Transaction.internal).where(
                Account.name == internal_filter
            )
        if external_filter:
            count_query = count_query.join(Transaction.external).where(
                Account.name == external_filter
            )
        if category_filter == "__uncategorized__":
            count_query = count_query.where(Transaction.category_id.is_(None))
        elif category_filter:
            count_query = count_query.join(Transaction.category).where(
                Category.name == category_filter
            )
        total_count = await session.scalar(count_query)

        total_pages = max(1, ceil(total_count / page_size))
        page = min(page, total_pages)
        offset = (page - 1) * page_size

        result = await session.execute(query.offset(offset).limit(page_size))
        transactions = result.scalars().all()

        # Get account lists for filter dropdowns
        int_result = await session.execute(
            select(Account.name)
            .where(Account.kind != "external")
            .order_by(Account.name)
        )
        internal_accounts = [r[0] for r in int_result]

        ext_result = await session.execute(
            select(Account.name)
            .where(Account.kind == "external")
            .order_by(Account.name)
        )
        external_accounts = [r[0] for r in ext_result]

        # Get category names for filter dropdown (only those with approved txns)
        cat_result = await session.execute(
            select(Category.name)
            .join(Transaction, Transaction.category_id == Category.id)
            .where(Transaction.status == "approved")
            .distinct()
            .order_by(Category.name)
        )
        category_options = [r[0] for r in cat_result]

        shared = await shared_context("transactions", session)

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
        "category_filter": category_filter,
        "internal_accounts": internal_accounts,
        "external_accounts": external_accounts,
        "category_options": category_options,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "total_count": total_count,
    }

    is_htmx = request.headers.get("HX-Request") == "true"
    if is_htmx:
        return templates.TemplateResponse(request, "_txn_table_body.html", ctx)

    ctx |= shared
    return templates.TemplateResponse(request, "transactions.html", ctx)


if __name__ == "__main__":
    uvicorn.run("financial_pipeline.main:app", host="127.0.0.1", port=8097, reload=True)
