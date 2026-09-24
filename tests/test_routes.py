from datetime import date

import pytest

from pipances.models import Account, Transaction

# === Inbox ===


async def test_inbox_get_200(client, seed_accounts):
    resp = await client.get("/inbox")
    assert resp.status_code == 200


async def test_inbox_tabulator_returns_404(client, seed_accounts):
    """The old /inbox-tabulator path must no longer exist."""
    resp = await client.get("/inbox-tabulator")
    assert resp.status_code == 404


async def test_inbox_toast_renders(client, seed_accounts):
    resp = await client.get(
        "/inbox?toast=upload_success&imported=3&duplicates=1&date_min=2026-01-01&date_max=2026-01-03&account=Checking"
    )
    assert resp.status_code == 200
    assert "Imported 3 transactions" in resp.text
    assert "1 duplicate skipped" in resp.text


async def test_inbox_toast_imported_one(client, seed_accounts):
    resp = await client.get("/inbox?toast=upload_success&imported=1&duplicates=0")
    assert resp.status_code == 200
    assert "Imported 1 transaction" in resp.text


# === Explore ===


@pytest.fixture
async def seed_explore_txns(session, seed_accounts, seed_categories, seed_import):
    """Two regular txns plus a Checking<->Savings transfer pair."""
    checking = seed_accounts["Checking"]
    savings = seed_accounts["Savings"]
    rows = [
        Transaction(
            import_id=seed_import.id,
            internal_id=checking.id,
            external_id=savings.id,
            raw_description="CHECKING TO SAVINGS",
            description="Transfer to savings",
            date=date(2026, 3, 15),
            amount_cents=50000,
            status="approved",
        ),
        Transaction(
            import_id=seed_import.id,
            internal_id=savings.id,
            external_id=checking.id,
            raw_description="SAVINGS FROM CHECKING",
            description="Transfer from checking",
            date=date(2026, 3, 15),
            amount_cents=-50000,
            status="approved",
        ),
        Transaction(
            import_id=seed_import.id,
            internal_id=checking.id,
            external_id=None,
            raw_description="SQ *BLUE BOTTLE",
            description="Blue Bottle Coffee",
            date=date(2026, 4, 2),
            amount_cents=-1234,
            status="approved",
            category_id=seed_categories["Dining"].id,
        ),
    ]
    session.add_all(rows)
    await session.commit()
    return rows


async def test_explore_get_200(client, seed_accounts):
    resp = await client.get("/explore")
    assert resp.status_code == 200


async def test_explore_invalid_page(client, seed_accounts):
    resp = await client.get("/explore?page=abc")
    assert resp.status_code == 200


async def test_explore_old_api_explore_returns_404(client, seed_accounts):
    """The deleted /api/explore endpoint must not exist."""
    resp = await client.get("/api/explore")
    assert resp.status_code == 404


async def test_explore_renders_charts_and_table(client, seed_explore_txns):
    """Full page renders stats, the Vega embed, and the Tabulator container."""
    resp = await client.get("/explore?preset=all")
    assert resp.status_code == 200
    # Tabulator container with the remote endpoint
    assert 'id="transactions-table-root"' in resp.text
    assert 'data-endpoint="/api/transactions/table"' in resp.text
    assert 'id="transactions-table"' in resp.text
    assert "explore-table.js" in resp.text
    # Stats + charts rendered server-side
    assert "vegaEmbed" in resp.text
    assert 'id="monthly-chart"' in resp.text
    # Three matching txns (including the transfer pair) are counted
    assert '<div class="stat-value">3</div>' in resp.text


async def test_explore_no_data_alert(client, seed_accounts):
    resp = await client.get("/explore")
    assert "No transactions match the current filters." in resp.text


async def test_explore_initial_filter_seed(client, seed_explore_txns):
    """Query-string name filters seed the table's initialHeaderFilter."""
    resp = await client.get(
        "/explore?preset=all&internal=Checking&external=Savings&category=Dining"
    )
    assert resp.status_code == 200
    assert '"internal_account.name": "Checking"' in resp.text
    assert '"external_account.name": "Savings"' in resp.text
    assert '"category.name": "Dining"' in resp.text


async def test_explore_initial_filter_empty_by_default(client, seed_accounts):
    resp = await client.get("/explore")
    assert "data-initial-filter='{}'" in resp.text


