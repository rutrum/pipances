from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from pipances.db.transactions import pending_txn_count
from pipances.settings import settings


def static_version(*parts: str) -> str:
    """Cache-busting token for a first-party static asset (its file mtime)."""
    try:
        return str(int(settings.static_dir.joinpath(*parts).stat().st_mtime))
    except OSError:
        return "0"


templates = Jinja2Templates(directory=str(settings.templates_dir))
templates.env.globals["static_version"] = static_version  # ty: ignore[invalid-assignment]


async def shared_context(active_page: str, session: AsyncSession) -> dict:
    """Return shared template context: active page and inbox count."""
    count = await pending_txn_count(session)
    return {"active_page": active_page, "inbox_count": count}
