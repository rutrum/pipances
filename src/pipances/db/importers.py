"""Importer SQL queries.

Session-first: every function takes an open AsyncSession and leaves
transaction boundaries (commit/rollback) to the caller.
"""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from pipances.models import Importer


async def list_importers(session: AsyncSession) -> Sequence[Importer]:
    """All importers ordered by name."""
    result = await session.execute(select(Importer).order_by(Importer.name))
    return result.scalars().all()


async def get_importer(session: AsyncSession, importer_id: int) -> Importer | None:
    """Look up a single importer by id."""
    return await session.get(Importer, importer_id)


async def create_importer(session: AsyncSession, *, name: str, sql: str) -> Importer:
    """Insert a new importer.

    Flushes so the unique-name constraint is enforced immediately; a duplicate
    raises ``IntegrityError``. The caller owns the commit.
    """
    importer = Importer(name=name.strip(), sql=sql)
    session.add(importer)
    await session.flush()
    return importer


async def update_importer(
    session: AsyncSession, importer_id: int, *, name: str | None, sql: str | None
) -> Importer | None:
    """Update the supplied fields on an importer; returns None when missing.

    Flushes so a colliding name raises ``IntegrityError`` immediately. The
    caller owns the commit.
    """
    importer = await session.get(Importer, importer_id)
    if importer is None:
        return None
    if name is not None:
        importer.name = name.strip()
    if sql is not None:
        importer.sql = sql
    await session.flush()
    return importer


async def delete_importer(session: AsyncSession, importer_id: int) -> bool:
    """Delete an importer; returns False when it does not exist.

    Flushes, leaving the commit to the caller.
    """
    importer = await session.get(Importer, importer_id)
    if importer is None:
        return False
    await session.delete(importer)
    await session.flush()
    return True
