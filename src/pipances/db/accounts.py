"""Account queries and resolution helpers. Session-first."""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from pipances.models import Account, AccountKind


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
