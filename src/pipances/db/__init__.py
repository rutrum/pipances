from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from pipances.db.migrations import (
    migrate_accounts,
    migrate_transaction_splits,
    migrate_transactions,
)
from pipances.models import Base


def _set_sqlite_pragma(dbapi_conn, connection_record) -> None:
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.close()


class Database:
    """Owns the engine and session factory. Constructed with settings, passed explicitly."""

    def __init__(self, url: str):
        self.engine: AsyncEngine = create_async_engine(url)
        self._sessions = async_sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
        event.listen(self.engine.sync_engine, "connect", _set_sqlite_pragma)

    def session(self) -> AsyncSession:
        """Open a new session. Caller manages the context and transaction."""
        return self._sessions()

    async def create_tables(self) -> None:
        """Create any missing tables, then migrate legacy schemas."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            await migrate_accounts(conn)
            await migrate_transactions(conn)
            await migrate_transaction_splits(conn)

    async def dispose(self) -> None:
        await self.engine.dispose()


def get_database(request: Request) -> Database:
    """FastAPI dependency returning the app-scoped Database instance."""
    database: Database = request.app.state.database
    return database


DatabaseDep = Annotated[Database, Depends(get_database)]
