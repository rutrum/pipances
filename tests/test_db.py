from sqlalchemy import text

from pipances.db import Database


async def test_create_tables_idempotent():
    """Calling create_tables() twice should not error."""
    database = Database("sqlite+aiosqlite:///:memory:")
    try:
        await database.create_tables()
        await database.create_tables()
        # No error = pass
    finally:
        await database.dispose()


async def test_migration_adds_missing_columns():
    """create_tables() should add columns missing from older schema versions."""
    database = Database("sqlite+aiosqlite:///:memory:")
    try:
        await database.create_tables()
        async with database.engine.connect() as conn:
            result = await conn.execute(text("PRAGMA table_info(accounts)"))
            columns = {row[1] for row in result}
            assert "starting_balance_cents" in columns
            assert "balance_date" in columns
            assert "active" in columns

            result = await conn.execute(text("PRAGMA table_info(transactions)"))
            txn_columns = {row[1] for row in result}
            assert "category_id" in txn_columns
            assert "ml_confidence_description" in txn_columns
            assert "ml_confidence_category" in txn_columns
            assert "ml_confidence_external" in txn_columns
    finally:
        await database.dispose()
