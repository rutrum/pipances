"""Tests for the Import page: auto-detection, preview, commit, manual entry, tabs."""

from __future__ import annotations

import json
import re
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

import polars as pl
from sqlalchemy import func, select

from pipances.ingest import discover_importers, preview_dedup, try_all_importers
from pipances.models import Import, Importer, Transaction
from pipances.schemas import ImportedTransaction

if TYPE_CHECKING:
    import patito as pt


def _extract_preview_rows(resp) -> list[dict]:
    """Pull the JSON payload out of the preview table's data attribute."""
    match = re.search(r"data-rows='(.*?)'", resp.text, re.DOTALL)
    assert match, "preview data attribute not found"
    return json.loads(match.group(1))


# === Helper ===


VALID_CSV = (
    b"date,amount,description\n2026-01-15,19.99,Coffee\n2026-01-16,-45.67,Refund\n"
)
GARBAGE_CSV = b"this is not a csv at all\x00\x01\x02"

SIMPLE_IMPORTER_SQL = (
    "SELECT CAST(date AS DATE) AS date, "
    "CAST(amount AS DECIMAL(38,2)) AS amount, "
    "CAST(description AS VARCHAR) AS description FROM raw"
)


def _make_df(rows: list[dict]) -> pt.DataFrame[ImportedTransaction]:  # type: ignore[name-defined]
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


def _extract_token(resp) -> str:
    token_match = re.search(r'name="token"\s+value="([^"]+)"', resp.text)
    assert token_match, "Token not found in preview response"
    return token_match.group(1)


async def _preview(client, blob: bytes = VALID_CSV):
    return await client.post(
        "/import/preview",
        files={"file": ("test.csv", blob, "text/csv")},
    )


# === 8. Unit Tests: Auto-Detection and Preview ===


async def test_discover_importers_keyed_by_id(database, session, seed_importers):
    importers = await discover_importers(database)
    assert set(importers) == {imp.id for imp in seed_importers.values()}
    example = importers[seed_importers["Example Bank"].id]
    assert example.name == "Example Bank"
    assert "FROM raw" in example.sql


async def test_try_all_importers_detection_per_id(database, session, seed_importers):
    results = await try_all_importers(database, VALID_CSV)
    example_id = seed_importers["Example Bank"].id
    metro_id = seed_importers["Metro Credit Union"].id

    assert set(results) == {example_id, metro_id}

    assert results[example_id]["success"] is True
    assert results[example_id]["name"] == "Example Bank"
    assert results[example_id]["df"].height == 2

    assert results[metro_id]["success"] is False
    assert results[metro_id]["name"] == "Metro Credit Union"
    assert results[metro_id]["error"]


async def test_try_all_importers_metro_detects_its_format(
    database, session, seed_importers
):
    metro_csv = (
        b"Transaction Date,Debit,Credit,Memo\n"
        b"02/15/2026,,2800.00,EMPLOYER DIRECT DEP\n"
        b"02/16/2026,87.43,,KROGER #1234\n"
    )
    results = await try_all_importers(database, metro_csv)
    example_id = seed_importers["Example Bank"].id
    metro_id = seed_importers["Metro Credit Union"].id

    assert results[metro_id]["success"] is True
    assert results[metro_id]["df"].height == 2
    assert results[example_id]["success"] is False


async def test_try_all_importers_garbage(database, session, seed_importers):
    results = await try_all_importers(database, GARBAGE_CSV)
    assert results
    assert all(not value["success"] for value in results.values())


async def test_try_all_importers_no_importers(database, session):
    results = await try_all_importers(database, VALID_CSV)
    assert results == {}


async def test_preview_dedup_flags_existing(database, session, seed_accounts):
    from pipances.ingest import ingest

    df = _make_df(
        [{"date": date(2026, 1, 15), "amount": 19.99, "description": "Coffee"}]
    )
    await ingest(database, df, internal_account="Checking", importer_name="test")

    flags = await preview_dedup(database, df, "Checking")
    assert flags == [True]


async def test_preview_dedup_no_dupes_empty_db(database, session, seed_accounts):
    df = _make_df(
        [{"date": date(2026, 1, 15), "amount": 19.99, "description": "Coffee"}]
    )
    flags = await preview_dedup(database, df, "Checking")
    assert flags == [False]


async def test_preview_dedup_same_file_dupes_not_flagged(
    database, session, seed_accounts
):
    df = _make_df(
        [
            {"date": date(2026, 1, 15), "amount": 5.00, "description": "Coffee"},
            {"date": date(2026, 1, 15), "amount": 5.00, "description": "Coffee"},
        ]
    )
    flags = await preview_dedup(database, df, "Checking")
    assert flags == [False, False]


