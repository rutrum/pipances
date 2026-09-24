"""Inbox page (Tabulator-based).

Replaces the old HTMX inbox and the temporary /inbox-tabulator path.
The upload toast is ported from the original inbox page.
"""

from fastapi import APIRouter, Request, Response
from fastapi.responses import HTMLResponse

from pipances.db import DatabaseDep
from pipances.db.transactions import get_txn, marked_txn_count
from pipances.routes._utils import shared_context, static_version, templates
from pipances.settings import settings

router = APIRouter()


@router.get("/inbox", response_class=HTMLResponse)
async def inbox_page(
    request: Request,
    database: DatabaseDep,
) -> Response:
    params = request.query_params

    async with database.session() as session:
        shared = await shared_context("inbox", session)
        marked_count = await marked_txn_count(session)

    toast = params.get("toast")
    ctx = {
        "page_size": settings.inbox_default_page_size,
        "page_size_options": settings.inbox_page_size_options,
        "marked_count": marked_count,
        "js_version": static_version("js", "pages", "inbox.js"),
        "modal_js_version": static_version("js", "pages", "inbox-modal.js"),
        "toast": toast,
        "import_summary": {
            "imported": params.get("imported"),
            "duplicates": params.get("duplicates"),
            "date_min": params.get("date_min"),
            "date_max": params.get("date_max"),
            "account": params.get("account"),
        }
        if toast == "upload_success"
        else None,
        **shared,
    }
    return templates.TemplateResponse(request, "pages/inbox.jinja2", ctx)


@router.get(
    "/inbox/transactions/{txn_id}/edit-modal",
    response_class=HTMLResponse,
)
async def inbox_edit_modal(
    txn_id: int,
    request: Request,
    database: DatabaseDep,
) -> Response:
    """Load the Tabulator inbox edit modal (scalars + splits) for one row."""
    from pipances.db.accounts import get_external_accounts
    from pipances.db.categories import get_categories
    from pipances.db.transactions import distinct_descriptions

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
        "inbox/_inbox_modal.jinja2",
        {
            "txn": txn,
            "external_accounts": external_accounts,
            "categories": categories,
            "categories_data": categories_data,
            "descriptions": descriptions,
        },
    )
