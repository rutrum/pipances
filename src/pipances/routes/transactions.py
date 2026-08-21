from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from pipances.db import async_session
from pipances.ingest import _resolve_account
from pipances.models import (
    Account,
    AccountKind,
    Category,
    Transaction,
    TransactionSplit,
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
    form = await request.form()
    ids = [int(str(i)) for i in form.getlist("ids") if str(i).strip()]
    if not ids:
        return HTMLResponse("No IDs provided", status_code=400)

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
        category_name = str(form.get("category", "")).strip()
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
        external_name = str(form.get("external", "")).strip()
        external_obj = None
        if external_name:
            external_obj = await _resolve_account(session, external_name)

        description = str(form.get("description", "")).strip()
        approve = str(form.get("marked_for_approval", "")).strip()

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
        row = templates.get_template("inbox/_inbox_row.jinja2").render(
            {"txn": txn, "oob": True}
        )
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
            txn.description = str(form["description"]) or None
            txn.ml_confidence_description = None

        if "external_id" in form:
            external_id_val = str(form["external_id"]).strip()
            if external_id_val:
                # Combo sends the display name; try integer ID first, then name lookup
                try:
                    external_id = int(external_id_val)
                    external = await session.get(Account, external_id)
                    if external:
                        txn.external_id = external_id
                        txn.external = external
                except (ValueError, TypeError):
                    ext_result = await session.execute(
                        select(Account).where(
                            func.lower(Account.name) == external_id_val.lower()
                        )
                    )
                    external = ext_result.scalar_one_or_none()
                    if external:
                        txn.external_id = external.id
                        txn.external = external
                    else:
                        # Create a new external account
                        external = Account(
                            name=external_id_val, kind=AccountKind.EXTERNAL
                        )
                        session.add(external)
                        await session.flush()
                        txn.external_id = external.id
                        txn.external = external
            else:
                txn.external_id = None
                txn.external = None
            txn.ml_confidence_external = None

        if "category_id" in form:
            category_id_val = str(form["category_id"]).strip()
            if category_id_val:
                # Combo sends the display name; try integer ID first, then name lookup
                try:
                    category_id = int(category_id_val)
                    category = await session.get(Category, category_id)
                    if category:
                        txn.category_id = category_id
                        txn.category = category
                except (ValueError, TypeError):
                    cat_result = await session.execute(
                        select(Category).where(
                            func.lower(Category.name) == category_id_val.lower()
                        )
                    )
                    category = cat_result.scalar_one_or_none()
                    if category:
                        txn.category_id = category.id
                        txn.category = category
                    else:
                        # Create a new category
                        category = Category(name=category_id_val)
                        session.add(category)
                        await session.flush()
                        txn.category_id = category.id
                        txn.category = category
            else:
                txn.category_id = None
                txn.category = None
            txn.ml_confidence_category = None

        if "marked_for_approval" in form:
            if form["marked_for_approval"] == "toggle":
                if not txn.marked_for_approval:
                    # Toggling from unapproved -> approved: validate required fields
                    if not txn.description or not txn.description.strip():
                        return HTMLResponse(
                            "Description is required for approval", status_code=422
                        )
                    if not txn.external_id:
                        return HTMLResponse(
                            "External account is required for approval", status_code=422
                        )
                txn.marked_for_approval = not txn.marked_for_approval
            elif form["marked_for_approval"] == "true":
                # Validate that description is not empty
                if not txn.description or not txn.description.strip():
                    return HTMLResponse(
                        "Description is required for approval",
                        status_code=422,
                    )
                txn.marked_for_approval = True

        await session.commit()
        await session.refresh(txn, ["internal", "external", "category"])

        if "marked_for_approval" in form:
            # Approval toggle: return just the row.
            # The modal closes itself via hx-on::after-request on the Approve/Unapprove
            # button, so no OOB update is needed.
            return templates.TemplateResponse(
                request, "inbox/_inbox_row.jinja2", {"txn": txn}
            )

        # Field update (description, external_id, category_id): return the row
        # plus an OOB fragment that refreshes the Approve button in the modal.
        # HTMX ignores the OOB swap when the target element doesn't exist in the DOM.
        row_html = templates.get_template("inbox/_inbox_row.jinja2").render(
            {"txn": txn, "oob": False}
        )
        btn_html = templates.get_template("shared/_modal_approve_btn.jinja2").render(
            {"txn": txn}
        )
        return HTMLResponse(row_html + btn_html)


@router.get("/transactions/{txn_id}/edit-modal", response_class=HTMLResponse)
async def edit_modal(txn_id: int, request: Request):
    """Load transaction edit modal with pre-filled form."""
    async with async_session() as session:
        txn = await session.get(
            Transaction,
            txn_id,
            options=[
                selectinload(Transaction.internal),
                selectinload(Transaction.external),
                selectinload(Transaction.category),
                selectinload(Transaction.splits).selectinload(
                    TransactionSplit.category
                ),
            ],
        )
        if txn is None:
            return HTMLResponse("Not found", status_code=404)

        # Load all external accounts for dropdown
        external_result = await session.execute(
            select(Account)
            .where(Account.kind == AccountKind.EXTERNAL)
            .order_by(Account.name)
        )
        external_accounts = external_result.scalars().all()

        # Load all categories for dropdown
        categories_result = await session.execute(
            select(Category).order_by(Category.name)
        )
        categories = categories_result.scalars().all()
        categories_data = [{"id": c.id, "name": c.name} for c in categories]

        return templates.TemplateResponse(
            request,
            "shared/_transaction_edit_modal.jinja2",
            {
                "txn": txn,
                "external_accounts": external_accounts,
                "categories": categories,
                "categories_data": categories_data,
            },
        )


async def _render_splits_section(request: Request, txn: Transaction) -> str:
    """Render the splits section partial for the given transaction."""
    async with async_session() as session:
        categories_result = await session.execute(
            select(Category).order_by(Category.name)
        )
        categories = categories_result.scalars().all()
        # Re-attach txn to load its category relationship
        fetched = await session.get(
            Transaction,
            txn.id,
            options=[
                selectinload(Transaction.splits).selectinload(
                    TransactionSplit.category
                ),
                selectinload(Transaction.category),
            ],
        )
        if fetched is None:
            raise RuntimeError(f"Transaction {txn.id} not found")
        txn = fetched
    categories_data = [{"id": c.id, "name": c.name} for c in categories]
    return templates.get_template("shared/_splits_section.jinja2").render(
        {"txn": txn, "categories": categories, "categories_data": categories_data}
    )


@router.post("/transactions/{txn_id}/splits", response_class=HTMLResponse)
async def create_split(txn_id: int, request: Request):
    form = await request.form()
    async with async_session() as session:
        txn = await session.get(
            Transaction,
            txn_id,
            options=[
                selectinload(Transaction.splits).selectinload(
                    TransactionSplit.category
                ),
            ],
        )
        if txn is None:
            return HTMLResponse("Not found", status_code=404)

        try:
            amount_dollars = float(str(form.get("amount_dollars", "0")))
        except (ValueError, TypeError):
            return HTMLResponse("Invalid amount", status_code=422)
        amount_cents = round(amount_dollars * 100)

        if amount_cents <= 0:
            return HTMLResponse("Amount must be positive", status_code=422)

        total_cents = abs(txn.amount_cents)
        existing_sum = sum(s.amount_cents for s in txn.splits)
        if amount_cents >= total_cents - existing_sum:
            return HTMLResponse("Amount would eliminate remainder", status_code=422)

        category_id_val = str(form.get("category_id", "")).strip()
        category_id = None
        if category_id_val:
            try:
                category_id = int(category_id_val)
            except (ValueError, TypeError):
                cat_result = await session.execute(
                    select(Category).where(
                        func.lower(Category.name) == category_id_val.lower()
                    )
                )
                cat = cat_result.scalar_one_or_none()
                if cat:
                    category_id = cat.id
                else:
                    cat = Category(name=category_id_val)
                    session.add(cat)
                    await session.flush()
                    category_id = cat.id

        split = TransactionSplit(
            transaction_id=txn_id,
            category_id=category_id,
            amount_cents=amount_cents,
        )
        session.add(split)
        await session.commit()
        await session.refresh(txn, ["splits"])

    html = await _render_splits_section(request, txn)
    return HTMLResponse(html)


@router.patch("/transactions/{txn_id}/splits/{split_id}", response_class=HTMLResponse)
async def update_split(txn_id: int, split_id: int, request: Request):
    form = await request.form()
    async with async_session() as session:
        split = await session.get(TransactionSplit, split_id)
        if split is None or split.transaction_id != txn_id:
            return HTMLResponse("Not found", status_code=404)

        txn = await session.get(
            Transaction,
            txn_id,
            options=[
                selectinload(Transaction.splits).selectinload(
                    TransactionSplit.category
                ),
            ],
        )
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

            other_sum = sum(s.amount_cents for s in txn.splits if s.id != split_id)
            total_cents = abs(txn.amount_cents)
            if amount_cents >= total_cents - other_sum:
                return HTMLResponse("Amount would eliminate remainder", status_code=422)
            split.amount_cents = amount_cents

        if "category_id" in form:
            category_id_val = str(form["category_id"]).strip()
            if category_id_val:
                try:
                    split.category_id = int(category_id_val)
                except (ValueError, TypeError):
                    cat_result = await session.execute(
                        select(Category).where(
                            func.lower(Category.name) == category_id_val.lower()
                        )
                    )
                    cat = cat_result.scalar_one_or_none()
                    if cat:
                        split.category_id = cat.id
                    else:
                        cat = Category(name=category_id_val)
                        session.add(cat)
                        await session.flush()
                        split.category_id = cat.id
            else:
                split.category_id = None

        await session.commit()
        await session.refresh(txn, ["splits"])

    html = await _render_splits_section(request, txn)
    return HTMLResponse(html)


@router.delete("/transactions/{txn_id}/splits/{split_id}", response_class=HTMLResponse)
async def delete_split(txn_id: int, split_id: int, request: Request):
    async with async_session() as session:
        split = await session.get(TransactionSplit, split_id)
        if split is None or split.transaction_id != txn_id:
            return HTMLResponse("Not found", status_code=404)

        txn = await session.get(
            Transaction,
            txn_id,
            options=[
                selectinload(Transaction.splits).selectinload(
                    TransactionSplit.category
                ),
            ],
        )
        if txn is None:
            return HTMLResponse("Not found", status_code=404)

        await session.delete(split)
        await session.commit()
        await session.refresh(txn, ["splits"])

    html = await _render_splits_section(request, txn)
    return HTMLResponse(html)


@router.get("/transactions/{txn_id}/row", response_class=HTMLResponse)
async def transaction_row(txn_id: int, request: Request):
    """Get a single transaction row for refreshing after modal close."""
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

        return templates.TemplateResponse(
            request,
            "inbox/_inbox_row.jinja2",
            {"txn": txn, "oob": False},
        )