# === 9. Integration Tests: CSV Preview and Commit ===


async def test_preview_valid_csv_returns_200(
    client, session, seed_accounts, seed_importers
):
    resp = await _preview(client)
    assert resp.status_code == 200
    assert "Coffee" in resp.text
    assert "Refund" in resp.text
    assert 'name="token"' in resp.text
    assert "data-preview-table" in resp.text
    assert "import-preview-table.js" in resp.text

    rows = _extract_preview_rows(resp)
    assert len(rows) == 2
    assert rows[0] == {
        "date": "2026-01-15",
        "amount_cents": 1999,
        "description": "Coffee",
        "duplicate": False,
    }
    assert rows[1]["amount_cents"] == -4567
    assert rows[1]["duplicate"] is False


async def test_preview_auto_selects_single_success(
    client, session, seed_accounts, seed_importers
):
    resp = await _preview(client)
    assert resp.status_code == 200

    example_id = seed_importers["Example Bank"].id
    # The sole success is preselected by id.
    assert f'name="importer" value="{example_id}"' in resp.text
    assert "Example Bank" in resp.text
    # The failing importer still appears as a ghost badge.
    assert "Metro Credit Union" in resp.text
    # No picker when there is exactly one success.
    assert '<select name="importer"' not in resp.text


async def test_preview_lists_multiple_successes(
    client, session, seed_accounts, seed_importers
):
    other = Importer(name="Second Bank", sql=SIMPLE_IMPORTER_SQL)
    session.add(other)
    await session.commit()
    await session.refresh(other)

    resp = await _preview(client)
    assert resp.status_code == 200
    # Every successful importer is listed; the failing one is shown dimmed.
    assert 'badge-success gap-1 mr-2">Example Bank' in resp.text
    assert 'badge-success gap-1 mr-2">Second Bank' in resp.text
    assert 'badge-ghost gap-1 mr-2">Metro Credit Union' in resp.text


async def test_preview_valid_csv_creates_temp_file(
    client, session, seed_accounts, seed_importers
):
    resp = await _preview(client)
    assert resp.status_code == 200

    from pipances.settings import settings

    token = _extract_token(resp)
    assert (settings.temp_dir / f"import_{token}.csv").exists()


async def test_preview_unparseable_csv_returns_error(
    client, session, seed_accounts, seed_importers
):
    resp = await _preview(client, GARBAGE_CSV)
    assert resp.status_code == 422
    assert "alert" in resp.text
    assert "could parse this file" in resp.text


async def test_preview_empty_configuration_message(client, seed_accounts):
    resp = await _preview(client)
    assert resp.status_code == 422
    assert "No importers are configured" in resp.text
    assert "could parse this file" not in resp.text


async def test_commit_valid_flow(client, session, seed_accounts, seed_importers):
    resp = await _preview(client)
    assert resp.status_code == 200
    token = _extract_token(resp)

    example_id = seed_importers["Example Bank"].id
    resp = await client.post(
        "/import/commit",
        data={"token": token, "importer": str(example_id), "account": "Checking"},
    )
    assert resp.status_code == 200
    assert "HX-Redirect" in resp.headers

    count = await session.scalar(select(func.count()).select_from(Transaction))
    assert count == 2


async def test_commit_populates_importer_provenance(
    client, session, seed_accounts, seed_importers
):
    resp = await _preview(client)
    token = _extract_token(resp)

    example = seed_importers["Example Bank"]
    resp = await client.post(
        "/import/commit",
        data={"token": token, "importer": str(example.id), "account": "Checking"},
    )
    assert resp.status_code == 200

    imp = await session.scalar(select(Import))
    assert imp is not None
    assert imp.importer_id == example.id
    assert imp.importer_name == "Example Bank"
    assert imp.importer_sql == example.sql
    assert imp.institution == "Example Bank"


async def test_commit_unknown_importer_id(
    client, session, seed_accounts, seed_importers
):
    resp = await _preview(client)
    token = _extract_token(resp)

    resp = await client.post(
        "/import/commit",
        data={"token": token, "importer": "99999", "account": "Checking"},
    )
    assert resp.status_code == 422
    assert "Unknown importer" in resp.text


async def test_commit_invalid_token(client, seed_accounts, seed_importers):
    example_id = seed_importers["Example Bank"].id
    resp = await client.post(
        "/import/commit",
        data={
            "token": "nonexistent",
            "importer": str(example_id),
            "account": "Checking",
        },
    )
    assert resp.status_code == 422
    assert "expired" in resp.text.lower()


