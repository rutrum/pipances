"""Import record queries. Session-first."""

from __future__ import annotations

from collections.abc import Sequence
from math import ceil
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from pipances.db import TablePage
from pipances.models import Import
from pipances.utils import escape_like


async def get_imports(session: AsyncSession) -> Sequence[Import]:
    """All import records, most recent first."""
    result = await session.execute(select(Import).order_by(Import.imported_at.desc()))
    return result.scalars().all()


_IMPORT_SORTS: dict[str, Any] = {
    "institution": Import.institution,
    "filename": Import.filename,
    "imported_at": Import.imported_at,
    "row_count": Import.row_count,
}

_IMPORT_TEXT_FILTERS = ("institution", "filename")


async def fetch_imports_page(
    session: AsyncSession,
    *,
    sorters: Sequence[dict[str, Any]] | None = None,
    filters: Sequence[dict[str, Any]] | None = None,
    page: int = 1,
    page_size: int = 25,
) -> TablePage:
    """One page of import history, newest first by default."""
    query: Select[Any] = select(Import)

    for spec in filters or ():
        field = str(spec.get("field", ""))
        value = spec.get("value")
        if field not in _IMPORT_TEXT_FILTERS or value in (None, ""):
            continue
        query = query.where(
            getattr(Import, field).ilike(f"%{escape_like(str(value))}%")
        )

    total_count = int(
        await session.scalar(select(func.count()).select_from(query.subquery())) or 0
    )
    total_pages = max(1, ceil(total_count / page_size))
    page = min(page, total_pages)
    offset = (page - 1) * page_size

    order_by = []
    for sorter in sorters or ():
        col = _IMPORT_SORTS.get(str(sorter.get("field", "")))
        if col is None:
            continue
        order_by.append(
            col.asc() if str(sorter.get("dir", "asc")).lower() == "asc" else col.desc()
        )
    if not order_by:
        order_by.append(Import.imported_at.desc())

    result = await session.execute(
        query.order_by(*order_by).offset(offset).limit(page_size)
    )
    return TablePage(result.scalars().all(), total_count, page, page_size, total_pages)
