from datetime import date

import pytest
from sqlalchemy import select

from pipances.models import Transaction, TransactionSplit


@pytest.fixture
async def txn_with_split(session, seed_accounts, seed_categories, seed_import):
    checking = seed_accounts["Checking"]
    groceries = seed_categories["Groceries"]
    txn = Transaction(
        import_id=seed_import.id,
        internal_id=checking.id,
        raw_description="Test Transaction",
        date=date(2026, 1, 15),
        amount_cents=-10000,
        status="pending",
        category_id=groceries.id,
    )
    session.add(txn)
    await session.flush()

    split = TransactionSplit(
        transaction_id=txn.id,
        category_id=groceries.id,
        amount_cents=3000,
    )
    session.add(split)
    await session.commit()
    await session.refresh(txn)
    await session.refresh(split)
    return {"txn": txn, "split": split}


# === POST /transactions/{id}/splits ===


async def test_create_split_valid(
    client, session, seed_accounts, seed_categories, seed_import
):
    checking = seed_accounts["Checking"]
    groceries = seed_categories["Groceries"]
    txn = Transaction(
        import_id=seed_import.id,
        internal_id=checking.id,
        raw_description="Test",
        date=date(2026, 1, 15),
        amount_cents=-10000,
        status="pending",
    )
    session.add(txn)
    await session.commit()
    txn_id = txn.id

    resp = await client.post(
        f"/transactions/{txn_id}/splits",
        data={"amount_dollars": "30.00", "category_id": str(groceries.id)},
    )
    assert resp.status_code == 200
    assert "splits-section" in resp.text

    splits = await session.scalars(
        select(TransactionSplit).where(TransactionSplit.transaction_id == txn_id)
    )
    splits_list = splits.all()
    assert len(splits_list) == 1
    assert splits_list[0].amount_cents == 3000
    assert splits_list[0].category_id == groceries.id


async def test_create_split_without_category(
    client, session, seed_accounts, seed_import
):
    checking = seed_accounts["Checking"]
    txn = Transaction(
        import_id=seed_import.id,
        internal_id=checking.id,
        raw_description="Test",
        date=date(2026, 1, 15),
        amount_cents=-10000,
        status="pending",
    )
    session.add(txn)
    await session.commit()
    txn_id = txn.id

    resp = await client.post(
        f"/transactions/{txn_id}/splits",
        data={"amount_dollars": "30.00", "category_id": ""},
    )
    assert resp.status_code == 200

    splits = await session.scalars(
        select(TransactionSplit).where(TransactionSplit.transaction_id == txn_id)
    )
    split = splits.one()
    assert split.amount_cents == 3000
    assert split.category_id is None


async def test_create_split_zero_amount(client, session, seed_accounts, seed_import):
    checking = seed_accounts["Checking"]
    txn = Transaction(
        import_id=seed_import.id,
        internal_id=checking.id,
        raw_description="Test",
        date=date(2026, 1, 15),
        amount_cents=-10000,
        status="pending",
    )
    session.add(txn)
    await session.commit()
    txn_id = txn.id

    resp = await client.post(
        f"/transactions/{txn_id}/splits",
        data={"amount_dollars": "0", "category_id": ""},
    )
    assert resp.status_code == 422


async def test_create_split_exact_amount_rejected(
    client, session, seed_accounts, seed_import
):
    checking = seed_accounts["Checking"]
    txn = Transaction(
        import_id=seed_import.id,
        internal_id=checking.id,
        raw_description="Test",
        date=date(2026, 1, 15),
        amount_cents=-10000,
        status="pending",
    )
    session.add(txn)
    await session.commit()
    txn_id = txn.id

    resp = await client.post(
        f"/transactions/{txn_id}/splits",
        data={"amount_dollars": "100.00", "category_id": ""},
    )
    assert resp.status_code == 422
    assert "remainder" in resp.text.lower()


async def test_create_split_exceeds_remainder(
    client, session, seed_accounts, seed_import
):
    checking = seed_accounts["Checking"]
    txn = Transaction(
        import_id=seed_import.id,
        internal_id=checking.id,
        raw_description="Test",
        date=date(2026, 1, 15),
        amount_cents=-10000,
        status="pending",
    )
    session.add(txn)
    await session.commit()
    txn_id = txn.id

    resp = await client.post(
        f"/transactions/{txn_id}/splits",
        data={"amount_dollars": "150.00", "category_id": ""},
    )
    assert resp.status_code == 422


async def test_create_split_nonexistent_txn(client, seed_accounts):
    resp = await client.post(
        "/transactions/99999/splits",
        data={"amount_dollars": "30.00"},
    )
    assert resp.status_code == 404


# === PATCH /transactions/{id}/splits/{sid} ===


async def test_update_split_amount(client, session, txn_with_split):
    split_id = txn_with_split["split"].id
    txn_id = txn_with_split["txn"].id

    resp = await client.patch(
        f"/transactions/{txn_id}/splits/{split_id}",
        data={"amount_dollars": "50.00"},
    )
    assert resp.status_code == 200
    assert "splits-section" in resp.text

    session.expire_all()
    updated = await session.get(TransactionSplit, split_id)
    assert updated.amount_cents == 5000


async def test_update_split_category(client, session, txn_with_split):
    split_id = txn_with_split["split"].id
    txn_id = txn_with_split["txn"].id

    resp = await client.patch(
        f"/transactions/{txn_id}/splits/{split_id}",
        data={"category_id": ""},
    )
    assert resp.status_code == 200

    session.expire_all()
    updated = await session.get(TransactionSplit, split_id)
    assert updated.category_id is None


async def test_update_split_eliminates_remainder(client, session, txn_with_split):
    split_id = txn_with_split["split"].id
    txn_id = txn_with_split["txn"].id

    resp = await client.patch(
        f"/transactions/{txn_id}/splits/{split_id}",
        data={"amount_dollars": "100.00"},
    )
    assert resp.status_code == 422


async def test_update_split_nonexistent_split(client, session, txn_with_split):
    txn_id = txn_with_split["txn"].id
    resp = await client.patch(
        f"/transactions/{txn_id}/splits/99999",
        data={"amount_dollars": "30.00"},
    )
    assert resp.status_code == 404


# === DELETE /transactions/{id}/splits/{sid} ===


async def test_delete_split(client, session, txn_with_split):
    split_id = txn_with_split["split"].id
    txn_id = txn_with_split["txn"].id

    resp = await client.delete(
        f"/transactions/{txn_id}/splits/{split_id}",
    )
    assert resp.status_code == 200
    assert "splits-section" in resp.text

    session.expire_all()
    deleted = await session.get(TransactionSplit, split_id)
    assert deleted is None


async def test_delete_split_nonexistent(client, session, txn_with_split):
    txn_id = txn_with_split["txn"].id
    resp = await client.delete(
        f"/transactions/{txn_id}/splits/99999",
    )
    assert resp.status_code == 404
