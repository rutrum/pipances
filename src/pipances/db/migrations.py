from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection


async def _columns(conn: AsyncConnection, table: str) -> set[str]:
    result = await conn.execute(text(f"PRAGMA table_info({table})"))
    return {row[1] for row in result}


async def migrate_accounts(conn: AsyncConnection) -> None:
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


async def migrate_transactions(conn: AsyncConnection) -> None:
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


async def migrate_transaction_splits(conn: AsyncConnection) -> None:
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
