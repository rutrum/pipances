"""Account queries and resolution helpers. Session-first."""

from __future__ import annotations

from collections.abc import Sequence
from math import ceil
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from pipances.db import TablePage
from pipances.models import Account, AccountKind, Transaction
from pipances.utils import escape_like


async def get_active_internal_accounts(session: AsyncSession) -> Sequence[Account]:
    """Active non-external accounts ordered by name."""
    result = await session.execute(
        select(Account)
        .where(
            Account.kind != AccountKind.EXTERNAL,
            Account.active == True,  # noqa: E712
        )
        .order_by(Account.name)
    )
    return result.scalars().all()


async def get_external_accounts(session: AsyncSession) -> Sequence[Account]:
    """All external accounts ordered by name."""
    result = await session.execute(
        select(Account)
        .where(Account.kind == AccountKind.EXTERNAL)
        .order_by(Account.name)
    )
    return result.scalars().all()


async def get_account_by_name(session: AsyncSession, name: str) -> Account | None:
    """Exact-name account lookup."""
    result = await session.execute(select(Account).where(Account.name == name))
    return result.scalar_one_or_none()


async def get_or_create_external_account(session: AsyncSession, name: str) -> Account:
    """Resolve an external account by case-insensitive name, creating one if missing."""
    result = await session.execute(
        select(Account).where(
            Account.kind == AccountKind.EXTERNAL,
            func.lower(Account.name) == name.lower(),
        )
    )
    account = result.scalar_one_or_none()
    if account is None:
        account = Account(name=name, kind=AccountKind.EXTERNAL)
        session.add(account)
        await session.flush()
    return account


_EXTERNAL_TXN_COUNT = func.count(Transaction.id).label("txn_count")

_EXTERNAL_ACCOUNT_SORTS: dict[str, Any] = {
    "name": Account.name,
    "txn_count": _EXTERNAL_TXN_COUNT,
}


def _external_accounts_query() -> Select[Any]:
    return (
        select(Account.id, Account.name, _EXTERNAL_TXN_COUNT)
        .outerjoin(Transaction, Transaction.external_id == Account.id)
        .where(Account.kind == AccountKind.EXTERNAL)
        .group_by(Account.id, Account.name)
    )


def _apply_external_account_filters(
    query: Select[Any], filters: Sequence[dict[str, Any]] | None
) -> Select[Any]:
    for spec in filters or ():
        if str(spec.get("field", "")) != "name":
            continue
        value = spec.get("value")
        if value in (None, ""):
            continue
        query = query.where(Account.name.ilike(f"%{escape_like(str(value))}%"))
    return query


async def fetch_external_accounts_page(
    session: AsyncSession,
    *,
    sorters: Sequence[dict[str, Any]] | None = None,
    filters: Sequence[dict[str, Any]] | None = None,
    page: int = 1,
    page_size: int = 25,
) -> TablePage:
    """One page of external accounts with their transaction counts."""
    query = _apply_external_account_filters(_external_accounts_query(), filters)

    total_count = int(
        await session.scalar(select(func.count()).select_from(query.subquery())) or 0
    )
    total_pages = max(1, ceil(total_count / page_size))
    page = min(page, total_pages)
    offset = (page - 1) * page_size

    order_by = []
    for sorter in sorters or ():
        col = _EXTERNAL_ACCOUNT_SORTS.get(str(sorter.get("field", "")))
        if col is None:
            continue
        order_by.append(
            col.asc() if str(sorter.get("dir", "asc")).lower() == "asc" else col.desc()
        )
    if not order_by:
        order_by.append(Account.name.asc())

    result = await session.execute(
        query.order_by(*order_by).offset(offset).limit(page_size)
    )
    return TablePage(result.all(), total_count, page, page_size, total_pages)


_ACCOUNT_SORTS: dict[str, Any] = {
    "name": Account.name,
    "kind": Account.kind,
    "starting_balance": Account.starting_balance_cents,
    "balance_date": Account.balance_date,
    "active": Account.active,
}


async def fetch_accounts_page(
    session: AsyncSession,
    *,
    show_closed: bool = False,
    sorters: Sequence[dict[str, Any]] | None = None,
    filters: Sequence[dict[str, Any]] | None = None,
    page: int = 1,
    page_size: int = 25,
) -> TablePage:
    """One page of internal accounts, optionally including closed ones."""
    query = select(Account).where(Account.kind != AccountKind.EXTERNAL)
    if not show_closed:
        query = query.where(Account.active == True)  # noqa: E712

    for spec in filters or ():
        if str(spec.get("field", "")) != "name":
            continue
        value = spec.get("value")
        if value in (None, ""):
            continue
        query = query.where(Account.name.ilike(f"%{escape_like(str(value))}%"))

    total_count = int(
        await session.scalar(select(func.count()).select_from(query.subquery())) or 0
    )
    total_pages = max(1, ceil(total_count / page_size))
    page = min(page, total_pages)
    offset = (page - 1) * page_size

    order_by = []
    for sorter in sorters or ():
        col = _ACCOUNT_SORTS.get(str(sorter.get("field", "")))
        if col is None:
            continue
        order_by.append(
            col.asc() if str(sorter.get("dir", "asc")).lower() == "asc" else col.desc()
        )
    if not order_by:
        order_by.append(Account.name.asc())

    result = await session.execute(
        query.order_by(*order_by).offset(offset).limit(page_size)
    )
    return TablePage(result.scalars().all(), total_count, page, page_size, total_pages)
