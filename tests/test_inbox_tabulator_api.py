"""Tests for the Tabulator-based inbox API and page.

Phase 1 covers the read-only remote table endpoint backing /inbox-tabulator.
"""

from datetime import date

import pytest

from pipances.models import Account, Transaction, TransactionSplit


@pytest.fixture
async def seed_pending(session, seed_accounts, seed_import, seed_categories):
    """Three pending transactions (one with a split) and one approved."""
    checking = seed_accounts["Checking"]
    external = Account(name="Kroger", kind="external")
    session.add(external)
    await session.commit()
    await session.refresh(external)

    categorized = Transaction(
        import_id=seed_import.id,
        internal_id=checking.id,
        external_id=external.id,
        raw_description="KROGER STORE #1",
        description="Groceries run",
        category_id=seed_categories["Groceries"].id,
        ml_confidence_description=0.9,
        ml_confidence_category=0.8,
        date=date(2026, 9, 1),
        amount_cents=-1000,
        status="pending",
    )
    split_txn = Transaction(
        import_id=seed_import.id,
        internal_id=checking.id,
        external_id=external.id,
        raw_description="KROGER STORE #2",
        description="Split run",
        category_id=seed_categories["Groceries"].id,
        date=date(2026, 9, 2),
        amount_cents=-2000,
        status="pending",
    )
    bare_txn = Transaction(
        import_id=seed_import.id,
        internal_id=checking.id,
        external_id=None,
        raw_description="UNKNOWN RETAIL STORE",
        description=None,
        category_id=None,
        date=date(2026, 9, 3),
        amount_cents=-3000,
        status="pending",
    )
    approved_txn = Transaction(
        import_id=seed_import.id,
        internal_id=checking.id,
        external_id=external.id,
        raw_description="APPROVED ROW",
        description="Already done",
        date=date(2026, 8, 1),
        amount_cents=-500,
        status="approved",
    )
    session.add_all([categorized, split_txn, bare_txn, approved_txn])
    await session.commit()
    for txn in (categorized, split_txn, bare_txn, approved_txn):
        await session.refresh(txn)

    session.add(
        TransactionSplit(
            transaction_id=split_txn.id,
            category_id=seed_categories["Dining"].id,
            amount_cents=500,
        )
    )
    await session.commit()
    return {
        "categorized": categorized,
        "split": split_txn,
        "bare": bare_txn,
        "approved": approved_txn,
    }


async def _post_table(client, **body):
    return await client.post("/api/inbox/table", json={"page": 1, "size": 25, **body})


async def test_inbox_table_envelope(client, seed_pending):
    resp = await _post_table(client)
    assert resp.status_code == 200
    body = resp.json()
    assert set(body) == {"last_page", "last_row", "data"}
    assert body["last_row"] == 3
    assert len(body["data"]) == 3


async def test_inbox_table_only_pending(client, seed_pending):
    body = (await _post_table(client)).json()
    assert {row["status"] for row in body["data"]} == {"pending"}
    assert seed_pending["approved"].id not in {row["id"] for row in body["data"]}


async def test_inbox_table_row_fields(client, seed_pending):
    body = (await _post_table(client)).json()
    by_id = {row["id"]: row for row in body["data"]}

    categorized = by_id[seed_pending["categorized"].id]
    assert categorized["can_approve"] is True
    assert categorized["category_id"] == seed_pending["categorized"].category_id
    assert categorized["external_id"] == seed_pending["categorized"].external_id
    assert categorized["split_count"] == 0
    assert categorized["category"]["name"] == "Groceries"
    assert categorized["external_account"]["name"] == "Kroger"

    bare = by_id[seed_pending["bare"].id]
    assert bare["can_approve"] is False
    assert bare["category_id"] is None
    assert bare["external_id"] is None
    assert bare["category"] is None
    assert bare["external_account"] is None
    assert bare["split_count"] == 0

    split = by_id[seed_pending["split"].id]
    assert split["split_count"] == 1


async def test_inbox_table_split_count_and_ml_confidence(client, seed_pending):
    body = (await _post_table(client)).json()
    split = next(r for r in body["data"] if r["id"] == seed_pending["split"].id)
    assert split["split_count"] == 1
    assert split["ml_confidence"] is None


async def test_inbox_table_sort_by_amount_desc(client, seed_pending):
    resp = await _post_table(client, sort=[{"field": "amount", "dir": "desc"}])
    amounts = [row["amount_cents"] for row in resp.json()["data"]]
    assert amounts == sorted(amounts, reverse=True)
    assert amounts == [-1000, -2000, -3000]


