"""JSON API for import history."""

from fastapi import APIRouter

from pipances.routes.api.queries import get_imports
from pipances.routes.api.schemas import ImportItem

router = APIRouter(prefix="/api", tags=["imports"])


@router.get(
    "/imports",
    response_model=list[ImportItem],
    summary="List import history",
    description="Return all imports ordered by date (newest first).",
)
async def list_imports():
    return await get_imports()
