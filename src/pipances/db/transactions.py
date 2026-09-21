"""Transaction queries and loader helpers.

Session-first: every function takes an open AsyncSession and leaves
transaction boundaries (commit/rollback) to the caller.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date
from math import ceil
from typing import Any, NamedTuple

from sqlalchemy import (
    ColumnElement,
    String,
    UnaryExpression,
    cast,
    exists,
    func,
    select,
)
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
from pipances.utils import escape_like, safe_date

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


async def marked_txn_count(session: AsyncSession) -> int:
    """Number of pending transactions currently marked for approval."""
    count = await session.scalar(
        select(func.count())
        .select_from(Transaction)
        .where(
            Transaction.status == TransactionStatus.PENDING,
            Transaction.marked_for_approval == True,  # noqa: E712
        )
    )
    return int(count or 0)


class CommitSummary(NamedTuple):
    """Preview of the work a commit would do."""

    count: int
    new_categories: list[str]
    new_externals: list[str]


async def commit_summary(session: AsyncSession) -> CommitSummary:
    """Count marked transactions and the entities a commit would newly create."""
    result = await session.execute(
        select(Transaction)
        .where(
            Transaction.status == TransactionStatus.PENDING,
            Transaction.marked_for_approval == True,  # noqa: E712
        )
        .options(*txn_options(splits=True))
    )
    marked = result.scalars().all()
    if not marked:
        return CommitSummary(0, [], [])

    # Categories referenced only by pending transactions.
    new_category_names: set[str] = set()
    for txn in marked:
        categories = [txn.category] if txn.category else []
        categories.extend(split.category for split in txn.splits if split.category)
        for category in categories:
            approved_ref = await session.execute(
                select(Transaction.id).where(
                    Transaction.category_id == category.id,
                    Transaction.status == TransactionStatus.APPROVED,
                )
            )
            if not approved_ref.first():
                new_category_names.add(category.name)

    # External accounts referenced only by pending transactions.
    new_external_names: set[str] = set()
    for txn in marked:
        if txn.external is None:
            continue
        approved_ref = await session.execute(
            select(Transaction.id).where(
                Transaction.external_id == txn.external_id,
                Transaction.status == TransactionStatus.APPROVED,
            )
        )
        if not approved_ref.first():
            new_external_names.add(txn.external.name)

    return CommitSummary(
        len(marked), sorted(new_category_names), sorted(new_external_names)
    )


async def commit_marked_transactions(session: AsyncSession) -> int:
    """Approve every marked pending transaction; prune orphaned externals.

    Returns the number of transactions committed (0 when nothing was marked).
    """
    result = await session.execute(
        select(Transaction).where(
            Transaction.status == TransactionStatus.PENDING,
            Transaction.marked_for_approval == True,  # noqa: E712
        )
    )
    marked = result.scalars().all()
    if not marked:
        return 0

    for txn in marked:
        txn.status = TransactionStatus.APPROVED
        txn.marked_for_approval = False
    await session.commit()

    orphans = (
        (
            await session.execute(
                select(Account).where(
                    Account.kind == AccountKind.EXTERNAL,
                    ~exists(
                        select(Transaction.id).where(
                            Transaction.external_id == Account.id
                        )
                    ),
                    ~exists(
                        select(Transaction.id).where(
                            Transaction.internal_id == Account.id
                        )
                    ),
                )
            )
        )
        .scalars()
        .all()
    )
    for orphan in orphans:
        await session.delete(orphan)
    await session.commit()
    return len(marked)


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


def _sort_expression(sort_col: str) -> ColumnElement[Any] | None:
    """Map a client-facing sort field to a SQL expression, or None if unknown."""
    if sort_col == "category.name":
        return (
            select(Category.name)
            .where(Category.id == Transaction.category_id)
            .correlate(Transaction)
            .scalar_subquery()
        )
    if sort_col == "external_account.name":
        return (
            select(Account.name)
            .where(Account.id == Transaction.external_id)
            .correlate(Transaction)
            .scalar_subquery()
        )
    if sort_col == "internal_account.name":
        return (
            select(Account.name)
            .where(Account.id == Transaction.internal_id)
            .correlate(Transaction)
            .scalar_subquery()
        )
    return SORT_COLUMNS.get(sort_col)


def resolve_order(sort_col: str = "date", sort_dir: str = "desc") -> UnaryExpression:
    """ORDER BY clause for transaction listings, including relationship-name keys."""
    col = _sort_expression(sort_col) or _column(Transaction.date)
    return col.asc() if sort_dir == "asc" else col.desc()


def order_clauses(sorters: Sequence[dict[str, Any]]) -> list[UnaryExpression]:
    """Compose an ORDER BY list from Tabulator ``sorters`` payload entries.

    Unknown fields are ignored. Falls back to most-recent-first when nothing
    usable was supplied.
    """
    clauses: list[UnaryExpression] = []
    for sorter in sorters:
        field = str(sorter.get("field", ""))
        # The Tabulator page displays `description` (not `raw_description`), so
        # sort on what the user sees. Legacy resolve_order keeps raw_description.
        col = (
            _column(Transaction.description)
            if field == "description"
            else _sort_expression(field)
        )
        if col is None:
            continue
        direction = str(sorter.get("dir", "asc")).lower()
        clauses.append(col.asc() if direction == "asc" else col.desc())
    if not clauses:
        clauses.append(_column(Transaction.date).desc())
    return clauses


# Client field -> (column, value kind) for Tabulator-style filters.
_FILTER_COLUMNS: dict[str, tuple[ColumnElement[Any], str]] = {
    "date": (_column(Transaction.date), "date"),
    "amount": (_column(Transaction.amount_cents), "amount"),
    "description": (_column(Transaction.description), "text"),
    "status": (_column(Transaction.status), "text"),
}

# Client field -> (relationship, related column) for filters on joined names.
_FILTER_RELATIONSHIPS: dict[str, tuple[Any, ColumnElement[Any]]] = {
    "category.name": (Transaction.category, _column(Category.name)),
    "external_account.name": (Transaction.external, _column(Account.name)),
    "internal_account.name": (Transaction.internal, _column(Account.name)),
}


def _coerce_value(value: Any, kind: str) -> Any:
    """Coerce a raw filter value to the column's expected Python type."""
    if kind == "date":
        return safe_date(str(value)) if value is not None else None
    if kind == "amount":
        try:
            return int(round(float(value) * 100))
        except (TypeError, ValueError):
            return None
    return value


