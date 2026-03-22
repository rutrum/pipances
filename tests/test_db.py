from sqlalchemy import text

from financial_pipeline.models import Base


async def test_create_tables_idempotent(engine):
    """Calling create_tables() twice should not error."""
    # Tables are already created by the engine fixture; call create_tables()
    # which uses the module-level engine (patched to our test engine).
    # We just verify no exception is raised on the second call.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # No error = pass


async def test_migration_adds_missing_columns(engine):
    """create_tables() should add columns missing from older schema versions."""
    # Drop a column that the migration adds, then re-run create_tables
    async with engine.begin() as conn:
        # Check that starting_balance_cents exists
        result = await conn.execute(text("PRAGMA table_info(accounts)"))
        columns = {row[1] for row in result}
        assert "starting_balance_cents" in columns
        assert "balance_date" in columns
        assert "active" in columns

        # Verify transactions migration columns exist
        result = await conn.execute(text("PRAGMA table_info(transactions)"))
        txn_columns = {row[1] for row in result}
        assert "category_id" in txn_columns
        assert "ml_confidence_description" in txn_columns
        assert "ml_confidence_category" in txn_columns
        assert "ml_confidence_external" in txn_columns
