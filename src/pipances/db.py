from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
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
            await _migrate_accounts(conn)
            await _migrate_transactions(conn)
            await _migrate_transaction_splits(conn)

    async def dispose(self) -> None:
        await self.engine.dispose()


def get_database(request: Request) -> Database:
    """FastAPI dependency returning the app-scoped Database instance."""
    database: Database = request.app.state.database
    return database


DatabaseDep = Annotated[Database, Depends(get_database)]


async def _columns(conn, table: str) -> set[str]:
    result = await conn.execute(text(f"PRAGMA table_info({table})"))
    return {row[1] for row in result}


async def _migrate_accounts(conn) -> None:
    columns = await _columns(conn, "accounts")
    if "starting_balance_cents" not in columns:
        await conn.execute(
            text(
                "ALTER TABLE accounts ADD COLUMN starting_balance_cents INTEGER NOT NULL DEFAULT 0"
            )
        )
    if "balance_date" not in columns:
        await conn.execute(text("ALTER TABLE accounts ADD COLUMN balance_date DATE"))
    if "active" not in columns:
        await conn.execute(
            text("ALTER TABLE accounts ADD COLUMN active BOOLEAN NOT NULL DEFAULT 1")
        )


async def _migrate_transactions(conn) -> None:
    columns = await _columns(conn, "transactions")
    migrations = {
        "category_id": "ALTER TABLE transactions ADD COLUMN category_id INTEGER REFERENCES categories(id)",
        "ml_confidence_description": "ALTER TABLE transactions ADD COLUMN ml_confidence_description REAL",
        "ml_confidence_category": "ALTER TABLE transactions ADD COLUMN ml_confidence_category REAL",
        "ml_confidence_external": "ALTER TABLE transactions ADD COLUMN ml_confidence_external REAL",
    }
    for column, ddl in migrations.items():
        if column not in columns:
            await conn.execute(text(ddl))


async def _migrate_transaction_splits(conn) -> None:
    result = await conn.execute(text("PRAGMA table_info(transaction_splits)"))
    if result.fetchone():
        return
    await conn.execute(
        text(
            "CREATE TABLE transaction_splits ("
            "id INTEGER NOT NULL PRIMARY KEY, "
            "transaction_id INTEGER NOT NULL REFERENCES transactions(id) ON DELETE CASCADE, "
            "category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL, "
            "amount_cents INTEGER NOT NULL"
            ")"
        )
    )