def _apply_operator(col: ColumnElement[Any], op: str, value: Any) -> Any:
    """Build a WHERE clause for one column/operator/value triple."""
    op = op.lower()
    if op in ("like", "starts", "ends"):
        pattern = escape_like(str(value))
        if op == "like":
            pattern = f"%{pattern}%"
        elif op == "starts":
            pattern = f"{pattern}%"
        else:
            pattern = f"%{pattern}"
        return col.ilike(pattern)
    if op == "=":
        return col == value
    if op == "!=":
        return col != value
    if op == "<":
        return col < value
    if op == "<=":
        return col <= value
    if op == ">":
        return col > value
    if op == ">=":
        return col >= value
    if op == "in":
        return col.in_(value if isinstance(value, list) else [value])
    return None


def apply_tabulator_filters(query: Select, filters: Sequence[dict[str, Any]]) -> Select:
    """Apply Tabulator ``filters`` payload entries to a transaction SELECT.

    Relationship-name filters use ``.has()`` so repeated filters on the same
    relationship never produce duplicate/ambiguous joins. Unknown fields and
    unsupported operators are ignored.
    """
    for spec in filters:
        field = str(spec.get("field", ""))
        op = str(spec.get("type", "like"))
        raw_value = spec.get("value")
        if raw_value is None or raw_value == "":
            continue

        if field in _FILTER_COLUMNS:
            col, kind = _FILTER_COLUMNS[field]
            value = _coerce_value(raw_value, kind)
            if value is None:
                continue
            # Numeric `like` from a header filter degrades to a text match.
            if kind == "amount" and op.lower() in ("like", "starts", "ends"):
                clause = _apply_operator(cast(col, String), op, str(raw_value))
            else:
                clause = _apply_operator(col, op, value)
        elif field in _FILTER_RELATIONSHIPS:
            rel, col = _FILTER_RELATIONSHIPS[field]
            clause = _apply_operator(col, op, raw_value)
            if clause is None:
                continue
            query = query.where(rel.has(clause))
            continue
        else:
            continue

        if clause is not None:
            query = query.where(clause)
    return query


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
    sorters: Sequence[dict[str, Any]] | None = None,
    tabulator_filters: Sequence[dict[str, Any]] | None = None,
    page: int = 1,
    page_size: int = 25,
    splits: bool = False,
    import_record: bool = False,
) -> TxnPage:
    """Count matching transactions, then fetch one sorted page.

    Page numbers beyond the last page are clamped back into range.
    Statuses default to approved + pending. ``sorters``/``tabulator_filters``
    accept Tabulator remote payload entries and override ``sort_col``/``sort_dir``.
    """
    base_where = statuses_where(
        tuple(statuses) if statuses is not None else VISIBLE_STATUSES
    )

    def filtered(query: Select) -> Select:
        query = apply_filters(
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
        if tabulator_filters:
            query = apply_tabulator_filters(query, tabulator_filters)
        return query

    count_query = filtered(
        select(func.count()).select_from(Transaction).where(base_where)
    )
    total_count = int(await session.scalar(count_query) or 0)

    total_pages = max(1, ceil(total_count / page_size))
    page = min(page, total_pages)
    offset = (page - 1) * page_size

    if sorters:
        order_by = order_clauses(sorters)
    else:
        order_by = [resolve_order(sort_col, sort_dir)]

    table_query = filtered(
        select(Transaction)
        .where(base_where)
        .options(*txn_options(splits=splits, import_record=import_record)),
    ).order_by(*order_by)

    result = await session.execute(table_query.offset(offset).limit(page_size))
    return TxnPage(result.scalars().all(), total_count, page, page_size, total_pages)
