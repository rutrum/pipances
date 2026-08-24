from fastapi import APIRouter, Request, Response
from fastapi.responses import HTMLResponse
from sqlalchemy import select

from pipances.db import Database, DatabaseDep
from pipances.db.accounts import (
    get_external_accounts,
    get_or_create_external_account,
)
from pipances.db.categories import get_categories, get_or_create_category
from pipances.db.transactions import (
    get_txn,
    remaining_split_capacity,
    set_txn_category,
    set_txn_description,
    set_txn_external,
    txn_options,
)
from pipances.models import (
    Account,
    Category,
    Transaction,
    TransactionSplit,
)
from pipances.routes._utils import templates

router = APIRouter()


@router.patch("/transactions/bulk", response_class=HTMLResponse)
async def bulk_update_transactions(
    request: Request,
    database: DatabaseDep,
) -> HTMLResponse:
    form = await request.form()
    ids = [int(str(i)) for i in form.getlist("ids") if str(i).strip()]
    if not ids:
        return HTMLResponse("No IDs provided", status_code=400)

    async with database.session() as session:
        result = await session.execute(
            select(Transaction).where(Transaction.id.in_(ids)).options(*txn_options())
        )
        transactions = result.scalars().all()

        # Resolve category once if provided
        category_name = str(form.get("category", "")).strip()
        category_obj = (
            await get_or_create_category(session, category_name)
            if category_name
            else None
        )

        # Resolve external account once if provided
        external_name = str(form.get("external", "")).strip()
        external_obj = (
            await get_or_create_external_account(session, external_name)
            if external_name
            else None
        )

        description = str(form.get("description", "")).strip()
        approve = str(form.get("marked_for_approval", "")).strip()

        for txn in transactions:
            if description:
                set_txn_description(txn, description)
            if category_obj:
                set_txn_category(txn, category_obj)
            if external_obj:
                set_txn_external(txn, external_obj)
            if approve == "true" and txn.description:
                txn.marked_for_approval = True

        await session.commit()

        # Re-fetch to get fresh relationships
        result = await session.execute(
            select(Transaction).where(Transaction.id.in_(ids)).options(*txn_options())
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
async def update_transaction(
    txn_id: int,
    request: Request,
    database: DatabaseDep,
) -> Response:
    form = await request.form()
    async with database.session() as session:
        txn = await get_txn(session, txn_id)
        if txn is None:
            return HTMLResponse("Not found", status_code=404)

        if "description" in form:
            set_txn_description(txn, str(form["description"]) or None)

        if "external_id" in form:
            external_id_val = str(form["external_id"]).strip()
            external: Account | None = None
            if external_id_val:
                # Combo sends the display name; try integer ID first, then name lookup
                try:
                    external = await session.get(Account, int(external_id_val))
                except (ValueError, TypeError):
                    external = await get_or_create_external_account(
                        session, external_id_val
                    )
            set_txn_external(txn, external)

        if "category_id" in form:
            category_id_val = str(form["category_id"]).strip()
            category: Category | None = None
            if category_id_val:
                # Combo sends the display name; try integer ID first, then name lookup
                try:
                    category = await session.get(Category, int(category_id_val))
                except (ValueError, TypeError):
                    category = await get_or_create_category(session, category_id_val)
            set_txn_category(txn, category)

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
async def edit_modal(
    txn_id: int,
    request: Request,
    database: DatabaseDep,
) -> Response:
    """Load transaction edit modal with pre-filled form."""
    async with database.session() as session:
        txn = await get_txn(session, txn_id, splits=True)
        if txn is None:
            return HTMLResponse("Not found", status_code=404)

        # Load all external accounts for dropdown
        external_accounts = await get_external_accounts(session)

        # Load all categories for dropdown
        categories = await get_categories(session)
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


@router.get("/transactions/{txn_id}/row", response_class=HTMLResponse)
async def transaction_row(
    txn_id: int,
    request: Request,
    database: DatabaseDep,
) -> Response:
    """Get a single transaction row for refreshing after modal close."""
    async with database.session() as session:
        txn = await get_txn(session, txn_id)
        if txn is None:
            return HTMLResponse("Not found", status_code=404)

        return templates.TemplateResponse(
            request,
            "inbox/_inbox_row.jinja2",
            {"txn": txn, "oob": False},
        )
