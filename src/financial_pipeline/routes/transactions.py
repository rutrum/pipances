from math import ceil

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from financial_pipeline.db import async_session
from financial_pipeline.ingest import _resolve_account
from financial_pipeline.models import (
    Account,
    AccountKind,
    Category,
    Transaction,
    TransactionStatus,
)
from financial_pipeline.routes._utils import shared_context, templates
from financial_pipeline.utils import compute_date_range, safe_int

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
        row = templates.get_template("_inbox_row.html").render({"txn": txn})
        row = row.replace(
            f'<tr id="txn-{txn.id}"',
            f'<tr id="txn-{txn.id}" hx-swap-oob="outerHTML:#txn-{txn.id}"',
            1,
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
        return templates.TemplateResponse(request, "_inbox_row.html", {"txn": txn})


@router.get("/transactions/{txn_id}/edit-description", response_class=HTMLResponse)
async def edit_description(txn_id: int, request: Request):
    async with async_session() as session:
        txn = await session.get(Transaction, txn_id)
    if txn is None:
        return HTMLResponse("Not found", status_code=404)
    return templates.TemplateResponse(
        request,
        "_edit_input.html",
        {
            "field_name": "description",
            "value": txn.description or "",
            "input_class": "w-full bg-transparent p-0 text-sm border-0 border-b border-transparent focus:border-base-300 outline-none transition-colors",
            "endpoint": f"/transactions/{txn_id}",
            "target": f"#txn-{txn_id}",
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
        "_combo_edit.html",
        {
            "current_value": current_value,
            "entity": "categories",
            "txn_id": txn_id,
            "field_name": "category",
        },
    )


@router.get("/transactions", response_class=HTMLResponse)
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
    page = safe_int(params.get("page"), 1, min_val=1)
    page_size = safe_int(params.get("page_size"), 25, min_val=1, max_val=100)

    date_from, date_to = compute_date_range(preset, date_from_str, date_to_str)

    async with async_session() as session:
        query = (
            select(Transaction)
            .where(Transaction.status == TransactionStatus.APPROVED)
            .options(
                selectinload(Transaction.internal),
                selectinload(Transaction.external),
                selectinload(Transaction.category),
            )
        )
        if date_from is not None:
            query = query.where(Transaction.date >= date_from)
        if date_to is not None:
            query = query.where(Transaction.date <= date_to)

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
            .where(Transaction.status == TransactionStatus.APPROVED)
        )
        if date_from is not None:
            count_query = count_query.where(Transaction.date >= date_from)
        if date_to is not None:
            count_query = count_query.where(Transaction.date <= date_to)
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
            .where(Account.kind != AccountKind.EXTERNAL)
            .order_by(Account.name)
        )
        internal_accounts = [r[0] for r in int_result]

        ext_result = await session.execute(
            select(Account.name)
            .where(Account.kind == AccountKind.EXTERNAL)
            .order_by(Account.name)
        )
        external_accounts = [r[0] for r in ext_result]

        # Get category names for filter dropdown (only those with approved txns)
        cat_result = await session.execute(
            select(Category.name)
            .join(Transaction, Transaction.category_id == Category.id)
            .where(Transaction.status == TransactionStatus.APPROVED)
            .distinct()
            .order_by(Category.name)
        )
        category_options = [r[0] for r in cat_result]

        shared = await shared_context("transactions", session)

    ctx = {
        "request": request,
        "transactions": transactions,
        "preset": preset,
        "date_from": str(date_from) if date_from else "",
        "date_to": str(date_to) if date_to else "",
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
        table_html = templates.get_template("_txn_table_body.html").render(ctx)
        # OOB swap the date range buttons to reflect the active preset
        date_range_oob = templates.get_template("_txn_date_range.html").render(
            {"preset": preset, "date_from": ctx["date_from"], "date_to": ctx["date_to"]}
        )
        date_range_oob = date_range_oob.replace(
            'id="txn-date-range"',
            'id="txn-date-range" hx-swap-oob="outerHTML:#txn-date-range"',
            1,
        )
        return HTMLResponse(table_html + date_range_oob)

    ctx |= shared
    return templates.TemplateResponse(request, "transactions.html", ctx)
