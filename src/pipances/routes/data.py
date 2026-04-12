import importlib.util
import os
from math import ceil
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from pipances.db import async_session
from pipances.models import (
    Account,
    AccountKind,
    Category,
    Import,
    Transaction,
    TransactionStatus,
)
from pipances.routes._utils import shared_context, templates
from pipances.routes.transactions import SORT_COLUMNS
from pipances.utils import compute_date_range, safe_date, safe_int

IMPORTERS_DIR = Path(
    os.environ.get(
        "PIPANCES_IMPORTERS_DIR", str(Path(__file__).resolve().parents[3] / "importers")
    )
)

router = APIRouter()


def _data_page_ctx(section: str, shared: dict, **extra) -> dict:
    return {"data_section": section, **shared, **extra}


# === Redirect ===


@router.get("/data")
async def data_redirect():
    return RedirectResponse(url="/data/accounts")


# === Accounts ===


@router.get("/data/accounts", response_class=HTMLResponse)
async def data_accounts_page(request: Request):
    show_closed = request.query_params.get("show_closed", "false") == "true"
    async with async_session() as session:
        shared = await shared_context("data", session)
        query = (
            select(Account)
            .where(Account.kind != AccountKind.EXTERNAL)
            .order_by(Account.name)
        )
        if not show_closed:
            query = query.where(Account.active == True)  # noqa: E712
        result = await session.execute(query)
        accounts = result.scalars().all()

    is_htmx = request.headers.get("HX-Request") == "true"
    if is_htmx:
        # If triggered by the show_closed toggle, return just table rows
        if "show_closed" in request.query_params:
            rows = ""
            for account in accounts:
                rows += templates.get_template("_account_row.html").render(
                    {"account": account, "show_closed": show_closed}
                )
            rows += templates.get_template("_account_input_row.html").render()
            return HTMLResponse(rows)
        # Sidebar click: return the full accounts partial
        return HTMLResponse(
            templates.get_template("_data_accounts.html").render(
                {"accounts": accounts, "show_closed": show_closed}
            )
        )

    content_html = templates.get_template("_data_accounts.html").render(
        {"accounts": accounts, "show_closed": show_closed}
    )
    return templates.TemplateResponse(
        request,
        "data.html",
        _data_page_ctx("accounts", shared, data_content_html=content_html),
    )


@router.post("/data/accounts", response_class=HTMLResponse)
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

    if kind.lower() == AccountKind.EXTERNAL:
        return HTMLResponse(
            '<div class="alert alert-error alert-sm">Account type cannot be "external".</div>',
            status_code=422,
        )

    starting_balance_cents = 0
    if balance_str:
        starting_balance_cents = int(round(float(balance_str) * 100))

    balance_date = safe_date(balance_date_str)

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


@router.patch("/accounts/{account_id}", response_class=HTMLResponse)
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
            if new_kind.lower() == AccountKind.EXTERNAL:
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
            account.balance_date = safe_date(bd)

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


@router.get("/accounts/{account_id}/edit-name", response_class=HTMLResponse)
async def edit_account_name(account_id: int, request: Request):
    async with async_session() as session:
        account = await session.get(Account, account_id)
    if account is None:
        return HTMLResponse("Not found", status_code=404)
    return templates.TemplateResponse(
        request,
        "_edit_input.html",
        {
            "field_name": "name",
            "value": account.name,
            "endpoint": f"/accounts/{account_id}",
            "target": f"#account-{account_id}",
        },
    )


@router.get("/accounts/{account_id}/edit-type", response_class=HTMLResponse)
async def edit_account_type(account_id: int, request: Request):
    async with async_session() as session:
        account = await session.get(Account, account_id)
    if account is None:
        return HTMLResponse("Not found", status_code=404)
    return templates.TemplateResponse(
        request,
        "_edit_input.html",
        {
            "field_name": "kind",
            "value": account.kind,
            "endpoint": f"/accounts/{account_id}",
            "target": f"#account-{account_id}",
        },
    )


@router.get("/accounts/{account_id}/edit-balance", response_class=HTMLResponse)
async def edit_account_balance(account_id: int, request: Request):
    async with async_session() as session:
        account = await session.get(Account, account_id)
    if account is None:
        return HTMLResponse("Not found", status_code=404)
    return templates.TemplateResponse(
        request,
        "_edit_input.html",
        {
            "field_name": "starting_balance",
            "value": f"{account.starting_balance_cents / 100:.2f}",
            "input_type": "number",
            "step": "0.01",
            "endpoint": f"/accounts/{account_id}",
            "target": f"#account-{account_id}",
        },
    )


@router.get("/accounts/{account_id}/edit-balance-date", response_class=HTMLResponse)
async def edit_account_balance_date(account_id: int, request: Request):
    async with async_session() as session:
        account = await session.get(Account, account_id)
    if account is None:
        return HTMLResponse("Not found", status_code=404)
    value = str(account.balance_date) if account.balance_date else ""
    return templates.TemplateResponse(
        request,
        "_edit_input.html",
        {
            "field_name": "balance_date",
            "value": value,
            "input_type": "date",
            "trigger": "blur, change",
            "endpoint": f"/accounts/{account_id}",
            "target": f"#account-{account_id}",
        },
    )


