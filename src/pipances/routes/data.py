from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse

from pipances.db import DatabaseDep
from pipances.db.importers import get_importer as db_get_importer
from pipances.db.importers import list_importers as db_list_importers
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
    """SQL importer list (client mode over embedded JSON). No builder markup."""
    async with database.session() as session:
        shared = await shared_context("data", session)
        importers = await db_list_importers(session)

    ctx = {
        "js_version": static_version("js", "pages", "importers.js"),
        "importers": [
            {
                "id": importer.id,
                "name": importer.name,
                "sql": importer.sql,
                "created_at": importer.created_at.isoformat(),
                "updated_at": importer.updated_at.isoformat(),
            }
            for importer in importers
        ],
    }
    content_html = templates.get_template("data/_data_importers.jinja2").render(ctx)
    return templates.TemplateResponse(
        request,
        "pages/data.jinja2",
        _data_page_ctx(
            "importers",
            shared,
            data_content_html=content_html,
            toast=request.query_params.get("toast"),
        ),
    )


def _render_importer_builder(
    request: Request, shared: dict, importer: dict | None
) -> Response:
    """Render the builder page content inside the Data layout."""
    ctx = {
        "js_version": static_version("js", "pages", "importer-builder.js"),
        "importer": importer,
    }
    content_html = templates.get_template("data/_importer_builder.jinja2").render(ctx)
    return templates.TemplateResponse(
        request,
        "pages/data.jinja2",
        _data_page_ctx("importers", shared, data_content_html=content_html),
    )


@router.get("/data/importers/new", response_class=HTMLResponse)
async def data_importer_new_page(
    request: Request,
    database: DatabaseDep,
) -> Response:
    """SQL importer builder in create mode."""
    async with database.session() as session:
        shared = await shared_context("data", session)

    return _render_importer_builder(request, shared, None)


@router.get("/data/importers/{importer_id}/edit", response_class=HTMLResponse)
async def data_importer_edit_page(
    request: Request,
    importer_id: int,
    database: DatabaseDep,
) -> Response:
    """SQL importer builder in edit mode; 404 when the importer is missing."""
    async with database.session() as session:
        shared = await shared_context("data", session)
        importer = await db_get_importer(session, importer_id)

    if importer is None:
        raise HTTPException(status_code=404, detail="Importer not found")

    return _render_importer_builder(
        request,
        shared,
        {"id": importer.id, "name": importer.name, "sql": importer.sql},
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
