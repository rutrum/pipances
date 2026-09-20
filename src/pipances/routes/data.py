from fastapi import APIRouter, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from pipances.db import DatabaseDep
from pipances.db.categories import (
    categories_with_usage,
    transaction_count_for_category,
)
from pipances.models import (
    Account,
    AccountKind,
    Category,
)
from pipances.routes._utils import shared_context, static_version, templates
from pipances.utils import compute_date_range, safe_date

router = APIRouter()


def _data_page_ctx(section: str, shared: dict, **extra) -> dict:
    return {"data_section": section, **shared, **extra}


# === Redirect ===


@router.get("/data")
async def data_redirect() -> RedirectResponse:
    return RedirectResponse(url="/data/accounts")


# === Accounts ===


@router.get("/data/accounts", response_class=HTMLResponse)
async def data_accounts_page(
    request: Request,
    database: DatabaseDep,
) -> Response:
    show_closed = request.query_params.get("show_closed", "false") == "true"
    async with database.session() as session:
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
                rows += templates.get_template("data/_account_row.jinja2").render(
                    {"account": account, "show_closed": show_closed}
                )
            rows += templates.get_template("data/_account_input_row.jinja2").render()
            return HTMLResponse(rows)
        # Sidebar click: return the full accounts partial
        return HTMLResponse(
            templates.get_template("data/_data_accounts.jinja2").render(
                {"accounts": accounts, "show_closed": show_closed}
            )
        )

    content_html = templates.get_template("data/_data_accounts.jinja2").render(
        {"accounts": accounts, "show_closed": show_closed}
    )

    return templates.TemplateResponse(
        request,
        "pages/data.jinja2",
        _data_page_ctx("accounts", shared, data_content_html=content_html),
    )


@router.post("/data/accounts", response_class=HTMLResponse)
async def create_account(
    request: Request,
    database: DatabaseDep,
) -> HTMLResponse:
    form = await request.form()
    name = str(form.get("name", "")).strip()
    kind = str(form.get("kind", "")).strip()
    balance_str = str(form.get("starting_balance", "")).strip()
    balance_date_str = str(form.get("balance_date", "")).strip()

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

    async with database.session() as session:
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
        templates.get_template("data/_account_row.jinja2").render({"account": account})
    )


@router.patch("/accounts/{account_id}", response_class=HTMLResponse)
async def update_account(
    account_id: int,
    request: Request,
    database: DatabaseDep,
) -> HTMLResponse:
    form = await request.form()
    async with database.session() as session:
        account = await session.get(Account, account_id)
        if account is None:
            return HTMLResponse("Not found", status_code=404)

        if "name" in form:
            new_name = str(form["name"]).strip()
            if new_name:
                account.name = new_name

        if "kind" in form:
            new_kind = str(form["kind"]).strip()
            if new_kind.lower() == AccountKind.EXTERNAL:
                return HTMLResponse(
                    '<div class="alert alert-error alert-sm">Account type cannot be "external".</div>',
                    status_code=422,
                )
            if new_kind:
                account.kind = new_kind

        if "starting_balance" in form:
            bal = str(form["starting_balance"]).strip()
            if bal:
                account.starting_balance_cents = int(round(float(bal) * 100))
            else:
                account.starting_balance_cents = 0

        if "balance_date" in form:
            bd = str(form["balance_date"]).strip()
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
        templates.get_template("data/_account_row.jinja2").render(
            {"account": account, "show_closed": show_closed}
        )
    )


@router.get("/accounts/{account_id}/edit-name", response_class=HTMLResponse)
async def edit_account_name(
    account_id: int,
    request: Request,
    database: DatabaseDep,
) -> Response:
    async with database.session() as session:
        account = await session.get(Account, account_id)
    if account is None:
        return HTMLResponse("Not found", status_code=404)
    return templates.TemplateResponse(
        request,
        "shared/_edit_input.jinja2",
        {
            "field_name": "name",
            "value": account.name,
            "endpoint": f"/accounts/{account_id}",
            "target": f"#account-{account_id}",
        },
    )


@router.get("/accounts/{account_id}/edit-type", response_class=HTMLResponse)
async def edit_account_type(
    account_id: int,
    request: Request,
    database: DatabaseDep,
) -> Response:
    async with database.session() as session:
        account = await session.get(Account, account_id)
    if account is None:
        return HTMLResponse("Not found", status_code=404)
    return templates.TemplateResponse(
        request,
        "shared/_edit_input.jinja2",
        {
            "field_name": "kind",
            "value": account.kind,
            "endpoint": f"/accounts/{account_id}",
            "target": f"#account-{account_id}",
        },
    )