async def test_commit_nonexistent_account(
    client, session, seed_accounts, seed_importers
):
    resp = await _preview(client)
    token = _extract_token(resp)

    example_id = seed_importers["Example Bank"].id
    resp = await client.post(
        "/import/commit",
        data={"token": token, "importer": str(example_id), "account": "NoSuchAccount"},
    )
    assert resp.status_code == 422
    assert "not found" in resp.text.lower()


async def test_dedup_endpoint_flags_duplicates(
    client, database, session, seed_accounts, seed_importers
):
    from pipances.ingest import ingest

    # First ingest the data so it's in the DB
    df = _make_df(
        [{"date": date(2026, 1, 15), "amount": 19.99, "description": "Coffee"}]
    )
    await ingest(database, df, internal_account="Checking", importer_name="test")

    # Preview the same data
    csv_data = b"date,amount,description\n2026-01-15,19.99,Coffee\n"
    resp = await _preview(client, csv_data)
    token = _extract_token(resp)

    # Call dedup endpoint with account
    example_id = seed_importers["Example Bank"].id
    resp = await client.post(
        "/import/preview/dedup",
        data={"token": token, "importer": str(example_id), "account": "Checking"},
    )
    assert resp.status_code == 200

    # The strike-through is applied client-side by Tabulator's rowFormatter, so
    # the server flags the duplicate in the JSON payload instead.
    rows = _extract_preview_rows(resp)
    assert len(rows) == 1
    assert rows[0]["duplicate"] is True
    assert "0 new" in resp.text
    assert "1 duplicate" in resp.text


# === 10. Integration Tests: Manual Entry ===


async def test_manual_valid_submission(client, session, seed_accounts):
    resp = await client.post(
        "/import/manual",
        data={
            "account": "Checking",
            "date[]": ["2026-03-01", "2026-03-02"],
            "amount[]": ["-50.00", "-12.00"],
            "description[]": ["Groceries", "Coffee"],
        },
    )
    assert resp.status_code == 200
    assert "HX-Redirect" in resp.headers

    # Check Import record
    imp = await session.scalar(select(Import).where(Import.institution == "Manual"))
    assert imp is not None
    assert imp.row_count == 2
    # Manual entry leaves importer provenance NULL.
    assert imp.importer_id is None
    assert imp.importer_name is None
    assert imp.importer_sql is None

    # Check transactions
    count = await session.scalar(select(func.count()).select_from(Transaction))
    assert count == 2


async def test_manual_mixed_empty_rows(client, session, seed_accounts):
    resp = await client.post(
        "/import/manual",
        data={
            "account": "Checking",
            "date[]": ["2026-03-01", "", "2026-03-03"],
            "amount[]": ["-50.00", "", "-15.00"],
            "description[]": ["Groceries", "", "Dinner"],
        },
    )
    assert resp.status_code == 200
    assert "HX-Redirect" in resp.headers

    count = await session.scalar(select(func.count()).select_from(Transaction))
    assert count == 2


async def test_manual_all_empty_rows(client, session, seed_accounts):
    resp = await client.post(
        "/import/manual",
        data={
            "account": "Checking",
            "date[]": ["", ""],
            "amount[]": ["", ""],
            "description[]": ["", ""],
        },
    )
    assert resp.status_code == 422
    assert "No transactions" in resp.text

    count = await session.scalar(select(func.count()).select_from(Import))
    assert count == 0


async def test_manual_no_account(client, seed_accounts):
    resp = await client.post(
        "/import/manual",
        data={
            "account": "",
            "date[]": ["2026-03-01"],
            "amount[]": ["-50.00"],
            "description[]": ["Groceries"],
        },
    )
    assert resp.status_code == 422


async def test_manual_partial_returns_form(client, seed_accounts):
    resp = await client.get("/import/manual")
    assert resp.status_code == 200
    assert "account" in resp.text
    assert "date[]" in resp.text


# === 11. Integration Tests: Tab Navigation ===


async def test_import_full_page_has_csv_tab(client, seed_accounts):
    resp = await client.get("/import")
    assert resp.status_code == 200
    assert "CSV Upload" in resp.text
    assert "Manual Entry" in resp.text
    assert 'name="file"' in resp.text


async def test_import_csv_partial_no_html_tag(client, seed_accounts):
    resp = await client.get("/import/csv", headers={"HX-Request": "true"})
    assert resp.status_code == 200
    assert "<html" not in resp.text


async def test_import_manual_partial_no_html_tag(client, seed_accounts):
    resp = await client.get("/import/manual", headers={"HX-Request": "true"})
    assert resp.status_code == 200
    assert "<html" not in resp.text
