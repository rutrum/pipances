"""Import record queries. Session-first."""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from pipances.models import Import


async def get_imports(session: AsyncSession) -> Sequence[Import]:
    """All import records, most recent first."""
    result = await session.execute(select(Import).order_by(Import.imported_at.desc()))
    return result.scalars().all()