@router.get("/accounts/{account_id}/edit-balance", response_class=HTMLResponse)
async def edit_account_balance(
    account_id: int,
    request: Request,
    database: DatabaseDep,
) -> Response:
    async with database.session() as session:
        account = await session.get(Account, account_id)
    if account is None:
        return HTMLResponse("Not found", status_code=404)
    return templates.TemplateResponse(
        request,
        "shared/_edit_input.jinja2",
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
async def edit_account_balance_date(
    account_id: int,
    request: Request,
    database: DatabaseDep,
) -> Response:
    async with database.session() as session:
        account = await session.get(Account, account_id)
    if account is None:
        return HTMLResponse("Not found", status_code=404)
    value = str(account.balance_date) if account.balance_date else ""
    return templates.TemplateResponse(
        request,
        "shared/_edit_input.jinja2",
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
async def data_categories_page(
    request: Request,
    database: DatabaseDep,
) -> Response:
    async with database.session() as session:
        shared = await shared_context("data", session)
        categories = await categories_with_usage(session)

    categories_data = [
        {"id": c.id, "name": c.name, "txn_count": c.txn_count} for c in categories
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
        return HTMLResponse(
            templates.get_template("data/_data_table.jinja2").render(ctx)
        )

    content_html = templates.get_template("data/_data_table.jinja2").render(ctx)
    return templates.TemplateResponse(
        request,
        "pages/data.jinja2",
        _data_page_ctx("categories", shared, data_content_html=content_html),
    )


@router.patch("/categories/{category_id}", response_class=HTMLResponse)
async def update_category(
    category_id: int,
    request: Request,
    database: DatabaseDep,
) -> HTMLResponse:
    form = await request.form()
    async with database.session() as session:
        category = await session.get(Category, category_id)
        if category is None:
            return HTMLResponse("Not found", status_code=404)

        if "name" in form:
            new_name = str(form["name"]).strip()
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

        txn_count = await transaction_count_for_category(session, category.id)

    return HTMLResponse(
        templates.get_template("data/_category_row.jinja2").render(
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
async def edit_category_name(
    category_id: int,
    request: Request,
    database: DatabaseDep,
) -> Response:
    async with database.session() as session:
        category = await session.get(Category, category_id)
    if category is None:
        return HTMLResponse("Not found", status_code=404)
    return templates.TemplateResponse(
        request,
        "shared/_edit_input.jinja2",
        {
            "field_name": "name",
            "value": category.name,
            "endpoint": f"/categories/{category_id}",
            "target": f"#category-{category_id}",
        },
    )


# === Transactions ===


@router.get("/data/transactions", response_class=HTMLResponse)
async def data_transactions_page(
    request: Request,
    database: DatabaseDep,
) -> Response:
    """Tabulator-based transactions table (read-only, remote mode)."""
    params = request.query_params
    preset = params.get("preset", "all")
    date_from, date_to = compute_date_range(
        preset, params.get("date_from"), params.get("date_to")
    )

    preset_ranges = []
    for key, label in (
        ("all", "All"),
        ("ytd", "YTD"),
        ("last_month", "Last 30 Days"),
        ("last_3_months", "Last 90 Days"),
        ("last_year", "Last 365 Days"),
    ):
        df, dt = compute_date_range(key, None, None)
        preset_ranges.append(
            {
                "key": key,
                "label": label,
                "date_from": str(df) if df else "",
                "date_to": str(dt) if dt else "",
            }
        )

    async with database.session() as session:
        shared = await shared_context("data", session)

    ctx = {
        "preset": preset,
        "date_from": str(date_from) if date_from else "",
        "date_to": str(date_to) if date_to else "",
        "preset_ranges": preset_ranges,
        "js_version": static_version("js", "pages", "transactions-table.js"),
    }

    content_html = templates.get_template("data/_data_transactions.jinja2").render(ctx)
    return templates.TemplateResponse(
        request,
        "pages/data.jinja2",
        _data_page_ctx("transactions", shared, data_content_html=content_html),
    )


@router.get("/data/tab_transactions")
async def data_tab_transactions_redirect() -> RedirectResponse:
    """Legacy path for the experimental Tabulator page, kept as a redirect."""
    return RedirectResponse(url="/data/transactions")


# === External Accounts ===


@router.get("/data/external-accounts", response_class=HTMLResponse)
async def data_external_accounts_page(
    request: Request,
    database: DatabaseDep,
) -> Response:
    """Tabulator-based external accounts table (read-only, remote mode)."""
    async with database.session() as session:
        shared = await shared_context("data", session)

    ctx = {"js_version": static_version("js", "pages", "external-accounts-table.js")}
    content_html = templates.get_template("data/_data_external_accounts.jinja2").render(
        ctx
    )
    return templates.TemplateResponse(
        request,
        "pages/data.jinja2",
        _data_page_ctx("external-accounts", shared, data_content_html=content_html),
    )


# === Importers ===


@router.get("/data/importers", response_class=HTMLResponse)
async def data_importers_page(
    request: Request,
    database: DatabaseDep,
) -> Response:
    """Tabulator-based importers table (filesystem-backed, client mode)."""
    async with database.session() as session:
        shared = await shared_context("data", session)

    ctx = {"js_version": static_version("js", "pages", "importers-table.js")}
    content_html = templates.get_template("data/_data_importers.jinja2").render(ctx)
    return templates.TemplateResponse(
        request,
        "pages/data.jinja2",
        _data_page_ctx("importers", shared, data_content_html=content_html),
    )


# === Import History ===


@router.get("/data/imports", response_class=HTMLResponse)
async def data_imports_page(
    request: Request,
    database: DatabaseDep,
) -> Response:
    """Tabulator-based import history table (read-only, remote mode)."""
    async with database.session() as session:
        shared = await shared_context("data", session)

    ctx = {"js_version": static_version("js", "pages", "imports-table.js")}
    content_html = templates.get_template("data/_data_imports.jinja2").render(ctx)
    return templates.TemplateResponse(
        request,
        "pages/data.jinja2",
        _data_page_ctx("imports", shared, data_content_html=content_html),
    )
