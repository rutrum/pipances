"""JSON API for import history."""

from fastapi import APIRouter

from pipances.db import DatabaseDep
from pipances.db.imports import fetch_imports_page, get_imports
from pipances.routes.api.queries import tabulator_envelope
from pipances.routes.api.schemas import (
    ImportItem,
    TabulatorRequest,
    TabulatorTableResponse,
)

router = APIRouter(prefix="/api", tags=["imports"])


@router.get(
    "/imports",
    response_model=list[ImportItem],
    summary="List import history",
    description="Return all imports ordered by date (newest first).",
)
async def list_imports(database: DatabaseDep):
    async with database.session() as session:
        return [
            {
                "id": imp.id,
                "institution": imp.institution,
                "filename": imp.filename,
                "imported_at": str(imp.imported_at),
                "row_count": imp.row_count,
            }
            for imp in await get_imports(session)
        ]


@router.post(
    "/imports/table",
    response_model=TabulatorTableResponse,
    summary="Import history for Tabulator (remote mode)",
    description=(
        "Tabulator-native endpoint: accepts Tabulator's page/size/sort/filter"
        " body and returns Tabulator's default remote envelope."
        " Used by /data/imports."
    ),
)
async def imports_table(
    payload: TabulatorRequest,
    database: DatabaseDep,
):
    async with database.session() as session:
        page = await fetch_imports_page(
            session,
            sorters=[s.model_dump() for s in payload.sort],
            filters=[f.model_dump() for f in payload.filter],
            page=max(payload.page, 1),
            page_size=min(max(payload.size, 1), 100),
        )
    return tabulator_envelope(
        [
            {
                "id": imp.id,
                "institution": imp.institution,
                "filename": imp.filename,
                "imported_at": imp.imported_at.strftime("%Y-%m-%d %H:%M"),
                "row_count": imp.row_count,
            }
            for imp in page.rows
        ],
        page.total_count,
        page.total_pages,
    )
