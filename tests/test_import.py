"""Tests for the Import page: auto-detection, preview, commit, manual entry, tabs."""

from datetime import date
from decimal import Decimal

import polars as pl
from sqlalchemy import func, select

from pipances.ingest import preview_dedup, try_all_importers
from pipances.models import Import, Transaction

# === Helper ===


VALID_CSV = (
    b"date,amount,description\n2026-01-15,19.99,Coffee\n2026-01-16,-45.67,Refund\n"
)
GARBAGE_CSV = b"this is not a csv at all\x00\x01\x02"


def _make_df(rows: list[dict]) -> pl.DataFrame:
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


# === 8. Unit Tests: Auto-Detection and Preview ===


def test_try_all_importers_valid_csv():
    results = try_all_importers(VALID_CSV)
    successes = {k: v for k, v in results.items() if v["success"]}
    assert len(successes) >= 1
    assert "example" in successes
    assert successes["example"]["name"] == "Example Bank"
    assert successes["example"]["df"] is not None


def test_try_all_importers_garbage():
    results = try_all_importers(GARBAGE_CSV)
    successes = {k: v for k, v in results.items() if v["success"]}
    assert len(successes) == 0


async def test_preview_dedup_flags_existing(session, seed_accounts):
    from pipances.ingest import ingest

    df = _make_df(
        [{"date": date(2026, 1, 15), "amount": 19.99, "description": "Coffee"}]
    )
    await ingest(df, internal_account="Checking", importer_name="test")

    flags = await preview_dedup(df, "Checking")
    assert flags == [True]


async def test_preview_dedup_no_dupes_empty_db(session, seed_accounts):
    df = _make_df(
        [{"date": date(2026, 1, 15), "amount": 19.99, "description": "Coffee"}]
    )
    flags = await preview_dedup(df, "Checking")
    assert flags == [False]


async def test_preview_dedup_same_file_dupes_not_flagged(session, seed_accounts):
    df = _make_df(
        [
            {"date": date(2026, 1, 15), "amount": 5.00, "description": "Coffee"},
            {"date": date(2026, 1, 15), "amount": 5.00, "description": "Coffee"},
        ]
    )
    flags = await preview_dedup(df, "Checking")
    assert flags == [False, False]


# === 9. Integration Tests: CSV Preview and Commit ===


async def test_preview_valid_csv_returns_200(client, seed_accounts):
    resp = await client.post(
        "/import/preview",
        files={"file": ("test.csv", VALID_CSV, "text/csv")},
    )
    assert resp.status_code == 200
    assert "Coffee" in resp.text
    assert "Refund" in resp.text
    assert 'name="token"' in resp.text


async def test_preview_valid_csv_creates_temp_file(client, seed_accounts):
    resp = await client.post(
        "/import/preview",
        files={"file": ("test.csv", VALID_CSV, "text/csv")},
    )
    assert resp.status_code == 200

    # Extract token and verify the temp file exists
    import re

    from pipances.routes.import_page import TEMP_DIR

    token_match = re.search(r'name="token"\s+value="([^"]+)"', resp.text)
    assert token_match
    token = token_match.group(1)
    assert (TEMP_DIR / f"import_{token}.csv").exists()


async def test_preview_unparseable_csv_returns_error(client, seed_accounts):
    resp = await client.post(
        "/import/preview",
        files={"file": ("test.csv", GARBAGE_CSV, "text/csv")},
    )
    assert resp.status_code == 422
    assert "alert" in resp.text


async def test_commit_valid_flow(client, session, seed_accounts):
    # First preview to get a token
    resp = await client.post(
        "/import/preview",
        files={"file": ("test.csv", VALID_CSV, "text/csv")},
    )
    assert resp.status_code == 200

    # Extract token from response
    import re

    token_match = re.search(r'name="token"\s+value="([^"]+)"', resp.text)
    assert token_match, "Token not found in preview response"
    token = token_match.group(1)

    resp = await client.post(
        "/import/commit",
        data={"token": token, "importer": "example", "account": "Checking"},
    )
    assert resp.status_code == 200
    assert "HX-Redirect" in resp.headers

    # Verify transactions were inserted
    count = await session.scalar(select(func.count()).select_from(Transaction))
    assert count == 2


async def test_commit_invalid_token(client, seed_accounts):
    resp = await client.post(
        "/import/commit",
        data={"token": "nonexistent", "importer": "example", "account": "Checking"},
    )
    assert resp.status_code == 422
    assert "expired" in resp.text.lower()


async def test_commit_nonexistent_account(client, seed_accounts):
    # Preview to get a token
    resp = await client.post(
        "/import/preview",
        files={"file": ("test.csv", VALID_CSV, "text/csv")},
    )
    import re

    token_match = re.search(r'name="token"\s+value="([^"]+)"', resp.text)
    token = token_match.group(1)

    resp = await client.post(
        "/import/commit",
        data={"token": token, "importer": "example", "account": "NoSuchAccount"},
    )
    assert resp.status_code == 422
    assert "not found" in resp.text.lower()


async def test_dedup_endpoint_shows_strikethrough(client, session, seed_accounts):
    from pipances.ingest import ingest

    # First ingest the data so it's in the DB
    df = _make_df(
        [{"date": date(2026, 1, 15), "amount": 19.99, "description": "Coffee"}]
    )
    await ingest(df, internal_account="Checking", importer_name="test")

    # Preview the same data
    csv_data = b"date,amount,description\n2026-01-15,19.99,Coffee\n"
    resp = await client.post(
        "/import/preview",
        files={"file": ("test.csv", csv_data, "text/csv")},
    )
    import re

    token_match = re.search(r'name="token"\s+value="([^"]+)"', resp.text)
    token = token_match.group(1)

    # Call dedup endpoint with account
    resp = await client.post(
        "/import/preview/dedup",
        data={"token": token, "importer": "example", "account": "Checking"},
    )
    assert resp.status_code == 200
    assert "line-through" in resp.text


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