async def test_inbox_table_sort_by_date_asc(client, seed_pending):
    resp = await _post_table(client, sort=[{"field": "date", "dir": "asc"}])
    dates = [row["date"] for row in resp.json()["data"]]
    assert dates == sorted(dates)
    assert dates == ["2026-09-01", "2026-09-02", "2026-09-03"]


async def test_inbox_table_unknown_sort_field_ignored(client, seed_pending):
    resp = await _post_table(client, sort=[{"field": "evil; DROP TABLE", "dir": "asc"}])
    assert resp.status_code == 200
    assert resp.json()["last_row"] == 3


async def test_inbox_table_pagination(client, seed_pending):
    resp = await client.post(
        "/api/inbox/table", json={"page": 2, "size": 2, "sort": [], "filter": []}
    )
    body = resp.json()
    assert body["last_page"] == 2
    assert body["last_row"] == 3
    assert len(body["data"]) == 1


async def test_inbox_table_page_out_of_range_clamped(client, seed_pending):
    resp = await _post_table(client, page=99, size=2)
    body = resp.json()
    assert resp.status_code == 200
    assert len(body["data"]) == 1


async def test_inbox_tabulator_page_renders(client, seed_pending):
    resp = await client.get("/inbox-tabulator")
    assert resp.status_code == 200
    assert 'id="inbox-tabulator-root"' in resp.text
    assert 'id="inbox-tabulator"' in resp.text
    assert "inbox-tabulator.js" in resp.text


