from fastapi import APIRouter, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse

from pipances.db import DatabaseDep
from pipances.routes._utils import shared_context, static_version, templates
from pipances.utils import compute_date_range

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
    """Tabulator-based internal accounts table with inline editing."""
    async with database.session() as session:
        shared = await shared_context("data", session)

    content_html = templates.get_template(
        "data/_data_accounts_tabulator.jinja2"
    ).render()
    return templates.TemplateResponse(
        request,
        "pages/data.jinja2",
        _data_page_ctx("accounts", shared, data_content_html=content_html),
    )


# === Categories ===


@router.get("/data/categories", response_class=HTMLResponse)
async def data_categories_page(
    request: Request,
    database: DatabaseDep,
) -> Response:
    """Tabulator-based categories table with inline name editing."""
    async with database.session() as session:
        shared = await shared_context("data", session)

    content_html = templates.get_template(
        "data/_data_categories_tabulator.jinja2"
    ).render()
    return templates.TemplateResponse(
        request,
        "pages/data.jinja2",
        _data_page_ctx("categories", shared, data_content_html=content_html),
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
