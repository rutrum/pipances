from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from pipances.db import async_session
from pipances.ingest import _resolve_account
from pipances.models import (
    Category,
    Transaction,
)
from pipances.routes._utils import templates

router = APIRouter()

SORT_COLUMNS = {
    "date": Transaction.date,
    "amount": Transaction.amount_cents,
    "description": Transaction.raw_description,
}


@router.patch("/transactions/bulk", response_class=HTMLResponse)
async def bulk_update_transactions(request: Request):
    body = await request.json()
    ids = body.get("ids", [])
    if not ids:
        return HTMLResponse("No IDs provided", status_code=400)

    ids = [int(i) for i in ids]

    async with async_session() as session:
        result = await session.execute(
            select(Transaction)
            .where(Transaction.id.in_(ids))
            .options(
                selectinload(Transaction.internal),
                selectinload(Transaction.external),
                selectinload(Transaction.category),
            )
        )
        transactions = result.scalars().all()

        # Resolve category once if provided
        category_name = body.get("category", "").strip()
        category_obj = None
        if category_name:
            cat_result = await session.execute(
                select(Category).where(
                    func.lower(Category.name) == category_name.lower()
                )
            )
            category_obj = cat_result.scalar_one_or_none()
            if category_obj is None:
                category_obj = Category(name=category_name)
                session.add(category_obj)
                await session.flush()

        # Resolve external account once if provided
        external_name = body.get("external", "").strip()
        external_obj = None
        if external_name:
            external_obj = await _resolve_account(session, external_name)

        description = body.get("description", "").strip()
        approve = body.get("marked_for_approval")

        for txn in transactions:
            if description:
                txn.description = description
                txn.ml_confidence_description = None
            if category_obj:
                txn.category_id = category_obj.id
                txn.category = category_obj
                txn.ml_confidence_category = None
            if external_obj:
                txn.external_id = external_obj.id
                txn.external = external_obj
                txn.ml_confidence_external = None
            if approve == "true" and txn.description:
                txn.marked_for_approval = True

        await session.commit()

        # Re-fetch to get fresh relationships
        result = await session.execute(
            select(Transaction)
            .where(Transaction.id.in_(ids))
            .options(
                selectinload(Transaction.internal),
                selectinload(Transaction.external),
                selectinload(Transaction.category),
            )
        )
        transactions = result.scalars().all()

    # Return OOB swaps for each affected row
    html = ""
    for txn in transactions:
        row = templates.get_template("inbox/_inbox_row.html").render({"txn": txn})
        html += row
    return HTMLResponse(html)


@router.patch("/transactions/{txn_id}", response_class=HTMLResponse)
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
            txn.ml_confidence_description = None

        if "external" in form:
            new_name = form["external"].strip()
            if new_name and new_name != txn.external.name:
                account = await _resolve_account(session, new_name)
                txn.external_id = account.id
                txn.external = account
            txn.ml_confidence_external = None

        if "category" in form:
            txn.ml_confidence_category = None
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
        return templates.TemplateResponse(
            request, "inbox/_inbox_row.html", {"txn": txn}
        )


@router.get("/transactions/{txn_id}/edit-description", response_class=HTMLResponse)
async def edit_description(txn_id: int, request: Request):
    async with async_session() as session:
        txn = await session.get(Transaction, txn_id)
    if txn is None:
        return HTMLResponse("Not found", status_code=404)
    return templates.TemplateResponse(
        request,
        "shared/_edit_input.html",
        {
            "field_name": "description",
            "value": txn.description or "",
            "input_class": "w-full bg-transparent p-0 text-sm border-0 border-b border-transparent focus:border-base-300 outline-none transition-colors",
            "endpoint": f"/transactions/{txn_id}",
            "target": f"#txn-{txn_id}",
        },
    )


@router.get(
    "/transactions/{txn_id}/edit-description-combo", response_class=HTMLResponse
)
async def edit_description_combo(txn_id: int, request: Request):
    async with async_session() as session:
        txn = await session.get(Transaction, txn_id)
    if txn is None:
        return HTMLResponse("Not found", status_code=404)
    return templates.TemplateResponse(
        request,
        "shared/_combo_edit.html",
        {
            "current_value": txn.description or "",
            "entity": "descriptions",
            "txn_id": txn_id,
            "field_name": "description",
        },
    )


@router.get("/transactions/{txn_id}/edit-external", response_class=HTMLResponse)
async def edit_external(txn_id: int, request: Request):
    async with async_session() as session:
        txn = await session.get(
            Transaction, txn_id, options=[selectinload(Transaction.external)]
        )
    if txn is None:
        return HTMLResponse("Not found", status_code=404)
    current_value = txn.external.name if txn.external else ""
    return templates.TemplateResponse(
        request,
        "shared/_combo_edit.html",
        {
            "current_value": current_value,
            "entity": "external-accounts",
            "txn_id": txn_id,
            "field_name": "external",
        },
    )


@router.get("/transactions/{txn_id}/edit-category", response_class=HTMLResponse)
async def edit_category(txn_id: int, request: Request):
    async with async_session() as session:
        txn = await session.get(
            Transaction, txn_id, options=[selectinload(Transaction.category)]
        )
    if txn is None:
        return HTMLResponse("Not found", status_code=404)
    current_value = txn.category.name if txn.category else ""
    return templates.TemplateResponse(
        request,
        "shared/_combo_edit.html",
        {
            "current_value": current_value,
            "entity": "categories",
            "txn_id": txn_id,
            "field_name": "category",
        },
    )
