"""Tabulator-based inbox page.

A second inbox implementation that lives alongside the original HTMX inbox.
It is self-contained by design: it will eventually replace the original, so it
does not share row/modal templates with it.
"""

from fastapi import APIRouter, Request, Response
from fastapi.responses import HTMLResponse

from pipances.db import DatabaseDep
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

    ctx = {
        "page_size": settings.inbox_default_page_size,
        "page_size_options": settings.inbox_page_size_options,
        "js_version": static_version("js", "pages", "inbox-tabulator.js"),
        **shared,
    }
    return templates.TemplateResponse(request, "pages/inbox_tabulator.jinja2", ctx)
