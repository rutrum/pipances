"""JSON API for import history."""

from fastapi import APIRouter

from pipances.db import DatabaseDep
from pipances.db.imports import get_imports
from pipances.routes.api.schemas import ImportItem

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
