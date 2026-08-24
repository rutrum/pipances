from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

import polars as pl
import pytest
from sqlalchemy import func, select

from pipances.ingest import ingest
from pipances.models import Import, Transaction
from pipances.schemas import ImportedTransaction

if TYPE_CHECKING:
    import patito as pt


def _make_df(rows: list[dict]) -> pt.DataFrame[ImportedTransaction]:  # type: ignore[name-defined]
    """Build a DataFrame matching ImportedTransaction schema."""
    df = pl.DataFrame(
        {
            "date": [r["date"] for r in rows],
            "amount": [Decimal(str(r["amount"])) for r in rows],
            "description": [r["description"] for r in rows],
        },
        schema={
            "date": pl.Date,
            "amount": pl.Decimal(38, 2),
            "description": pl.Utf8,
        },
    )
    return ImportedTransaction.validate(df)


async def test_amount_conversion_rounds_correctly(database, session, seed_accounts):
    df = _make_df(
        [{"date": date(2026, 1, 15), "amount": 19.99, "description": "Coffee"}]
    )
    result = await ingest(
        database, df, internal_account="Checking", importer_name="test"
    )
    assert result.inserted_count == 1

    txn = await session.scalar(select(Transaction))
    assert txn.amount_cents == 1999


async def test_amount_conversion_negative(database, session, seed_accounts) -> None:
    df = _make_df(
        [{"date": date(2026, 1, 15), "amount": -45.67, "description": "Refund"}]
    )
    result = await ingest(
        database, df, internal_account="Checking", importer_name="test"
    )
    assert result.inserted_count == 1

    txn = await session.scalar(select(Transaction))
    assert txn.amount_cents == -4567


async def test_amount_conversion_exact(database, session, seed_accounts) -> None:
    df = _make_df([{"date": date(2026, 1, 15), "amount": 10.00, "description": "Even"}])
    result = await ingest(
        database, df, internal_account="Checking", importer_name="test"
    )
    assert result.inserted_count == 1

    txn = await session.scalar(select(Transaction))
    assert txn.amount_cents == 1000


async def test_same_file_duplicates_both_inserted(
    database, session, seed_accounts
) -> None:
    df = _make_df(
        [
            {"date": date(2026, 1, 15), "amount": 5.00, "description": "Coffee"},
            {"date": date(2026, 1, 15), "amount": 5.00, "description": "Coffee"},
        ]
    )
    result = await ingest(
        database, df, internal_account="Checking", importer_name="test"
    )
    assert result.inserted_count == 2


async def test_cross_import_duplicates_skipped(
    database, session, seed_accounts
) -> None:
    df = _make_df(
        [{"date": date(2026, 1, 15), "amount": 5.00, "description": "Coffee"}]
    )
    await ingest(database, df, internal_account="Checking", importer_name="test")
    result = await ingest(
        database, df, internal_account="Checking", importer_name="test"
    )
    assert result.inserted_count == 0


async def test_cross_import_partial_overlap(database, session, seed_accounts) -> None:
    df1 = _make_df(
        [
            {"date": date(2026, 1, 15), "amount": 5.00, "description": "Coffee"},
            {"date": date(2026, 1, 16), "amount": 10.00, "description": "Lunch"},
            {"date": date(2026, 1, 17), "amount": 15.00, "description": "Dinner"},
        ]
    )
    await ingest(database, df1, internal_account="Checking", importer_name="test")

    df2 = _make_df(
        [
            {"date": date(2026, 1, 15), "amount": 5.00, "description": "Coffee"},
            {"date": date(2026, 1, 16), "amount": 10.00, "description": "Lunch"},
            {"date": date(2026, 1, 18), "amount": 20.00, "description": "Groceries"},
        ]
    )
    result = await ingest(
        database, df2, internal_account="Checking", importer_name="test"
    )
    assert result.inserted_count == 1
    assert result.duplicate_count == 2


async def test_cross_account_not_deduplicated(database, session, seed_accounts) -> None:
    df = _make_df(
        [{"date": date(2026, 1, 15), "amount": 5.00, "description": "Transfer"}]
    )
    await ingest(database, df, internal_account="Checking", importer_name="test")
    result = await ingest(
        database, df, internal_account="Savings", importer_name="test"
    )
    assert result.inserted_count == 1


async def test_all_duplicates_creates_phantom_import(
    database, session, seed_accounts
) -> None:
    df = _make_df(
        [{"date": date(2026, 1, 15), "amount": 5.00, "description": "Coffee"}]
    )
    await ingest(database, df, internal_account="Checking", importer_name="test")
    result = await ingest(
        database, df, internal_account="Checking", importer_name="test"
    )
    assert result.inserted_count == 0

    count = await session.scalar(select(func.count()).select_from(Import))
    assert count == 2  # phantom import record exists


async def test_missing_internal_account_raises(
    database, session, seed_accounts
) -> None:
    df = _make_df(
        [{"date": date(2026, 1, 15), "amount": 5.00, "description": "Coffee"}]
    )
    with pytest.raises(ValueError, match="not found"):
        await ingest(database, df, internal_account="NonExistent", importer_name="test")
