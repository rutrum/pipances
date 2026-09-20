"""JSON API for importer discovery."""

from fastapi import APIRouter

from pipances.ingest import discover_importers
from pipances.routes.api.schemas import ImporterItem

router = APIRouter(prefix="/api", tags=["importers"])


@router.get(
    "/importers",
    response_model=list[ImporterItem],
    summary="List available importers",
    description=(
        "Return discovered importer modules (display name + filename)."
        " Used by /data/importers."
    ),
)
async def list_importers() -> list[ImporterItem]:
    return [
        ImporterItem(name=info.name, filename=f"{info.module_name}.py")
        for info in discover_importers().values()
    ]
