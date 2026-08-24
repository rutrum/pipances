from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from pipances.db.transactions import pending_txn_count
from pipances.settings import settings

templates = Jinja2Templates(directory=str(settings.templates_dir))


async def shared_context(active_page: str, session: AsyncSession) -> dict:
    """Return shared template context: active page and inbox count."""
    count = await pending_txn_count(session)
    return {"active_page": active_page, "inbox_count": count}
