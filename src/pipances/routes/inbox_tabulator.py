"""Tabulator-based inbox page.

A second inbox implementation that lives alongside the original HTMX inbox.
It is self-contained by design: it will eventually replace the original, so it
does not share row/modal templates with it.
"""

from fastapi import APIRouter, Request, Response
from fastapi.responses import HTMLResponse

from pipances.db import DatabaseDep
from pipances.db.accounts import get_external_accounts
from pipances.db.categories import get_categories
from pipances.db.transactions import distinct_descriptions, get_txn, marked_txn_count
from pipances.routes._utils import shared_context, static_version, templates
from pipances.settings import settings

router = APIRouter()


@router.get("/inbox-tabulator", response_class=HTMLResponse)
async def inbox_tabulator_page(
    request: Request,
    database: DatabaseDep,
) -> Response:
    async with database.session() as session:
        shared = await shared_context("inbox_tabulator", session)
        marked_count = await marked_txn_count(session)

    ctx = {
        "page_size": settings.inbox_default_page_size,
        "page_size_options": settings.inbox_page_size_options,
        "marked_count": marked_count,
        "js_version": static_version("js", "pages", "inbox-tabulator.js"),
        "modal_js_version": static_version("js", "pages", "inbox-tabulator-modal.js"),
        **shared,
    }
    return templates.TemplateResponse(request, "pages/inbox_tabulator.jinja2", ctx)


@router.get(
    "/inbox-tabulator/transactions/{txn_id}/edit-modal",
    response_class=HTMLResponse,
)
async def inbox_tabulator_edit_modal(
    txn_id: int,
    request: Request,
    database: DatabaseDep,
) -> Response:
    """Load the Tabulator inbox edit modal (scalars + splits) for one row."""
    async with database.session() as session:
        txn = await get_txn(session, txn_id, splits=True)
        if txn is None:
            return HTMLResponse("Not found", status_code=404)

        external_accounts = await get_external_accounts(session)
        categories = await get_categories(session)
        categories_data = [{"id": c.id, "name": c.name} for c in categories]
        descriptions = await distinct_descriptions(session)

    return templates.TemplateResponse(
        request,
        "inbox/_inbox_tabulator_modal.jinja2",
        {
            "txn": txn,
            "external_accounts": external_accounts,
            "categories": categories,
            "categories_data": categories_data,
            "descriptions": descriptions,
        },
    )
