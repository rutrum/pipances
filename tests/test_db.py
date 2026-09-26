import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from pipances.db import Database
from pipances.db.importers import (
    create_importer,
    delete_importer,
    get_importer,
    list_importers,
    update_importer,
)
from pipances.db.migrations import migrate_imports
from pipances.models import Import


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


async def test_create_tables_creates_importers_table():
    """create_all() creates the importers table with its full column set."""
    database = Database("sqlite+aiosqlite:///:memory:")
    try:
        await database.create_tables()
        async with database.engine.connect() as conn:
            result = await conn.execute(text("PRAGMA table_info(importers)"))
            columns = {row[1] for row in result}
            assert {"id", "name", "sql", "created_at", "updated_at"} <= columns
    finally:
        await database.dispose()


async def test_importer_crud_round_trip(session):
    """create -> list -> get -> update -> delete round trip."""
    importer = await create_importer(session, name="Bank A", sql="SELECT 1")
    await session.commit()
    assert importer.id is not None

    listed = await list_importers(session)
    assert [item.name for item in listed] == ["Bank A"]

    fetched = await get_importer(session, importer.id)
    assert fetched is not None
    assert fetched.sql == "SELECT 1"

    updated = await update_importer(session, importer.id, name="Bank B", sql="SELECT 2")
    assert updated is not None
    assert updated.name == "Bank B"
    assert updated.sql == "SELECT 2"
    await session.commit()

    assert await delete_importer(session, importer.id) is True
    await session.commit()
    assert await get_importer(session, importer.id) is None
    assert await delete_importer(session, importer.id) is False


async def test_create_importer_duplicate_name_raises(session):
    """A duplicate name surfaces as IntegrityError, not a silent merge."""
    await create_importer(session, name="Bank", sql="SELECT 1")
    await session.commit()

    with pytest.raises(IntegrityError):
        await create_importer(session, name="Bank", sql="SELECT 2")
    await session.rollback()


async def test_update_importer_to_colliding_name_raises(session):
    """Renaming onto an existing name surfaces as IntegrityError."""
    first = await create_importer(session, name="Bank A", sql="SELECT 1")
    await create_importer(session, name="Bank B", sql="SELECT 2")
    await session.commit()

    with pytest.raises(IntegrityError):
        await update_importer(session, first.id, name="Bank B", sql=None)
    await session.rollback()


async def test_migrate_imports_adds_columns_idempotent():
    """migrate_imports() adds the provenance columns and is a no-op on rerun."""
    database = Database("sqlite+aiosqlite:///:memory:")
    try:
        async with database.engine.begin() as conn:
            # Simulate a legacy schema that predates the provenance columns.
            await conn.execute(text("CREATE TABLE importers (id INTEGER PRIMARY KEY)"))
            await conn.execute(
                text(
                    "CREATE TABLE imports ("
                    "id INTEGER NOT NULL PRIMARY KEY, "
                    "institution VARCHAR NOT NULL"
                    ")"
                )
            )

            await migrate_imports(conn)
            result = await conn.execute(text("PRAGMA table_info(imports)"))
            columns = {row[1] for row in result}
            assert {"importer_id", "importer_name", "importer_sql"} <= columns

            # Second run must not error or alter the schema further.
            await migrate_imports(conn)
            result = await conn.execute(text("PRAGMA table_info(imports)"))
            assert {row[1] for row in result} == columns
    finally:
        await database.dispose()


async def test_import_provenance_defaults_null_and_accepts_values(session):
    """The provenance columns default to NULL and store snapshots."""
    record = Import(institution="bank")
    session.add(record)
    await session.commit()
    assert record.importer_id is None
    assert record.importer_name is None
    assert record.importer_sql is None

    importer = await create_importer(session, name="Bank", sql="SELECT 1")
    await session.commit()

    record.importer_id = importer.id
    record.importer_name = importer.name
    record.importer_sql = importer.sql
    await session.commit()

    assert record.importer_id == importer.id
    assert record.importer_name == "Bank"
    assert record.importer_sql == "SELECT 1"
