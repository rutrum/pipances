"""Category queries and resolution helpers. Session-first."""

from __future__ import annotations

from collections.abc import Sequence
from math import ceil
from typing import Any, NamedTuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from pipances.db import TablePage
from pipances.db.transactions import VISIBLE_STATUSES, statuses_where
from pipances.models import Category, Transaction, TransactionStatus
from pipances.utils import escape_like


async def get_categories(session: AsyncSession) -> Sequence[Category]:
    """All categories ordered by name."""
    result = await session.execute(select(Category).order_by(Category.name))
    return result.scalars().all()


async def get_or_create_category(session: AsyncSession, name: str) -> Category:
    """Resolve a category by case-insensitive name, creating one if missing."""
    result = await session.execute(
        select(Category).where(func.lower(Category.name) == name.lower())
    )
    category = result.scalar_one_or_none()
    if category is None:
        category = Category(name=name)
        session.add(category)
        await session.flush()
    return category


async def category_names_with_transactions(
    session: AsyncSession,
    statuses: Sequence[TransactionStatus] = VISIBLE_STATUSES,
) -> Sequence[str]:
    """Names of categories referenced by at least one transaction with a given status."""
    result = await session.execute(
        select(Category.name)
        .join(Transaction, Transaction.category_id == Category.id)
        .where(statuses_where(statuses))
        .distinct()
        .order_by(Category.name)
    )
    return [row[0] for row in result]


class CategoryUsage(NamedTuple):
    """A category with the number of transactions referencing it."""

    id: int
    name: str
    txn_count: int


async def categories_with_usage(session: AsyncSession) -> Sequence[CategoryUsage]:
    """All categories ordered by name with a count of referencing transactions."""
    result = await session.execute(
        select(Category.id, Category.name, func.count(Transaction.id))
        .outerjoin(Transaction, Transaction.category_id == Category.id)
        .group_by(Category.id, Category.name)
        .order_by(Category.name)
    )
    return [CategoryUsage(*row) for row in result.all()]


async def transaction_count_for_category(
    session: AsyncSession, category_id: int
) -> int:
    """Number of transactions referencing the given category."""
    count = await session.scalar(
        select(func.count(Transaction.id)).where(Transaction.category_id == category_id)
    )
    return int(count or 0)


_CATEGORY_TXN_COUNT = func.count(Transaction.id).label("txn_count")

_CATEGORY_SORTS: dict[str, Any] = {
    "name": Category.name,
    "txn_count": _CATEGORY_TXN_COUNT,
}


def _categories_query() -> Select[Any]:
    return (
        select(Category.id, Category.name, _CATEGORY_TXN_COUNT)
        .outerjoin(Transaction, Transaction.category_id == Category.id)
        .group_by(Category.id, Category.name)
    )


async def fetch_categories_page(
    session: AsyncSession,
    *,
    sorters: Sequence[dict[str, Any]] | None = None,
    filters: Sequence[dict[str, Any]] | None = None,
    page: int = 1,
    page_size: int = 25,
) -> TablePage:
    """One page of categories with their transaction counts."""
    query = _categories_query()

    for spec in filters or ():
        if str(spec.get("field", "")) != "name":
            continue
        value = spec.get("value")
        if value in (None, ""):
            continue
        query = query.where(Category.name.ilike(f"%{escape_like(str(value))}%"))

    total_count = int(
        await session.scalar(select(func.count()).select_from(query.subquery())) or 0
    )
    total_pages = max(1, ceil(total_count / page_size))
    page = min(page, total_pages)
    offset = (page - 1) * page_size

    order_by = []
    for sorter in sorters or ():
        col = _CATEGORY_SORTS.get(str(sorter.get("field", "")))
        if col is None:
            continue
        order_by.append(
            col.asc() if str(sorter.get("dir", "asc")).lower() == "asc" else col.desc()
        )
    if not order_by:
        order_by.append(Category.name.asc())

    result = await session.execute(
        query.order_by(*order_by).offset(offset).limit(page_size)
    )
    return TablePage(result.all(), total_count, page, page_size, total_pages)
