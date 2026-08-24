"""Category queries and resolution helpers. Session-first."""

from __future__ import annotations

from collections.abc import Sequence
from typing import NamedTuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from pipances.db.transactions import VISIBLE_STATUSES, statuses_where
from pipances.models import Category, Transaction, TransactionStatus


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
