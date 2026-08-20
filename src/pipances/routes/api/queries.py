"""Shared query logic used by multiple API endpoints.

Kept in the api package because its sole consumer is the JSON API.
If HTML routes need it later, extract to a top-level services/ module.
"""

from __future__ import annotations

from datetime import date
from math import ceil
from typing import Any

from sqlalchemy import func, select
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import Select

from pipances.db import async_session
from pipances.models import (
    Account,
    AccountKind,
    Category,
    Import,
    Transaction,
    TransactionSplit,
    TransactionStatus,
)
from pipances.routes.transactions import SORT_COLUMNS as BASE_SORT_COLUMNS

# Extended sort columns: also handles Tabulator field names which differ from old keys
SORT_COLUMNS: dict[str, Any] = {
    **BASE_SORT_COLUMNS,
    "amount_cents": BASE_SORT_COLUMNS.get("amount"),  # Tabulator sends field name
    "category.name": Category.name,
}


def build_filters(
    query: Select,
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
    if date_from is not None:
        query = query.where(Transaction.date >= date_from)
    if date_to is not None:
        query = query.where(Transaction.date <= date_to)
    if internal_filter:
        query = query.join(Transaction.internal).where(
            Account.name == internal_filter
        )
    if internal_id is not None:
        query = query.where(Transaction.internal_id == internal_id)
    if external_filter:
        query = query.join(Transaction.external).where(
            Account.name == external_filter
        )
    if import_id is not None:
        query = query.where(Transaction.import_id == import_id)
    if category_filter == "__uncategorized__":
        query = query.where(Transaction.category_id.is_(None))
    elif category_filter:
        query = query.join(Transaction.category).where(
            Category.name == category_filter
        )
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


def transaction_to_dict(txn: Transaction) -> dict[str, Any]:
    ml: dict[str, float | None] = {}
    if txn.ml_confidence_description is not None:
        ml["description"] = txn.ml_confidence_description
    if txn.ml_confidence_category is not None:
        ml["category"] = txn.ml_confidence_category
    if txn.ml_confidence_external is not None:
        ml["external"] = txn.ml_confidence_external

    result: dict[str, Any] = {
        "id": txn.id,
        "date": str(txn.date),
        "amount_cents": txn.amount_cents,
        "raw_description": txn.raw_description,
        "description": txn.description,
        "status": txn.status,
        "marked_for_approval": txn.marked_for_approval,
        "ml_confidence": ml if ml else None,
        "category": (
            {"id": txn.category.id, "name": txn.category.name}
            if txn.category
            else None
        ),
        "external_account": (
            {"id": txn.external.id, "name": txn.external.name}
            if txn.external
            else None
        ),
        "internal_account": (
            {"id": txn.internal.id, "name": txn.internal.name}
            if txn.internal
            else None
        ),
        "import_id": txn.import_id,
    }
    if "splits" not in sa_inspect(txn).unloaded:
        result["splits"] = [
            {
                "id": s.id,
                "amount_cents": s.amount_cents,
                "category": (
                    {"id": s.category.id, "name": s.category.name}
                    if s.category
                    else None
                ),
            }
            for s in txn.splits
        ]
    return result


async def query_transactions(
    *,
    statuses: list[TransactionStatus] | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    internal_filter: str | None = None,
    external_filter: str | None = None,
    category_filter: str | None = None,
    internal_id: int | None = None,
    import_id: int | None = None,
    sort_col: str = "date",
    sort_dir: str = "desc",
    page: int = 1,
    page_size: int = 25,
    exclude_transfers: bool = False,
    load_splits: bool = False,
    description_filter: str | None = None,
    category_name_filter: str | None = None,
    external_name_filter: str | None = None,
    internal_name_filter: str | None = None,
) -> dict[str, Any]:
    async with async_session() as session:
        statuses = statuses or [
            TransactionStatus.APPROVED,
            TransactionStatus.PENDING,
        ]
        base_where = Transaction.status.in_(statuses)

        options = [
            selectinload(Transaction.internal),
            selectinload(Transaction.external),
            selectinload(Transaction.category),
        ]
        if load_splits:
            options.append(
                selectinload(Transaction.splits).selectinload(
                    TransactionSplit.category
                )
            )

        count_query = (
            select(func.count()).select_from(Transaction).where(base_where)
        )
        count_query = build_filters(
            count_query,
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
        total_count = await session.scalar(count_query)

        total_pages = max(1, ceil(total_count / page_size))
        page = min(page, total_pages)
        offset = (page - 1) * page_size

        table_query = (
            select(Transaction).where(base_where).options(*options)
        )
        table_query = build_filters(
            table_query,
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

        # Resolve sort column — use correlated subqueries for related entity names
        # to avoid join conflicts with build_filters
        if sort_col == "category.name":
            from sqlalchemy import select as sa_select
            col = (
                sa_select(Category.name)
                .where(Category.id == Transaction.category_id)
                .correlate(Transaction)
                .scalar_subquery()
            )
        elif sort_col == "external_account.name":
            from sqlalchemy import select as sa_select
            col = (
                sa_select(Account.name)
                .where(Account.id == Transaction.external_id)
                .correlate(Transaction)
                .scalar_subquery()
            )
        elif sort_col == "internal_account.name":
            from sqlalchemy import select as sa_select
            col = (
                sa_select(Account.name)
                .where(Account.id == Transaction.internal_id)
                .correlate(Transaction)
                .scalar_subquery()
            )
        elif sort_col == "amount_cents":
            col = Transaction.amount_cents
        elif sort_col == "amount":
            col = Transaction.amount_cents
        else:
            col = SORT_COLUMNS.get(sort_col, Transaction.date)
        if sort_dir == "asc":
            table_query = table_query.order_by(col.asc())
        else:
            table_query = table_query.order_by(col.desc())

        result = await session.execute(
            table_query.offset(offset).limit(page_size)
        )
        transactions = result.scalars().all()

    return {
        "data": [transaction_to_dict(t) for t in transactions],
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total_count,
            "total_pages": total_pages,
        },
    }


async def get_categories() -> list[dict]:
    async with async_session() as session:
        result = await session.execute(
            select(Category).order_by(Category.name)
        )
        return [{"id": c.id, "name": c.name} for c in result.scalars().all()]


async def get_internal_accounts() -> list[dict]:
    async with async_session() as session:
        result = await session.execute(
            select(Account)
            .where(
                Account.kind != AccountKind.EXTERNAL,
                Account.active == True,  # noqa: E712
            )
            .order_by(Account.name)
        )
        return [
            {"id": a.id, "name": a.name, "kind": a.kind, "active": a.active}
            for a in result.scalars().all()
        ]


async def get_external_accounts() -> list[dict]:
    async with async_session() as session:
        result = await session.execute(
            select(Account)
            .where(Account.kind == AccountKind.EXTERNAL)
            .order_by(Account.name)
        )
        return [
            {"id": a.id, "name": a.name, "kind": a.kind, "active": a.active}
            for a in result.scalars().all()
        ]


async def get_imports() -> list[dict]:
    async with async_session() as session:
        result = await session.execute(
            select(Import).order_by(Import.imported_at.desc())
        )
        return [
            {
                "id": imp.id,
                "institution": imp.institution,
                "filename": imp.filename,
                "imported_at": str(imp.imported_at),
                "row_count": imp.row_count,
            }
            for imp in result.scalars().all()
        ]