async def test_explore_transfers_counted_in_stats(client, seed_explore_txns):
    """Decision 6: transfers are included in stats, not excluded."""
    resp = await client.get("/explore?preset=all")
    # Transfer pair contributes +$500.00 income; together with the coffee
    # purchase, expenses total $-512.34.
    assert "$500.00" in resp.text
    assert "$-512.34" in resp.text


async def test_explore_custom_range(client, seed_explore_txns):
    resp = await client.get(
        "/explore?preset=custom&date_from=2026-03-01&date_to=2026-03-31"
    )
    assert resp.status_code == 200
    assert 'data-date-from="2026-03-01"' in resp.text
    assert 'data-date-to="2026-03-31"' in resp.text
    # Only the transfer pair falls inside the custom range
    assert '<div class="stat-value">2</div>' in resp.text


async def test_old_dashboard_returns_404(client, seed_accounts):
    resp = await client.get("/dashboard")
    assert resp.status_code == 404


async def test_old_transactions_returns_404(client, seed_accounts):
    resp = await client.get("/transactions")
    assert resp.status_code == 404


# === Import Page ===


async def test_import_page_get_200(client, seed_accounts):
    resp = await client.get("/import")
    assert resp.status_code == 200


async def test_import_preview_missing_file(client, seed_accounts):
    resp = await client.post("/import/preview")
    assert resp.status_code == 422


async def test_import_preview_renders_tabulator(client, seed_accounts):
    resp = await client.post(
        "/import/preview",
        files={
            "file": (
                "test.csv",
                b"date,amount,description\n2026-01-15,19.99,Coffee\n",
                "text/csv",
            )
        },
    )
    assert resp.status_code == 200
    assert "data-preview-table" in resp.text
    assert "data-rows='" in resp.text
    assert "import-preview-table.js" in resp.text


async def test_import_commit_unknown_importer(client, seed_accounts):
    resp = await client.post(
        "/import/commit",
        data={"importer": "nonexistent", "account": "Checking", "token": "faketoken"},
    )
    assert resp.status_code == 422


async def test_import_preview_does_not_leak_internals(client, seed_accounts):
    resp = await client.post(
        "/import/preview",
        files={"file": ("test.csv", b"bad,data,here\n1,2,3", "text/csv")},
    )
    assert resp.status_code == 422
    assert "Traceback" not in resp.text
    assert "alert" in resp.text


async def test_old_upload_returns_404(client, seed_accounts):
    resp = await client.get("/upload")
    assert resp.status_code == 404


# === Data: Accounts ===


async def test_data_accounts_get_200(client, seed_accounts):
    resp = await client.get("/data/accounts")
    assert resp.status_code == 200


# === Data: Categories ===


async def test_data_categories_get_200(client, seed_accounts):
    resp = await client.get("/data/categories")
    assert resp.status_code == 200


# === Data: Redirect ===


async def test_data_redirect_to_accounts(client, seed_accounts):
    resp = await client.get("/data", follow_redirects=False)
    assert resp.status_code == 307
    assert resp.headers["location"] == "/data/accounts"


# === Data: Transactions ===


async def test_data_transactions_get_200(client, seed_accounts):
    resp = await client.get("/data/transactions")
    assert resp.status_code == 200


# === Root Redirect ===


async def test_explore_redirect_from_root(client, seed_accounts):
    resp = await client.get("/", follow_redirects=False)
    assert resp.status_code == 307
    assert resp.headers["location"] == "/explore"


# === Data: External Accounts ===


async def test_data_external_accounts_get_200(client, seed_accounts):
    resp = await client.get("/data/external-accounts")
    assert resp.status_code == 200


async def test_data_external_accounts_includes_txn_count(
    client, session, seed_accounts, seed_import
):
    checking = seed_accounts["Checking"]
    ext = Account(name="Walmart", kind="external")
    session.add(ext)
    await session.commit()
    await session.refresh(ext)

    txn = Transaction(
        import_id=seed_import.id,
        internal_id=checking.id,
        external_id=ext.id,
        raw_description="Purchase",
        date=date(2026, 1, 15),
        amount_cents=1000,
        status="approved",
    )
    session.add(txn)
    await session.commit()

    resp = await client.post(
        "/api/external-accounts/table",
        json={"page": 1, "size": 25, "sort": [], "filter": []},
    )
    assert resp.status_code == 200
    walmart = next(a for a in resp.json()["data"] if a["name"] == "Walmart")
    assert walmart["txn_count"] == 1


