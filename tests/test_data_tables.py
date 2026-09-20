"""Tests for the read-only Tabulator endpoints backing the /data tables.

Covers external accounts, import history, and importer discovery. These
endpoints share Tabulator's default remote envelope
(``last_page``/``last_row``/``data``).
"""

from datetime import date, datetime

import pytest

from pipances.models import Account, Import, Transaction


@pytest.fixture
async def seed_external_accounts(session, seed_accounts, seed_import):
    """Three external accounts with 2, 1, and 0 transactions respectively."""
    checking = seed_accounts["Checking"]
    alpha = Account(name="Alpha Market", kind="external")
    beta = Account(name="Beta Cafe", kind="external")
    gamma = Account(name="Gamma Gas", kind="external")
    session.add_all([alpha, beta, gamma])
    await session.commit()
    for account in (alpha, beta, gamma):
        await session.refresh(account)

    session.add_all(
        [
            Transaction(
                import_id=seed_import.id,
                internal_id=checking.id,
                external_id=alpha.id,
                raw_description="ALPHA 1",
                date=date(2026, 1, 1),
                amount_cents=-100,
                status="approved",
            ),
            Transaction(
                import_id=seed_import.id,
                internal_id=checking.id,
                external_id=alpha.id,
                raw_description="ALPHA 2",
                date=date(2026, 1, 2),
                amount_cents=-200,
                status="approved",
            ),
            Transaction(
                import_id=seed_import.id,
                internal_id=checking.id,
                external_id=beta.id,
                raw_description="BETA 1",
                date=date(2026, 1, 3),
                amount_cents=-300,
                status="approved",
            ),
        ]
    )
    await session.commit()
    return {"alpha": alpha, "beta": beta, "gamma": gamma}


async def _post_external(client, **body):
    return await client.post(
        "/api/external-accounts/table", json={"page": 1, "size": 25, **body}
    )


async def test_external_accounts_table_envelope(client, seed_external_accounts):
    resp = await _post_external(client)
    assert resp.status_code == 200
    body = resp.json()
    assert set(body) == {"last_page", "last_row", "data"}
    assert body["last_row"] == 3
    counts = {row["name"]: row["txn_count"] for row in body["data"]}
    assert counts == {"Alpha Market": 2, "Beta Cafe": 1, "Gamma Gas": 0}


async def test_external_accounts_default_sort_is_name_asc(
    client, seed_external_accounts
):
    resp = await _post_external(client)
    names = [row["name"] for row in resp.json()["data"]]
    assert names == sorted(names)


async def test_external_accounts_sort_by_txn_count_desc(client, seed_external_accounts):
    resp = await _post_external(client, sort=[{"field": "txn_count", "dir": "desc"}])
    counts = [row["txn_count"] for row in resp.json()["data"]]
    assert counts == sorted(counts, reverse=True)


async def test_external_accounts_name_filter(client, seed_external_accounts):
    resp = await _post_external(
        client, filter=[{"field": "name", "type": "like", "value": "market"}]
    )
    body = resp.json()
    assert body["last_row"] == 1
    assert body["data"][0]["name"] == "Alpha Market"


async def test_external_accounts_pagination(client, seed_external_accounts):
    resp = await client.post(
        "/api/external-accounts/table",
        json={"page": 2, "size": 2, "sort": [], "filter": []},
    )
    body = resp.json()
    assert body["last_page"] == 2
    assert body["last_row"] == 3
    assert len(body["data"]) == 1


async def test_external_accounts_unknown_field_ignored(client, seed_external_accounts):
    resp = await _post_external(
        client,
        sort=[{"field": "evil; DROP TABLE", "dir": "asc"}],
        filter=[{"field": "nope", "type": "like", "value": "x"}],
    )
    assert resp.status_code == 200
    assert resp.json()["last_row"] == 3


@pytest.fixture
async def seed_imports(session, seed_import):
    """Three imports with distinct institutions and nullable fields."""
    seed_import.imported_at = datetime(2026, 2, 1, 9, 30)
    session.add_all(
        [
            Import(
                institution="Second Bank",
                filename="second.csv",
                imported_at=datetime(2026, 3, 1, 12, 0),
                row_count=42,
            ),
            Import(
                institution="Third Bank",
                filename=None,
                imported_at=datetime(2026, 1, 1, 8, 15),
                row_count=None,
            ),
        ]
    )
    await session.commit()
    return seed_import


async def _post_imports(client, **body):
    return await client.post("/api/imports/table", json={"page": 1, "size": 25, **body})


async def test_imports_table_envelope_and_format(client, seed_imports):
    resp = await _post_imports(client)
    assert resp.status_code == 200
    body = resp.json()
    assert body["last_row"] == 3
    # Default sort is imported_at DESC, so the newest import comes first.
    first = body["data"][0]
    assert first["institution"] == "Second Bank"
    assert first["imported_at"] == "2026-03-01 12:00"


async def test_imports_filter_by_institution(client, seed_imports):
    resp = await _post_imports(
        client, filter=[{"field": "institution", "type": "like", "value": "third"}]
    )
    body = resp.json()
    assert body["last_row"] == 1
    row = body["data"][0]
    assert row["institution"] == "Third Bank"
    assert row["filename"] is None
    assert row["row_count"] is None


async def test_imports_sort_by_row_count_desc(client, seed_imports):
    resp = await _post_imports(client, sort=[{"field": "row_count", "dir": "desc"}])
    rows = [row["row_count"] for row in resp.json()["data"]]
    # 42 > 0 > NULL when descending.
    assert rows == [42, 0, None]


async def test_imports_pagination(client, seed_imports):
    resp = await client.post(
        "/api/imports/table", json={"page": 2, "size": 2, "sort": [], "filter": []}
    )
    body = resp.json()
    assert body["last_page"] == 2
    assert body["last_row"] == 3
    assert len(body["data"]) == 1


async def test_importers_api(client, seed_accounts):
    resp = await client.get("/api/importers")
    assert resp.status_code == 200
    items = resp.json()
    assert "example.py" in {item["filename"] for item in items}
    assert "Example Bank" in {item["name"] for item in items}
