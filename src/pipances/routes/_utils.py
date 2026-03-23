from pathlib import Path

from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select

from pipances.models import Transaction, TransactionStatus

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=TEMPLATES_DIR)


async def shared_context(active_page: str, session) -> dict:
    """Return shared template context: active page and inbox count."""
    count = await session.scalar(
        select(func.count())
        .select_from(Transaction)
        .where(Transaction.status == TransactionStatus.PENDING)
    )
    return {"active_page": active_page, "inbox_count": count}