# === Data: Importers ===


async def test_data_importers_get_200(client, seed_accounts):
    resp = await client.get("/data/importers")
    assert resp.status_code == 200


async def test_data_importers_lists_files(client, seed_accounts):
    resp = await client.get("/api/importers")
    assert resp.status_code == 200
    items = resp.json()
    assert "example.py" in {item["filename"] for item in items}
    assert "Example Bank" in {item["name"] for item in items}


# === Data: Imports ===


async def test_data_imports_get_200(client, seed_accounts):
    resp = await client.get("/data/imports")
    assert resp.status_code == 200


# === Data: Categories with counts ===


async def test_data_categories_includes_txn_count_and_explore(
    client, session, seed_accounts, seed_categories, seed_import
):
    checking = seed_accounts["Checking"]
    ext = Account(name="Store", kind="external")
    session.add(ext)
    await session.commit()
    await session.refresh(ext)

    groceries = seed_categories["Groceries"]
    txn = Transaction(
        import_id=seed_import.id,
        internal_id=checking.id,
        external_id=ext.id,
        raw_description="Grocery run",
        date=date(2026, 1, 15),
        amount_cents=5000,
        status="approved",
        category_id=groceries.id,
    )
    session.add(txn)
    await session.commit()

    # The page now renders a Tabulator container; rows come from the JSON API.
    resp = await client.get("/data/categories")
    assert resp.status_code == 200
    assert "categories-table.js" in resp.text

    table = await client.post("/api/categories/table", json={"page": 1, "size": 25})
    groceries = next(row for row in table.json()["data"] if row["name"] == "Groceries")
    assert groceries["txn_count"] == 1


async def test_data_accounts_renders_tabulator_container(client, seed_accounts):
    resp = await client.get("/data/accounts")
    assert resp.status_code == 200
    assert 'id="accounts-table"' in resp.text
    assert "accounts-table.js" in resp.text


async def test_combo_search_with_percent(client, seed_accounts, seed_categories):
    resp = await client.get("/api/categories?q=%25")
    assert resp.status_code == 200
    data = resp.json()
    # % should not match everything -- only items with literal %
    # With 3 seeded categories, matching none means the wildcard was escaped
    assert len(data) == 0


async def test_combo_search_with_underscore(client, seed_accounts, seed_categories):
    resp = await client.get("/api/categories?q=_")
    assert resp.status_code == 200
    data = resp.json()
    # _ should not match single chars -- only items with literal _
    assert len(data) == 0


async def test_old_inbox_tabulator_routes_404(client, seed_accounts):
    """The old HTMX inbox routes must be gone."""
    assert (await client.get("/inbox/commit-summary")).status_code == 404
    assert (await client.post("/inbox/commit")).status_code == 404
    assert (await client.post("/inbox/retrain")).status_code == 404


async def test_old_data_html_routes_404(client, seed_accounts):
    """The old data HTML handlers must be gone."""
    assert (await client.get("/accounts/99999/edit-name")).status_code == 404
    assert (await client.get("/accounts/99999/edit-type")).status_code == 404
    assert (await client.get("/accounts/99999/edit-balance")).status_code == 404
    assert (await client.get("/accounts/99999/edit-balance-date")).status_code == 404
    assert (
        await client.patch("/accounts/99999", data={"name": "Nope"})
    ).status_code == 404
    # POST to /data/accounts returns 405 (GET-only route exists)
    assert (await client.get("/categories/99999/edit-name")).status_code == 404
    assert (
        await client.patch("/categories/99999", data={"name": "X"})
    ).status_code == 404


async def test_old_transaction_html_routes_404(client, seed_accounts):
    """The old transaction HTML handlers must be gone."""
    assert (await client.patch("/transactions/bulk")).status_code == 404
    assert (await client.patch("/transactions/99999")).status_code == 404
    assert (await client.get("/transactions/99999/edit-modal")).status_code == 404
    assert (await client.get("/transactions/99999/row")).status_code == 404
