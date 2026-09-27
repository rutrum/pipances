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
    # Accounts are typed internal or external; the merchant/payee kind is
    # "external". (An earlier rename used "counter_account" as the kind.)
    await conn.execute(
        text("UPDATE accounts SET kind = 'external' WHERE kind = 'counter_account'")
    )


async def migrate_transactions(conn: AsyncConnection) -> None:
    columns = await _columns(conn, "transactions")
    # The transaction's other side is its counter account (internal or external).
    if "external_id" in columns and "counter_account_id" not in columns:
        await conn.execute(
            text(
                "ALTER TABLE transactions RENAME COLUMN external_id TO counter_account_id"
            )
        )
    if "ml_confidence_external" in columns:
        if "ml_confidence_counter_account" not in columns:
            await conn.execute(
                text(
                    "ALTER TABLE transactions RENAME COLUMN ml_confidence_external"
                    " TO ml_confidence_counter_account"
                )
            )
        else:
            # A previously half-applied rename left both columns; carry the
            # legacy confidence values over before dropping the old column.
            await conn.execute(
                text(
                    "UPDATE transactions SET ml_confidence_counter_account ="
                    " ml_confidence_external WHERE ml_confidence_counter_account IS NULL"
                )
            )
            await conn.execute(
                text("ALTER TABLE transactions DROP COLUMN ml_confidence_external")
            )
    columns = await _columns(conn, "transactions")
    migrations = {
        "category_id": "ALTER TABLE transactions ADD COLUMN category_id INTEGER REFERENCES categories(id)",
        "ml_confidence_description": "ALTER TABLE transactions ADD COLUMN ml_confidence_description REAL",
        "ml_confidence_category": "ALTER TABLE transactions ADD COLUMN ml_confidence_category REAL",
        "ml_confidence_counter_account": "ALTER TABLE transactions ADD COLUMN ml_confidence_counter_account REAL",
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


async def migrate_imports(conn: AsyncConnection) -> None:
    columns = await _columns(conn, "imports")
    migrations = {
        "importer_id": (
            "ALTER TABLE imports ADD COLUMN importer_id INTEGER "
            "REFERENCES importers(id) ON DELETE SET NULL"
        ),
        "importer_name": "ALTER TABLE imports ADD COLUMN importer_name VARCHAR",
        "importer_sql": "ALTER TABLE imports ADD COLUMN importer_sql TEXT",
    }
    for column, ddl in migrations.items():
        if column not in columns:
            await conn.execute(text(ddl))
