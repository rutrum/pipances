from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from sqlalchemy import select
from sqlalchemy.orm import selectinload

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
    return RedirectResponse(url="/inbox")


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


if __name__ == "__main__":
    uvicorn.run("financial_pipeline.main:app", host="127.0.0.1", port=8097, reload=True)
