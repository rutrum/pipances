from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from financial_pipeline.models import Base

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATABASE_URL = f"sqlite+aiosqlite:///{PROJECT_ROOT / 'financial_pipeline.db'}"

engine = create_async_engine(DATABASE_URL)
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


async def get_session():
    async with async_session() as session:
        yield session
