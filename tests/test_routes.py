from datetime import date

from sqlalchemy import select

from financial_pipeline.models import Account, Category, Transaction

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


# === Transactions ===


async def test_transactions_get_200(client, seed_accounts):
    resp = await client.get("/transactions")
    assert resp.status_code == 200


async def test_transactions_invalid_page(client, seed_accounts):
    resp = await client.get("/transactions?page=abc")
    assert resp.status_code == 200


# === Upload ===


async def test_upload_page_get_200(client, seed_accounts):
    resp = await client.get("/upload")
    assert resp.status_code == 200


async def test_upload_missing_file(client, seed_accounts):
    resp = await client.post(
        "/upload",
        data={"importer": "test", "account": "Checking"},
    )
    assert resp.status_code == 422


async def test_upload_unknown_importer(client, seed_accounts):
    resp = await client.post(
        "/upload",
        data={"importer": "nonexistent", "account": "Checking"},
        files={"file": ("test.csv", b"dummy,data", "text/csv")},
    )
    assert resp.status_code == 422
    assert "Unknown importer" in resp.text


async def test_upload_error_does_not_leak_internals(client, seed_accounts):
    resp = await client.post(
        "/upload",
        data={"importer": "nonexistent", "account": "Checking"},
        files={"file": ("test.csv", b"bad,data,here\n1,2,3", "text/csv")},
    )
    assert resp.status_code == 422
    assert "Traceback" not in resp.text
    assert "Error" not in resp.text or "alert" in resp.text


# === Settings: Accounts ===


async def test_settings_accounts_get_200(client, seed_accounts):
    resp = await client.get("/settings/accounts")
    assert resp.status_code == 200


async def test_create_account_valid(client, session, seed_accounts):
    resp = await client.post(
        "/settings/accounts",
        data={"name": "New Account", "kind": "checking"},
    )
    assert resp.status_code == 200

    acct = await session.scalar(select(Account).where(Account.name == "New Account"))
    assert acct is not None


async def test_create_account_missing_name(client, seed_accounts):
    resp = await client.post(
        "/settings/accounts",
        data={"name": "", "kind": "checking"},
    )
    assert resp.status_code == 422


async def test_create_account_external_kind_rejected(client, seed_accounts):
    resp = await client.post(
        "/settings/accounts",
        data={"name": "Ext Acct", "kind": "external"},
    )
    assert resp.status_code == 422


async def test_create_account_duplicate_name(client, seed_accounts):
    resp = await client.post(
        "/settings/accounts",
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


# === Settings: Categories ===


async def test_settings_categories_get_200(client, seed_accounts):
    resp = await client.get("/settings/categories")
    assert resp.status_code == 200


async def test_create_category_valid(client, session, seed_accounts):
    resp = await client.post(
        "/settings/categories",
        data={"name": "Entertainment"},
    )
    assert resp.status_code == 200

    cat = await session.scalar(select(Category).where(Category.name == "Entertainment"))
    assert cat is not None


async def test_create_category_empty_name(client, seed_accounts):
    resp = await client.post(
        "/settings/categories",
        data={"name": ""},
    )
    assert resp.status_code == 422


async def test_delete_category(client, session, seed_accounts, seed_categories):
    groceries = seed_categories["Groceries"]
    resp = await client.delete(f"/categories/{groceries.id}")
    assert resp.status_code == 200

    result = await session.execute(select(Category).where(Category.id == groceries.id))
    assert result.scalar_one_or_none() is None


async def test_edit_category_name_nonexistent(client, seed_accounts):
    resp = await client.get("/categories/99999/edit-name")
    assert resp.status_code == 404


# === Dashboard ===


async def test_dashboard_get_200(client, seed_accounts):
    resp = await client.get("/dashboard")
    assert resp.status_code == 200


async def test_dashboard_redirect_from_root(client, seed_accounts):
    resp = await client.get("/", follow_redirects=False)
    assert resp.status_code == 307
    assert resp.headers["location"] == "/dashboard"


# === Combo Search ===


async def test_combo_search_with_percent(client, seed_accounts, seed_categories):
    resp = await client.get("/api/combo/categories?q=%25")
    assert resp.status_code == 200
    # % should not match everything — only items with literal %
    # With 3 seeded categories, matching all 3 means the wildcard leaked
    for cat_name in ["Groceries", "Dining", "Transport"]:
        assert cat_name not in resp.text


async def test_combo_search_with_underscore(client, seed_accounts, seed_categories):
    resp = await client.get("/api/combo/categories?q=_")
    assert resp.status_code == 200
    # _ should not match single chars — only items with literal _
    for cat_name in ["Groceries", "Dining", "Transport"]:
        assert cat_name not in resp.text
