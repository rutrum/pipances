"""Tests for the inline-editing endpoints backing /data/categories and /data/accounts.

Each editable table returns rows in the same shape from both its table endpoint
and its PATCH endpoint, so Tabulator can reconcile a row after an edit.
"""

from datetime import date

import pytest

from pipances.models import Account, Transaction


async def _post_table(client, path, **body):
    return await client.post(path, json={"page": 1, "size": 25, **body})


# === Categories ===


@pytest.fixture
async def seed_category_with_txn(session, seed_accounts, seed_categories, seed_import):
    checking = seed_accounts["Checking"]
    groceries = seed_categories["Groceries"]
    session.add(
        Transaction(
            import_id=seed_import.id,
            internal_id=checking.id,
            raw_description="MARKET",
            date=date(2026, 1, 15),
            amount_cents=-1000,
            status="approved",
            category_id=groceries.id,
        )
    )
    await session.commit()
    return groceries


async def test_categories_table_envelope(client, seed_categories):
    resp = await _post_table(client, "/api/categories/table")
    assert resp.status_code == 200
    body = resp.json()
    assert body["last_row"] == 3
    assert {"id", "name", "txn_count"} <= set(body["data"][0])


async def test_categories_table_txn_count(client, seed_category_with_txn):
    resp = await _post_table(client, "/api/categories/table")
    groceries = next(row for row in resp.json()["data"] if row["name"] == "Groceries")
    assert groceries["txn_count"] == 1


async def test_category_rename_returns_row_with_count(client, seed_category_with_txn):
    resp = await client.patch(
        f"/api/categories/{seed_category_with_txn.id}",
        json={"name": "Food & Drink"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "Food & Drink"
    assert body["txn_count"] == 1


async def test_category_rename_duplicate_is_rejected(client, seed_categories):
    dining = seed_categories["Dining"]
    resp = await client.patch(
        f"/api/categories/{dining.id}", json={"name": "Groceries"}
    )
    assert resp.status_code == 422
    assert "already exists" in resp.json()["detail"]


async def test_category_rename_empty_is_rejected(client, seed_categories):
    dining = seed_categories["Dining"]
    resp = await client.patch(f"/api/categories/{dining.id}", json={"name": "   "})
    assert resp.status_code == 422


async def test_category_rename_missing_is_404(client, seed_categories):
    resp = await client.patch("/api/categories/99999", json={"name": "Nope"})
    assert resp.status_code == 404


# === Accounts ===


@pytest.fixture
async def seed_account_states(session, seed_accounts):
    """Mark one account closed and add an external account (which must be hidden)."""
    closed = seed_accounts["Credit Card"]
    closed.active = False
    session.add(Account(name="Some Merchant", kind="external"))
    await session.commit()
    return seed_accounts


async def test_accounts_table_excludes_closed_by_default(client, seed_account_states):
    resp = await _post_table(client, "/api/accounts/table")
    body = resp.json()
    assert body["last_row"] == 2
    names = {row["name"] for row in body["data"]}
    assert names == {"Checking", "Savings"}


async def test_accounts_table_show_closed_includes_inactive(
    client, seed_account_states
):
    resp = await _post_table(client, "/api/accounts/table", show_closed=True)
    body = resp.json()
    assert body["last_row"] == 3
    assert "Credit Card" in {row["name"] for row in body["data"]}
    # External accounts never appear in this table.
    assert "Some Merchant" not in {row["name"] for row in body["data"]}


async def test_account_row_shape(client, seed_accounts):
    resp = await _post_table(client, "/api/accounts/table")
    row = resp.json()["data"][0]
    assert set(row) == {
        "id",
        "name",
        "kind",
        "starting_balance",
        "balance_date",
        "active",
    }


async def test_account_patch_fields(client, seed_accounts):
    checking = seed_accounts["Checking"]
    resp = await client.patch(
        f"/api/accounts/{checking.id}",
        json={
            "name": "Main Checking",
            "kind": "savings",
            "starting_balance": 123.45,
            "balance_date": "2026-01-15",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "Main Checking"
    assert body["kind"] == "savings"
    assert body["starting_balance"] == pytest.approx(123.45)
    assert body["balance_date"] == "2026-01-15"


async def test_account_patch_can_clear_balance_date(client, seed_accounts):
    checking = seed_accounts["Checking"]
    await client.patch(
        f"/api/accounts/{checking.id}", json={"balance_date": "2026-01-01"}
    )
    resp = await client.patch(
        f"/api/accounts/{checking.id}", json={"balance_date": None}
    )
    assert resp.json()["balance_date"] is None


async def test_account_patch_invalid_kind_rejected(client, seed_accounts):
    checking = seed_accounts["Checking"]
    resp = await client.patch(f"/api/accounts/{checking.id}", json={"kind": "external"})
    assert resp.status_code == 422


async def test_account_patch_duplicate_name_rejected(client, seed_accounts):
    checking = seed_accounts["Checking"]
    resp = await client.patch(f"/api/accounts/{checking.id}", json={"name": "Savings"})
    assert resp.status_code == 422


async def test_account_create(client, seed_accounts):
    resp = await client.post(
        "/api/accounts",
        json={
            "name": "Brokerage",
            "kind": "savings",
            "starting_balance": 500,
            "balance_date": "2026-02-01",
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Brokerage"
    assert body["active"] is True
    assert body["starting_balance"] == pytest.approx(500)

    table = await _post_table(client, "/api/accounts/table")
    assert "Brokerage" in {row["name"] for row in table.json()["data"]}


async def test_account_create_invalid_kind_rejected(client, seed_accounts):
    resp = await client.post("/api/accounts", json={"name": "Bad", "kind": "external"})
    assert resp.status_code == 422


async def test_account_create_duplicate_rejected(client, seed_accounts):
    resp = await client.post(
        "/api/accounts", json={"name": "Checking", "kind": "checking"}
    )
    assert resp.status_code == 422


async def test_account_close_and_reopen(client, seed_accounts):
    checking = seed_accounts["Checking"]

    closed = await client.patch(f"/api/accounts/{checking.id}", json={"active": False})
    assert closed.json()["active"] is False

    included = await _post_table(client, "/api/accounts/table", show_closed=True)
    assert checking.id in {row["id"] for row in included.json()["data"]}

    reopened = await client.patch(f"/api/accounts/{checking.id}", json={"active": True})
    assert reopened.json()["active"] is True
