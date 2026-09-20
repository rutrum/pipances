from datetime import date

from sqlalchemy import select

from pipances.models import Account, Transaction

# === Inbox ===


async def test_inbox_get_200(client, seed_accounts):
    resp = await client.get("/inbox")
    assert resp.status_code == 200


async def test_inbox_invalid_page_param(client, seed_accounts):
    resp = await client.get("/inbox?page=abc")
    assert resp.status_code == 200


async def test_inbox_negative_page_size(client, seed_accounts):
    resp = await client.get("/inbox?page_size=-1")
    assert resp.status_code == 200


async def test_inbox_invalid_date_filter(client, seed_accounts):
    resp = await client.get("/inbox?date_from=not-a-date")
    assert resp.status_code == 200


async def test_inbox_invalid_internal_id_filter(client, seed_accounts):
    resp = await client.get("/inbox?internal_id=abc")
    assert resp.status_code == 200


# === Inbox: Edit Endpoints ===


async def test_edit_description_nonexistent_txn(client, seed_accounts):
    resp = await client.get("/transactions/99999/edit-description")
    assert resp.status_code == 404


async def test_edit_external_nonexistent_txn(client, seed_accounts):
    resp = await client.get("/transactions/99999/edit-external")
    assert resp.status_code == 404


async def test_edit_category_nonexistent_txn(client, seed_accounts):
    resp = await client.get("/transactions/99999/edit-category")
    assert resp.status_code == 404


# === Inbox: Commit Workflow ===


async def test_commit_no_marked_transactions(client, seed_accounts):
    resp = await client.post("/inbox/commit")
    assert resp.status_code == 200
    assert "Nothing to commit" in resp.text


async def test_commit_marked_transactions_approved(
    client, session, seed_accounts, seed_import
):
    checking = seed_accounts["Checking"]
    ext = Account(name="Store", kind="external")
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
        status="pending",
        marked_for_approval=True,
    )
    session.add(txn)
    await session.commit()
    txn_id = txn.id

    resp = await client.post("/inbox/commit")
    assert resp.status_code == 200

    session.expire_all()
    updated = await session.get(Transaction, txn_id)
    assert updated.status == "approved"
    assert updated.marked_for_approval is False


async def test_commit_unmarked_transactions_remain_pending(
    client, session, seed_accounts, seed_import
):
    checking = seed_accounts["Checking"]
    ext = Account(name="Store2", kind="external")
    session.add(ext)
    await session.commit()
    await session.refresh(ext)

    marked_txn = Transaction(
        import_id=seed_import.id,
        internal_id=checking.id,
        external_id=ext.id,
        raw_description="Marked",
        date=date(2026, 1, 15),
        amount_cents=500,
        status="pending",
        marked_for_approval=True,
    )
    unmarked_txn = Transaction(
        import_id=seed_import.id,
        internal_id=checking.id,
        external_id=ext.id,
        raw_description="Unmarked",
        date=date(2026, 1, 16),
        amount_cents=700,
        status="pending",
        marked_for_approval=False,
    )
    session.add_all([marked_txn, unmarked_txn])
    await session.commit()
    unmarked_id = unmarked_txn.id

    resp = await client.post("/inbox/commit")
    assert resp.status_code == 200

    session.expire_all()
    still_pending = await session.get(Transaction, unmarked_id)
    assert still_pending.status == "pending"


# === Explore ===


async def test_explore_get_200(client, seed_accounts):
    resp = await client.get("/explore")
    assert resp.status_code == 200


async def test_explore_invalid_page(client, seed_accounts):
    resp = await client.get("/explore?page=abc")
    assert resp.status_code == 200


async def test_explore_htmx_returns_partial(client, seed_accounts):
    resp = await client.get("/explore", headers={"HX-Request": "true"})
    assert resp.status_code == 200
    assert "<html" not in resp.text
    assert "explore-date-range" in resp.text  # OOB swap present


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


async def test_create_account_valid(client, session, seed_accounts):
    resp = await client.post(
        "/data/accounts",
        data={"name": "New Account", "kind": "checking"},
    )
    assert resp.status_code == 200

    acct = await session.scalar(select(Account).where(Account.name == "New Account"))
    assert acct is not None


