#!/usr/bin/env python3
"""One-off script to load manually curated transfers into the database."""

import argparse
import asyncio
from pathlib import Path

import polars as pl
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Add src to path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pipances.models import (
    Account,
    AccountKind,
    Category,
    Import,
    Transaction,
    TransactionStatus,
    Base,
)


def _infer_account_kind(name: str) -> AccountKind:
    n = name.lower()
    if "citi" in n or "credit" in n:
        return AccountKind.CREDIT_CARD
    elif "savings" in n:
        return AccountKind.SAVINGS
    elif "checking" in n:
        return AccountKind.CHECKING
    return AccountKind.EXTERNAL


async def load_transfers(engine, df: pl.DataFrame) -> int:
    async_session_maker = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    internal_names = df["internal"].unique().to_list()
    external_names = df["external"].unique().to_list()
    category_names = [c for c in df["category"].unique().to_list() if c]

    async with async_session_maker() as session:
        # Ensure internal accounts exist
        internal_id_map = {}
        for name in internal_names:
            account = await session.scalar(select(Account).where(Account.name == name))
            if account is None:
                account = Account(name=name, kind=_infer_account_kind(name))
                session.add(account)
                await session.flush()
            internal_id_map[name] = account.id

        # Ensure external accounts exist
        external_id_map = {}
        for name in external_names:
            account = await session.scalar(select(Account).where(Account.name == name))
            if account is None:
                account = Account(name=name, kind=AccountKind.EXTERNAL)
                session.add(account)
                await session.flush()
            external_id_map[name] = account.id

        # Ensure categories exist
        category_id_map = {}
        for name in category_names:
            category = await session.scalar(
                select(Category).where(Category.name == name)
            )
            if category is None:
                category = Category(name=name)
                session.add(category)
                await session.flush()
            category_id_map[name] = category.id
        category_id_map[None] = None

        # Create Import record
        import_record = Import(
            institution="me",
            filename="finanal.load_transfers",
            row_count=len(df),
        )
        session.add(import_record)
        await session.flush()

        # Insert transactions
        for row in df.iter_rows(named=True):
            txn = Transaction(
                import_id=import_record.id,
                internal_id=internal_id_map[row["internal"]],
                external_id=external_id_map[row["external"]],
                raw_description=row["description"],
                description=None,
                date=row["date"],
                amount_cents=int(row["amount"] * 100),
                status=TransactionStatus.APPROVED,
                category_id=category_id_map.get(row["category"]),
            )
            session.add(txn)

        await session.commit()
        return import_record.id


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("db_path", help="Path to SQLite database")
    parser.add_argument("input_path", help="Path to input parquet file")
    args = parser.parse_args()

    db_url = f"sqlite+aiosqlite:///{args.db_path}"
    engine = create_async_engine(db_url)

    # Create tables if they don't exist
    import sqlalchemy
    from sqlalchemy import event

    @event.listens_for(engine.sync_engine, "connect")
    def _set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.close()

    import asyncio
    from sqlalchemy.ext.asyncio import AsyncEngine

    async def _create_tables():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    asyncio.run(_create_tables())

    df = pl.read_parquet(args.input_path)

    import_id = asyncio.run(load_transfers(engine, df))
    print(f"Created import record with id: {import_id}")


if __name__ == "__main__":
    main()
