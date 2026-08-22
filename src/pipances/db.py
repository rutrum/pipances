from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from pipances.models import Base
from pipances.settings import settings

engine = create_async_engine(settings.database_url)


@event.listens_for(engine.sync_engine, "connect")
def _set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.close()


async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Migrate existing accounts table if missing new columns
        result = await conn.execute(text("PRAGMA table_info(accounts)"))
        columns = {row[1] for row in result}
        if "starting_balance_cents" not in columns:
            await conn.execute(
                text(
                    "ALTER TABLE accounts ADD COLUMN starting_balance_cents INTEGER NOT NULL DEFAULT 0"
                )
            )
        if "balance_date" not in columns:
            await conn.execute(
                text("ALTER TABLE accounts ADD COLUMN balance_date DATE")
            )
        if "active" not in columns:
            await conn.execute(
                text(
                    "ALTER TABLE accounts ADD COLUMN active BOOLEAN NOT NULL DEFAULT 1"
                )
            )
        # Migrate existing transactions table if missing columns
        result = await conn.execute(text("PRAGMA table_info(transactions)"))
        txn_columns = {row[1] for row in result}
        if "category_id" not in txn_columns:
            await conn.execute(
                text(
                    "ALTER TABLE transactions ADD COLUMN category_id INTEGER REFERENCES categories(id)"
                )
            )
        if "ml_confidence_description" not in txn_columns:
            await conn.execute(
                text(
                    "ALTER TABLE transactions ADD COLUMN ml_confidence_description REAL"
                )
            )
        if "ml_confidence_category" not in txn_columns:
            await conn.execute(
                text("ALTER TABLE transactions ADD COLUMN ml_confidence_category REAL")
            )
        if "ml_confidence_external" not in txn_columns:
            await conn.execute(
                text("ALTER TABLE transactions ADD COLUMN ml_confidence_external REAL")
            )
        # Migrate: create transaction_splits table if it doesn't exist
        result = await conn.execute(text("PRAGMA table_info(transaction_splits)"))
        if not result.fetchone():
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