# === Categories ===


@router.get("/data/categories", response_class=HTMLResponse)
async def data_categories_page(request: Request):
    async with async_session() as session:
        shared = await shared_context("data", session)
        query = (
            select(
                Category.id,
                Category.name,
                func.count(Transaction.id).label("txn_count"),
            )
            .outerjoin(Transaction, Transaction.category_id == Category.id)
            .group_by(Category.id, Category.name)
            .order_by(Category.name)
        )
        result = await session.execute(query)
        categories = result.all()

    # Convert to list of dicts for template
    categories_data = [
        {"id": cat.id, "name": cat.name, "txn_count": cat.txn_count}
        for cat in categories
    ]

    columns = [
        {
            "key": "name",
            "label": "Name",
            "type": "editable",
            "id_key": "id",
            "edit_endpoint": "/categories/{id}/edit-name",
        },
        {"key": "txn_count", "label": "Transactions"},
        {
            "key": "_explore",
            "label": "",
            "type": "link",
            "href": "/explore?category={name}",
            "icon": "compass",
            "title": "View in Explore",
        },
    ]

    ctx = {
        "title": "Categories",
        "empty_message": "No categories yet. Categories are created automatically when you assign them to transactions.",
        "columns": columns,
        "rows": categories_data,
        "tbody_id": "categories-table-body",
        "row_id_key": "id",
    }

    is_htmx = request.headers.get("HX-Request") == "true"
    if is_htmx:
        return HTMLResponse(templates.get_template("_data_table.html").render(ctx))

    content_html = templates.get_template("_data_table.html").render(ctx)
    return templates.TemplateResponse(
        request,
        "data.html",
        _data_page_ctx("categories", shared, data_content_html=content_html),
    )


@router.patch("/categories/{category_id}", response_class=HTMLResponse)
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

        txn_count = await session.scalar(
            select(func.count(Transaction.id)).where(
                Transaction.category_id == category.id
            )
        )

    return HTMLResponse(
        templates.get_template("_category_row.html").render(
            {
                "category": {
                    "id": category.id,
                    "name": category.name,
                    "txn_count": txn_count or 0,
                }
            }
        )
    )


@router.get("/categories/{category_id}/edit-name", response_class=HTMLResponse)
async def edit_category_name(category_id: int, request: Request):
    async with async_session() as session:
        category = await session.get(Category, category_id)
    if category is None:
        return HTMLResponse("Not found", status_code=404)
    return templates.TemplateResponse(
        request,
        "_edit_input.html",
        {
            "field_name": "name",
            "value": category.name,
            "endpoint": f"/categories/{category_id}",
            "target": f"#category-{category_id}",
        },
    )


# === Transactions ===


def _build_filters(
    query, date_from, date_to, internal_filter, external_filter, category_filter
):
    if date_from is not None:
        query = query.where(Transaction.date >= date_from)
    if date_to is not None:
        query = query.where(Transaction.date <= date_to)
    if internal_filter:
        query = query.join(Transaction.internal).where(Account.name == internal_filter)
    if external_filter:
        query = query.join(Transaction.external).where(Account.name == external_filter)
    if category_filter == "__uncategorized__":
        query = query.where(Transaction.category_id.is_(None))
    elif category_filter:
        query = query.join(Transaction.category).where(Category.name == category_filter)
    return query


@router.get("/data/transactions", response_class=HTMLResponse)
async def data_transactions_page(request: Request):
    params = request.query_params

    preset = params.get("preset", "all")
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
        base_where = Transaction.status.in_(
            [TransactionStatus.APPROVED, TransactionStatus.PENDING]
        )

        # Count total for pagination
        count_query = select(func.count()).select_from(Transaction).where(base_where)
        count_query = _build_filters(
            count_query,
            date_from,
            date_to,
            internal_filter,
            external_filter,
            category_filter,
        )
        total_count = await session.scalar(count_query)

        total_pages = max(1, ceil(total_count / page_size))
        page = min(page, total_pages)
        offset = (page - 1) * page_size

        # Paginated query for table
        table_query = (
            select(Transaction)
            .where(base_where)
            .options(
                selectinload(Transaction.internal),
                selectinload(Transaction.external),
                selectinload(Transaction.category),
            )
        )
        table_query = _build_filters(
            table_query,
            date_from,
            date_to,
            internal_filter,
            external_filter,
            category_filter,
        )

        col = SORT_COLUMNS.get(sort_col, Transaction.date)
        if sort_dir == "asc":
            table_query = table_query.order_by(col.asc())
        else:
            table_query = table_query.order_by(col.desc())

        result = await session.execute(table_query.offset(offset).limit(page_size))
        transactions = result.scalars().all()

        # Account lists for filter dropdowns
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

        # Category names for filter dropdown
        cat_result = await session.execute(
            select(Category.name)
            .join(Transaction, Transaction.category_id == Category.id)
            .where(base_where)
            .distinct()
            .order_by(Category.name)
        )
        category_options = [r[0] for r in cat_result]

        shared = await shared_context("data", session)

    ctx = {
        # Transaction table data
        "transactions": transactions,
        # Filters and sorting
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
        # Pagination
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "total_count": total_count,
        # Table template parameters (for _transaction_table.html)
        "endpoint": "/data/transactions",
        "target": "#data-content",
        "include_selector": "#data-txn-filters, #data-transactions-pagination-page-size",
        "filters_container_id": "data-txn-filters",
        "pagination_id": "data-transactions-pagination",
    }

    is_htmx = request.headers.get("HX-Request") == "true"
    if is_htmx:
        return HTMLResponse(
            templates.get_template("_data_transactions.html").render(ctx)
        )

    content_html = templates.get_template("_data_transactions.html").render(ctx)
    return templates.TemplateResponse(
        request,
        "data.html",
        _data_page_ctx("transactions", shared, data_content_html=content_html),
    )