async def test_create_account_missing_name(client, seed_accounts):
    resp = await client.post(
        "/data/accounts",
        data={"name": "", "kind": "checking"},
    )
    assert resp.status_code == 422


async def test_create_account_external_kind_rejected(client, seed_accounts):
    resp = await client.post(
        "/data/accounts",
        data={"name": "Ext Acct", "kind": "external"},
    )
    assert resp.status_code == 422


async def test_create_account_duplicate_name(client, seed_accounts):
    resp = await client.post(
        "/data/accounts",
        data={"name": "Checking", "kind": "checking"},
    )
    assert resp.status_code == 422


async def test_edit_account_name_nonexistent(client, seed_accounts):
    resp = await client.get("/accounts/99999/edit-name")
    assert resp.status_code == 404


async def test_edit_account_type_nonexistent(client, seed_accounts):
    resp = await client.get("/accounts/99999/edit-type")
    assert resp.status_code == 404


async def test_edit_account_balance_nonexistent(client, seed_accounts):
    resp = await client.get("/accounts/99999/edit-balance")
    assert resp.status_code == 404


async def test_edit_account_balance_date_nonexistent(client, seed_accounts):
    resp = await client.get("/accounts/99999/edit-balance-date")
    assert resp.status_code == 404


async def test_update_account_nonexistent(client, seed_accounts):
    resp = await client.patch(
        "/accounts/99999",
        data={"name": "Nope"},
    )
    assert resp.status_code == 404


# === Data: Categories ===


async def test_data_categories_get_200(client, seed_accounts):
    resp = await client.get("/data/categories")
    assert resp.status_code == 200


async def test_edit_category_name_nonexistent(client, seed_accounts):
    resp = await client.get("/categories/99999/edit-name")
    assert resp.status_code == 404


# === Data: Redirect ===


async def test_data_redirect_to_accounts(client, seed_accounts):
    resp = await client.get("/data", follow_redirects=False)
    assert resp.status_code == 307
    assert resp.headers["location"] == "/data/accounts"


# === Data: Transactions ===


async def test_data_transactions_get_200(client, seed_accounts):
    resp = await client.get("/data/transactions")
    assert resp.status_code == 200


async def test_data_tab_transactions_redirects(client, seed_accounts):
    resp = await client.get("/data/tab_transactions", follow_redirects=False)
    assert resp.status_code == 307
    assert resp.headers["location"] == "/data/transactions"


# === Root Redirect ===


async def test_explore_redirect_from_root(client, seed_accounts):
    resp = await client.get("/", follow_redirects=False)
    assert resp.status_code == 307
    assert resp.headers["location"] == "/explore"


# === Combo Search ===


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


# === Inbox: OOB thead swap ===


async def test_inbox_htmx_response_includes_thead_oob(client, seed_accounts):
    """HTMX request to /inbox must include the thead with hx-swap-oob.

    This is a regression guard for pipances-857.  If the str.replace() approach
    ever silently fails (e.g. because the template changed attribute order),
    the thead OOB attribute would be missing and sort arrows would stop updating
    after HTMX navigations.  The template-based approach must emit the attribute
    unconditionally when oob=True is passed.
    """
    resp = await client.get("/inbox", headers={"HX-Request": "true"})
    assert resp.status_code == 200
    assert "<html" not in resp.text
    assert 'id="inbox-thead"' in resp.text
    assert 'hx-swap-oob="outerHTML:#inbox-thead"' in resp.text


async def test_inbox_full_page_does_not_include_thead_oob(client, seed_accounts):
    """Full-page render must NOT emit hx-swap-oob on the thead.

    hx-swap-oob in a full-page response has no effect but is a sign that
    the template is leaking OOB attributes unconditionally.
    The attribute should only appear in HTMX partial responses.
    """
    resp = await client.get("/inbox")
    assert resp.status_code == 200
    assert 'hx-swap-oob="outerHTML:#inbox-thead"' not in resp.text
