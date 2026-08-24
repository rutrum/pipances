"""Transaction queries and loader helpers.

Session-first: every function takes an open AsyncSession and leaves
transaction boundaries (commit/rollback) to the caller.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date
from math import ceil
from typing import Any, NamedTuple

from sqlalchemy import ColumnElement, UnaryExpression, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.interfaces import ORMOption
from sqlalchemy.sql import Select

from pipances.models import (
    Account,
    AccountKind,
    Category,
    Transaction,
    TransactionSplit,
    TransactionStatus,
)

VISIBLE_STATUSES: tuple[TransactionStatus, ...] = (
    TransactionStatus.APPROVED,
    TransactionStatus.PENDING,
)


def _column(attr: Any) -> ColumnElement[Any]:
    """Runtime view of an instrumented attribute as a column expression."""
    return attr


SORT_COLUMNS: dict[str, ColumnElement[Any]] = {
    "date": _column(Transaction.date),
    "amount": _column(Transaction.amount_cents),
    "amount_cents": _column(Transaction.amount_cents),
    "description": _column(Transaction.raw_description),
}


def statuses_where(statuses: Sequence[TransactionStatus]) -> ColumnElement[bool]:
    """WHERE clause matching any of the given transaction statuses."""
    if len(statuses) == 1:
        return Transaction.status == statuses[0]
    return Transaction.status.in_(statuses)


async def pending_txn_count(session: AsyncSession) -> int:
    """Number of transactions awaiting review."""
    count = await session.scalar(
        select(func.count())
        .select_from(Transaction)
        .where(Transaction.status == TransactionStatus.PENDING)
    )
    return int(count or 0)


def txn_options(
    *, splits: bool = False, import_record: bool = False
) -> list[ORMOption]:
    """Eager-loading options covering the relationships templates render."""
    options: list[ORMOption] = [
        selectinload(Transaction.internal),
        selectinload(Transaction.external),
        selectinload(Transaction.category),
    ]
    if splits:
        options.append(
            selectinload(Transaction.splits).selectinload(TransactionSplit.category)
        )
    if import_record:
        options.append(selectinload(Transaction.import_record))
    return options


async def get_txn(
    session: AsyncSession,
    txn_id: int,
    *,
    splits: bool = False,
    import_record: bool = False,
) -> Transaction | None:
    """Fetch one transaction by primary key with eager loads applied."""
    return await session.get(
        Transaction,
        txn_id,
        options=txn_options(splits=splits, import_record=import_record),
    )


def apply_filters(
    query: Select,
    *,
    date_from: date | None = None,
    date_to: date | None = None,
    internal_filter: str | None = None,
    external_filter: str | None = None,
    category_filter: str | None = None,
    internal_id: int | None = None,
    import_id: int | None = None,
    exclude_transfers: bool = False,
    description_filter: str | None = None,
    category_name_filter: str | None = None,
    external_name_filter: str | None = None,
    internal_name_filter: str | None = None,
) -> Select:
    """Apply the standard transaction filters to any SELECT against transactions."""
    if date_from is not None:
        query = query.where(Transaction.date >= date_from)
    if date_to is not None:
        query = query.where(Transaction.date <= date_to)
    if internal_filter:
        query = query.join(Transaction.internal).where(Account.name == internal_filter)
    if internal_id is not None:
        query = query.where(Transaction.internal_id == internal_id)
    if external_filter:
        query = query.join(Transaction.external).where(Account.name == external_filter)
    if import_id is not None:
        query = query.where(Transaction.import_id == import_id)
    if category_filter == "__uncategorized__":
        query = query.where(Transaction.category_id.is_(None))
    elif category_filter:
        query = query.join(Transaction.category).where(Category.name == category_filter)
    if description_filter:
        query = query.where(Transaction.description.ilike(f"%{description_filter}%"))
    if category_name_filter:
        query = query.join(Transaction.category).where(
            Category.name.ilike(f"%{category_name_filter}%")
        )
    if external_name_filter:
        query = query.join(Transaction.external).where(
            Account.name.ilike(f"%{external_name_filter}%")
        )
    if internal_name_filter:
        query = query.join(Transaction.internal).where(
            Account.name.ilike(f"%{internal_name_filter}%")
        )
    if exclude_transfers:
        query = query.join(Transaction.external).where(
            Account.kind == AccountKind.EXTERNAL
        )
    return query


def resolve_order(sort_col: str = "date", sort_dir: str = "desc") -> UnaryExpression:
    """ORDER BY clause for transaction listings, including relationship-name keys."""
    col: ColumnElement[Any]
    if sort_col == "category.name":
        col = (
            select(Category.name)
            .where(Category.id == Transaction.category_id)
            .correlate(Transaction)
            .scalar_subquery()
        )
    elif sort_col == "external_account.name":
        col = (
            select(Account.name)
            .where(Account.id == Transaction.external_id)
            .correlate(Transaction)
            .scalar_subquery()
        )
    elif sort_col == "internal_account.name":
        col = (
            select(Account.name)
            .where(Account.id == Transaction.internal_id)
            .correlate(Transaction)
            .scalar_subquery()
        )
    else:
        col = SORT_COLUMNS.get(sort_col, _column(Transaction.date))
    return col.asc() if sort_dir == "asc" else col.desc()


def remaining_split_capacity(
    txn: Transaction, *, excluding_split_id: int | None = None
) -> int:
    """Cents still allocatable to a split before eliminating the remainder."""
    allocated = sum(s.amount_cents for s in txn.splits if s.id != excluding_split_id)
    return abs(txn.amount_cents) - allocated


def set_txn_description(txn: Transaction, value: str | None) -> None:
    """Assign a description, discarding any ML suggestion confidence."""
    txn.description = value
    txn.ml_confidence_description = None


def set_txn_category(txn: Transaction, category: Category | None) -> None:
    """Assign a category, discarding any ML suggestion confidence."""
    txn.category_id = category.id if category else None
    txn.category = category
    txn.ml_confidence_category = None


def set_txn_external(txn: Transaction, account: Account | None) -> None:
    """Assign an external account, discarding any ML suggestion confidence."""
    txn.external_id = account.id if account else None
    txn.external = account
    txn.ml_confidence_external = None


class TxnPage(NamedTuple):
    """One page of transactions plus the pagination metadata derived from it."""

    rows: Sequence[Transaction]
    total_count: int
    page: int
    page_size: int
    total_pages: int


async def fetch_page(
    session: AsyncSession,
    *,
    statuses: Sequence[TransactionStatus] | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    internal_filter: str | None = None,
    external_filter: str | None = None,
    category_filter: str | None = None,
    internal_id: int | None = None,
    import_id: int | None = None,
    exclude_transfers: bool = False,
    description_filter: str | None = None,
    category_name_filter: str | None = None,
    external_name_filter: str | None = None,
    internal_name_filter: str | None = None,
    sort_col: str = "date",
    sort_dir: str = "desc",
    page: int = 1,
    page_size: int = 25,
    splits: bool = False,
    import_record: bool = False,
) -> TxnPage:
    """Count matching transactions, then fetch one sorted page.

    Page numbers beyond the last page are clamped back into range.
    Statuses default to approved + pending.
    """
    base_where = statuses_where(
        tuple(statuses) if statuses is not None else VISIBLE_STATUSES
    )

    def filtered(query: Select) -> Select:
        return apply_filters(
            query,
            date_from=date_from,
            date_to=date_to,
            internal_filter=internal_filter,
            external_filter=external_filter,
            category_filter=category_filter,
            internal_id=internal_id,
            import_id=import_id,
            exclude_transfers=exclude_transfers,
            description_filter=description_filter,
            category_name_filter=category_name_filter,
            external_name_filter=external_name_filter,
            internal_name_filter=internal_name_filter,
        )

    count_query = filtered(
        select(func.count()).select_from(Transaction).where(base_where)
    )
    total_count = int(await session.scalar(count_query) or 0)

    total_pages = max(1, ceil(total_count / page_size))
    page = min(page, total_pages)
    offset = (page - 1) * page_size

    table_query = filtered(
        select(Transaction)
        .where(base_where)
        .options(*txn_options(splits=splits, import_record=import_record)),
    ).order_by(resolve_order(sort_col, sort_dir))

    result = await session.execute(table_query.offset(offset).limit(page_size))
    return TxnPage(result.scalars().all(), total_count, page, page_size, total_pages)