# === External Accounts ===


@router.get("/data/external-accounts", response_class=HTMLResponse)
async def data_external_accounts_page(request: Request):
    async with async_session() as session:
        shared = await shared_context("data", session)
        query = (
            select(
                Account.id,
                Account.name,
                func.count(Transaction.id).label("txn_count"),
            )
            .outerjoin(Transaction, Transaction.external_id == Account.id)
            .where(Account.kind == AccountKind.EXTERNAL)
            .group_by(Account.id, Account.name)
            .order_by(Account.name)
        )
        result = await session.execute(query)
        accounts = [{"name": row.name, "txn_count": row.txn_count} for row in result]

    columns = [
        {"key": "name", "label": "Name"},
        {"key": "txn_count", "label": "Transactions"},
        {
            "key": "_explore",
            "label": "",
            "type": "link",
            "href": "/explore?external={name}",
            "icon": "compass",
            "title": "View in Explore",
        },
    ]

    ctx = {
        "title": "External Accounts",
        "empty_message": "No external accounts yet. They are created automatically when you import transactions.",
        "columns": columns,
        "rows": accounts,
    }

    is_htmx = request.headers.get("HX-Request") == "true"
    if is_htmx:
        return HTMLResponse(templates.get_template("_data_table.html").render(ctx))

    content_html = templates.get_template("_data_table.html").render(ctx)
    return templates.TemplateResponse(
        request,
        "data.html",
        _data_page_ctx("external-accounts", shared, data_content_html=content_html),
    )


# === Importers ===


def _discover_importers() -> list[dict]:
    importers = []
    if not IMPORTERS_DIR.is_dir():
        return importers
    for path in sorted(IMPORTERS_DIR.glob("*.py")):
        if path.name.startswith("__"):
            continue
        name = path.stem
        try:
            spec = importlib.util.spec_from_file_location(f"importers.{name}", path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            display_name = getattr(mod, "IMPORTER_NAME", path.name)
        except Exception:
            display_name = path.name
        importers.append({"name": display_name, "filename": path.name})
    return importers


@router.get("/data/importers", response_class=HTMLResponse)
async def data_importers_page(request: Request):
    async with async_session() as session:
        shared = await shared_context("data", session)

    importers = _discover_importers()

    columns = [
        {"key": "name", "label": "Name"},
        {"key": "filename", "label": "Filename"},
    ]

    ctx = {
        "title": "Importers",
        "empty_message": "No importers available.",
        "columns": columns,
        "rows": importers,
    }

    is_htmx = request.headers.get("HX-Request") == "true"
    if is_htmx:
        return HTMLResponse(templates.get_template("_data_table.html").render(ctx))

    content_html = templates.get_template("_data_table.html").render(ctx)
    return templates.TemplateResponse(
        request,
        "data.html",
        _data_page_ctx("importers", shared, data_content_html=content_html),
    )


# === Import History ===


@router.get("/data/imports", response_class=HTMLResponse)
async def data_imports_page(request: Request):
    async with async_session() as session:
        shared = await shared_context("data", session)
        result = await session.execute(
            select(Import).order_by(Import.imported_at.desc())
        )
        imports = result.scalars().all()

    columns = [
        {"key": "institution", "label": "Institution"},
        {
            "key": "filename",
            "label": "Filename",
            "type": "null_safe",
            "null_value": "—",
        },
        {
            "key": "imported_at",
            "label": "Imported At",
            "type": "date",
            "format": "%Y-%m-%d %H:%M",
        },
        {
            "key": "row_count",
            "label": "Rows",
            "type": "null_safe",
            "null_value": "—",
        },
    ]

    ctx = {
        "title": "Import History",
        "empty_message": "No imports yet. Upload a CSV file to get started.",
        "columns": columns,
        "rows": imports,
    }

    is_htmx = request.headers.get("HX-Request") == "true"
    if is_htmx:
        return HTMLResponse(templates.get_template("_data_table.html").render(ctx))

    content_html = templates.get_template("_data_table.html").render(ctx)
    return templates.TemplateResponse(
        request,
        "data.html",
        _data_page_ctx("imports", shared, data_content_html=content_html),
    )