async def test_patch_description_updates_and_clears_ml_confidence(client, seed_pending):
    txn_id = seed_pending["categorized"].id
    resp = await client.patch(
        f"/api/inbox/transactions/{txn_id}", json={"description": "Renamed"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["description"] == "Renamed"
    assert (body["ml_confidence"] or {}).get("description") is None
    # Editing the description must not touch the category suggestion.
    assert (body["ml_confidence"] or {}).get("category") == 0.8


async def test_patch_category_by_id(client, seed_pending, seed_categories):
    txn_id = seed_pending["categorized"].id
    dining_id = seed_categories["Dining"].id
    resp = await client.patch(
        f"/api/inbox/transactions/{txn_id}", json={"category_id": dining_id}
    )
    body = resp.json()
    assert body["category"]["id"] == dining_id
    assert body["category"]["name"] == "Dining"
    assert (body["ml_confidence"] or {}).get("category") is None


async def test_patch_category_by_existing_name_is_case_insensitive(
    client, seed_pending
):
    txn_id = seed_pending["categorized"].id
    resp = await client.patch(
        f"/api/inbox/transactions/{txn_id}", json={"category_id": "dining"}
    )
    assert resp.json()["category"]["name"] == "Dining"


async def test_patch_category_by_new_name_creates(client, seed_pending):
    txn_id = seed_pending["categorized"].id
    resp = await client.patch(
        f"/api/inbox/transactions/{txn_id}", json={"category_id": "Utilities"}
    )
    assert resp.json()["category"]["name"] == "Utilities"


async def test_patch_external_by_new_name_creates(client, seed_pending):
    txn_id = seed_pending["categorized"].id
    resp = await client.patch(
        f"/api/inbox/transactions/{txn_id}", json={"external_id": "New Merchant"}
    )
    body = resp.json()
    assert body["external_account"]["name"] == "New Merchant"
    assert (body["ml_confidence"] or {}).get("external") is None


async def test_patch_empty_strings_clear_fields(client, seed_pending):
    txn_id = seed_pending["categorized"].id
    resp = await client.patch(
        f"/api/inbox/transactions/{txn_id}",
        json={"description": "", "category_id": "", "external_id": ""},
    )
    body = resp.json()
    assert body["description"] is None
    assert body["category"] is None
    assert body["external_account"] is None
    assert body["can_approve"] is False


async def test_patch_only_provided_fields_applied(client, seed_pending):
    txn_id = seed_pending["categorized"].id
    resp = await client.patch(
        f"/api/inbox/transactions/{txn_id}", json={"category_id": "Dining"}
    )
    body = resp.json()
    assert body["description"] == "Groceries run"
    assert body["external_account"]["name"] == "Kroger"


async def test_patch_returns_split_count(client, seed_pending):
    txn_id = seed_pending["split"].id
    resp = await client.patch(
        f"/api/inbox/transactions/{txn_id}", json={"description": "Renamed"}
    )
    assert resp.json()["split_count"] == 1


async def test_patch_unknown_transaction_is_404(client, seed_pending):
    resp = await client.patch(
        "/api/inbox/transactions/999999", json={"description": "x"}
    )
    assert resp.status_code == 404


async def test_patch_approve_requires_description(client, seed_pending):
    txn_id = seed_pending["bare"].id
    resp = await client.patch(
        f"/api/inbox/transactions/{txn_id}", json={"marked_for_approval": True}
    )
    assert resp.status_code == 422
    assert "Description" in resp.json()["detail"]


async def test_patch_approve_requires_external(client, seed_pending):
    txn_id = seed_pending["bare"].id
    await client.patch(
        f"/api/inbox/transactions/{txn_id}", json={"description": "Has a description"}
    )
    resp = await client.patch(
        f"/api/inbox/transactions/{txn_id}", json={"marked_for_approval": True}
    )
    assert resp.status_code == 422
    assert "External" in resp.json()["detail"]


async def test_patch_approve_succeeds_and_toggles(client, seed_pending):
    txn_id = seed_pending["categorized"].id
    resp = await client.patch(
        f"/api/inbox/transactions/{txn_id}", json={"marked_for_approval": True}
    )
    assert resp.status_code == 200
    assert resp.json()["marked_for_approval"] is True

    resp = await client.patch(
        f"/api/inbox/transactions/{txn_id}", json={"marked_for_approval": False}
    )
    assert resp.json()["marked_for_approval"] is False


async def test_patch_approve_alongside_field_updates(client, seed_pending):
    txn_id = seed_pending["bare"].id
    resp = await client.patch(
        f"/api/inbox/transactions/{txn_id}",
        json={
            "description": "Fresh",
            "external_id": "Fresh Merchant",
            "marked_for_approval": True,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["marked_for_approval"] is True
    assert body["description"] == "Fresh"
    assert body["external_account"]["name"] == "Fresh Merchant"


async def test_commit_summary_nothing_marked(client, seed_pending):
    resp = await client.get("/api/inbox/commit-summary")
    assert resp.status_code == 200
    assert resp.json() == {"count": 0, "new_categories": [], "new_externals": []}


async def test_commit_summary_lists_new_entities(client, seed_pending):
    txn_id = seed_pending["bare"].id
    await client.patch(
        f"/api/inbox/transactions/{txn_id}",
        json={
            "description": "Pretty new",
            "category_id": "Brand New Category",
            "external_id": "Brand New Merchant",
            "marked_for_approval": True,
        },
    )
    resp = await client.get("/api/inbox/commit-summary")
    body = resp.json()
    assert body["count"] == 1
    assert body["new_categories"] == ["Brand New Category"]
    assert body["new_externals"] == ["Brand New Merchant"]


async def test_commit_summary_ignores_existing_approved_entities(client, seed_pending):
    # The seed's approved transaction already references Kroger, so it is not
    # listed as new; Groceries is referenced only by pending rows.
    txn_id = seed_pending["categorized"].id
    await client.patch(
        f"/api/inbox/transactions/{txn_id}", json={"marked_for_approval": True}
    )
    body = (await client.get("/api/inbox/commit-summary")).json()
    assert body["count"] == 1
    assert body["new_categories"] == ["Groceries"]
    assert body["new_externals"] == []


async def test_commit_json_approves_and_reports_remaining(client, seed_pending):
    txn_id = seed_pending["categorized"].id
    await client.patch(
        f"/api/inbox/transactions/{txn_id}", json={"marked_for_approval": True}
    )

    resp = await client.post("/api/inbox/commit")
    assert resp.status_code == 200
    assert resp.json() == {"committed": 1, "remaining": 2}

    table = await _post_table(client)
    assert table.json()["last_row"] == 2


async def test_commit_json_nothing_marked(client, seed_pending):
    resp = await client.post("/api/inbox/commit")
    assert resp.json() == {"committed": 0, "remaining": 3}


async def test_commit_prunes_orphan_external(client, session, seed_pending):
    session.add(Account(name="Orphan Only", kind="external"))
    await session.commit()

    txn_id = seed_pending["categorized"].id
    await client.patch(
        f"/api/inbox/transactions/{txn_id}", json={"marked_for_approval": True}
    )
    await client.post("/api/inbox/commit")

    resp = await client.get("/api/external-accounts", params={"q": "Orphan Only"})
    assert resp.json() == []


async def test_page_shows_marked_count(client, seed_pending):
    txn_id = seed_pending["categorized"].id
    await client.patch(
        f"/api/inbox/transactions/{txn_id}", json={"marked_for_approval": True}
    )
    resp = await client.get("/inbox-tabulator")
    assert resp.status_code == 200
    assert 'data-marked-count="1"' in resp.text
