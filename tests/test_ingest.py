from datetime import date
from decimal import Decimal

import polars as pl
import pytest
from sqlalchemy import func, select

from financial_pipeline.ingest import ingest
from financial_pipeline.models import Import, Transaction


def _make_df(rows: list[dict]) -> pl.DataFrame:
    """Build a DataFrame matching ImportedTransaction schema."""
    return pl.DataFrame(
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


async def test_amount_conversion_rounds_correctly(session, seed_accounts):
    df = _make_df(
        [{"date": date(2026, 1, 15), "amount": 19.99, "description": "Coffee"}]
    )
    result = await ingest(df, internal_account="Checking", importer_name="test")
    assert result.inserted_count == 1

    txn = await session.scalar(select(Transaction))
    assert txn.amount_cents == 1999


async def test_amount_conversion_negative(session, seed_accounts):
    df = _make_df(
        [{"date": date(2026, 1, 15), "amount": -45.67, "description": "Refund"}]
    )
    result = await ingest(df, internal_account="Checking", importer_name="test")
    assert result.inserted_count == 1

    txn = await session.scalar(select(Transaction))
    assert txn.amount_cents == -4567


async def test_amount_conversion_exact(session, seed_accounts):
    df = _make_df([{"date": date(2026, 1, 15), "amount": 10.00, "description": "Even"}])
    result = await ingest(df, internal_account="Checking", importer_name="test")
    assert result.inserted_count == 1

    txn = await session.scalar(select(Transaction))
    assert txn.amount_cents == 1000


async def test_same_file_duplicates_both_inserted(session, seed_accounts):
    df = _make_df(
        [
            {"date": date(2026, 1, 15), "amount": 5.00, "description": "Coffee"},
            {"date": date(2026, 1, 15), "amount": 5.00, "description": "Coffee"},
        ]
    )
    result = await ingest(df, internal_account="Checking", importer_name="test")
    assert result.inserted_count == 2


async def test_cross_import_duplicates_skipped(session, seed_accounts):
    df = _make_df(
        [{"date": date(2026, 1, 15), "amount": 5.00, "description": "Coffee"}]
    )
    await ingest(df, internal_account="Checking", importer_name="test")
    result = await ingest(df, internal_account="Checking", importer_name="test")
    assert result.inserted_count == 0


async def test_cross_import_partial_overlap(session, seed_accounts):
    df1 = _make_df(
        [
            {"date": date(2026, 1, 15), "amount": 5.00, "description": "Coffee"},
            {"date": date(2026, 1, 16), "amount": 10.00, "description": "Lunch"},
            {"date": date(2026, 1, 17), "amount": 15.00, "description": "Dinner"},
        ]
    )
    await ingest(df1, internal_account="Checking", importer_name="test")

    df2 = _make_df(
        [
            {"date": date(2026, 1, 15), "amount": 5.00, "description": "Coffee"},
            {"date": date(2026, 1, 16), "amount": 10.00, "description": "Lunch"},
            {"date": date(2026, 1, 18), "amount": 20.00, "description": "Groceries"},
        ]
    )
    result = await ingest(df2, internal_account="Checking", importer_name="test")
    assert result.inserted_count == 1
    assert result.duplicate_count == 2


async def test_cross_account_not_deduplicated(session, seed_accounts):
    df = _make_df(
        [{"date": date(2026, 1, 15), "amount": 5.00, "description": "Transfer"}]
    )
    await ingest(df, internal_account="Checking", importer_name="test")
    result = await ingest(df, internal_account="Savings", importer_name="test")
    assert result.inserted_count == 1


async def test_all_duplicates_creates_phantom_import(session, seed_accounts):
    df = _make_df(
        [{"date": date(2026, 1, 15), "amount": 5.00, "description": "Coffee"}]
    )
    await ingest(df, internal_account="Checking", importer_name="test")
    result = await ingest(df, internal_account="Checking", importer_name="test")
    assert result.inserted_count == 0

    count = await session.scalar(select(func.count()).select_from(Import))
    assert count == 2  # phantom import record exists


async def test_missing_internal_account_raises(session, seed_accounts):
    df = _make_df(
        [{"date": date(2026, 1, 15), "amount": 5.00, "description": "Coffee"}]
    )
    with pytest.raises(ValueError, match="not found"):
        await ingest(df, internal_account="NonExistent", importer_name="test")
