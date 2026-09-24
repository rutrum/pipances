from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from pipances.db import Database, DatabaseDep
from pipances.db.categories import get_categories, get_or_create_category
from pipances.db.transactions import (
    get_txn,
    remaining_split_capacity,
)
from pipances.models import (
    Transaction,
    TransactionSplit,
)
from pipances.routes._utils import templates

router = APIRouter()


async def _render_splits_section(
    request: Request, txn: Transaction, database: Database
) -> str:
    """Render the splits section partial for the given transaction."""
    async with database.session() as session:
        categories = await get_categories(session)
        # Re-attach txn to load its category relationship
        fetched = await get_txn(session, txn.id, splits=True)
        if fetched is None:
            raise RuntimeError(f"Transaction {txn.id} not found")
        txn = fetched
    categories_data = [{"id": c.id, "name": c.name} for c in categories]
    return templates.get_template("shared/_splits_section.jinja2").render(
        {"txn": txn, "categories": categories, "categories_data": categories_data}
    )


@router.post("/transactions/{txn_id}/splits", response_class=HTMLResponse)
async def create_split(
    txn_id: int,
    request: Request,
    database: DatabaseDep,
) -> HTMLResponse:
    form = await request.form()
    async with database.session() as session:
        txn = await get_txn(session, txn_id, splits=True)
        if txn is None:
            return HTMLResponse("Not found", status_code=404)

        try:
            amount_dollars = float(str(form.get("amount_dollars", "0")))
        except (ValueError, TypeError):
            return HTMLResponse("Invalid amount", status_code=422)
        amount_cents = round(amount_dollars * 100)

        if amount_cents <= 0:
            return HTMLResponse("Amount must be positive", status_code=422)

        if amount_cents >= remaining_split_capacity(txn):
            return HTMLResponse("Amount would eliminate remainder", status_code=422)

        category_id_val = str(form.get("category_id", "")).strip()
        category_id = None
        if category_id_val:
            try:
                category_id = int(category_id_val)
            except (ValueError, TypeError):
                cat = await get_or_create_category(session, category_id_val)
                category_id = cat.id

        split = TransactionSplit(
            transaction_id=txn_id,
            category_id=category_id,
            amount_cents=amount_cents,
        )
        session.add(split)
        await session.commit()
        await session.refresh(txn, ["splits"])

    html = await _render_splits_section(request, txn, database)
    return HTMLResponse(html)


@router.patch("/transactions/{txn_id}/splits/{split_id}", response_class=HTMLResponse)
async def update_split(
    txn_id: int,
    split_id: int,
    request: Request,
    database: DatabaseDep,
) -> HTMLResponse:
    form = await request.form()
    async with database.session() as session:
        split = await session.get(TransactionSplit, split_id)
        if split is None or split.transaction_id != txn_id:
            return HTMLResponse("Not found", status_code=404)

        txn = await get_txn(session, txn_id, splits=True)
        if txn is None:
            return HTMLResponse("Not found", status_code=404)

        if "amount_dollars" in form:
            try:
                amount_dollars = float(str(form["amount_dollars"]))
            except (ValueError, TypeError):
                return HTMLResponse("Invalid amount", status_code=422)
            amount_cents = round(amount_dollars * 100)
            if amount_cents <= 0:
                return HTMLResponse("Amount must be positive", status_code=422)

            if amount_cents >= remaining_split_capacity(
                txn, excluding_split_id=split_id
            ):
                return HTMLResponse("Amount would eliminate remainder", status_code=422)
            split.amount_cents = amount_cents

        if "category_id" in form:
            category_id_val = str(form["category_id"]).strip()
            if category_id_val:
                try:
                    split.category_id = int(category_id_val)
                except (ValueError, TypeError):
                    cat = await get_or_create_category(session, category_id_val)
                    split.category_id = cat.id
            else:
                split.category_id = None

        await session.commit()
        await session.refresh(txn, ["splits"])

    html = await _render_splits_section(request, txn, database)
    return HTMLResponse(html)


@router.delete("/transactions/{txn_id}/splits/{split_id}", response_class=HTMLResponse)
async def delete_split(
    txn_id: int,
    split_id: int,
    request: Request,
    database: DatabaseDep,
) -> HTMLResponse:
    async with database.session() as session:
        split = await session.get(TransactionSplit, split_id)
        if split is None or split.transaction_id != txn_id:
            return HTMLResponse("Not found", status_code=404)

        txn = await get_txn(session, txn_id, splits=True)
        if txn is None:
            return HTMLResponse("Not found", status_code=404)

        await session.delete(split)
        await session.commit()
        await session.refresh(txn, ["splits"])

    html = await _render_splits_section(request, txn, database)
    return HTMLResponse(html)
