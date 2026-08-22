from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select

from pipances.models import Transaction, TransactionStatus
from pipances.settings import settings

templates = Jinja2Templates(directory=str(settings.templates_dir))


async def shared_context(active_page: str, session) -> dict:
    """Return shared template context: active page and inbox count."""
    count = await session.scalar(
        select(func.count())
        .select_from(Transaction)
        .where(Transaction.status == TransactionStatus.PENDING)
    )
    return {"active_page": active_page, "inbox_count": count}
