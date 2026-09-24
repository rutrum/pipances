"""Tests for the Tabulator-native /api/transactions/table endpoint.

Tabulator 6.5.0 sends remote sort/filter entries as ``sort`` and ``filter``
(``dataSendParams`` defaults to ``{}``), so these tests use those wire names.
"""

from datetime import date

import pytest

from pipances.models import Account, Transaction


@pytest.fixture
async def seed_txns(session, seed_accounts, seed_categories, seed_import):
    """Create a handful of transactions with distinct sort/filter dimensions."""
    checking = seed_accounts["Checking"]
    savings = seed_accounts["Savings"]
    coffee = Account(name="Blue Bottle", kind="external")
    market = Account(name="Green Market", kind="external")
    session.add_all([coffee, market])
    await session.commit()
    await session.refresh(coffee)
    await session.refresh(market)

    rows = [
        Transaction(
            import_id=seed_import.id,
            internal_id=checking.id,
            external_id=coffee.id,
            raw_description="SQ *BLUE BOTTLE",
            description="Blue Bottle Coffee",
            date=date(2026, 1, 15),
            amount_cents=-1234,
            status="approved",
            category_id=seed_categories["Dining"].id,
        ),
        Transaction(
            import_id=seed_import.id,
            internal_id=checking.id,
            external_id=market.id,
            raw_description="GREEN MARKET #12",
            description="Weekly groceries",
            date=date(2026, 2, 3),
            amount_cents=-5600,
            status="approved",
            category_id=seed_categories["Groceries"].id,
        ),
        Transaction(
            import_id=seed_import.id,
            internal_id=savings.id,
            external_id=None,
            raw_description="PAYROLL DEPOSIT",
            description="Paycheck",
            date=date(2026, 2, 20),
            amount_cents=250000,
            status="approved",
            category_id=None,
        ),
        Transaction(
            import_id=seed_import.id,
            internal_id=checking.id,
            external_id=market.id,
            raw_description="BUS FARE",
            description=None,
            date=date(2026, 3, 1),
            amount_cents=-275,
            status="pending",
            category_id=seed_categories["Transport"].id,
        ),
    ]
    session.add_all(rows)
    await session.commit()
    return rows


async def _post(client, **body):
    payload = {"page": 1, "size": 25, **body}
    return await client.post("/api/transactions/table", json=payload)


async def test_table_returns_tabulator_envelope(client, seed_txns):
    resp = await _post(client)
    assert resp.status_code == 200
    body = resp.json()
    assert set(body) == {"last_page", "last_row", "data"}
    assert body["last_row"] == 4
    assert len(body["data"]) == 4
    # `amount` is dollars as a number so Tabulator's money formatter works.
    coffee = next(d for d in body["data"] if d["description"] == "Blue Bottle Coffee")
    assert coffee["amount"] == pytest.approx(-12.34)
    assert coffee["category"]["name"] == "Dining"
    assert coffee["external_account"]["name"] == "Blue Bottle"


async def test_table_default_sort_is_date_desc(client, seed_txns):
    resp = await _post(client)
    dates = [d["date"] for d in resp.json()["data"]]
    assert dates == sorted(dates, reverse=True)


async def test_table_like_filter_on_description(client, seed_txns):
    resp = await _post(
        client,
        filter=[{"field": "description", "type": "like", "value": "coffee"}],
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["last_row"] == 1
    assert body["data"][0]["description"] == "Blue Bottle Coffee"


async def test_table_filter_on_category_name(client, seed_txns):
    resp = await _post(
        client,
        filter=[{"field": "category.name", "type": "like", "value": "groc"}],
    )
    body = resp.json()
    assert body["last_row"] == 1
    assert body["data"][0]["category"]["name"] == "Groceries"


async def test_table_filter_on_external_name(client, seed_txns):
    resp = await _post(
        client,
        filter=[{"field": "external_account.name", "type": "like", "value": "market"}],
    )
    body = resp.json()
    assert body["last_row"] == 2


async def test_table_multiple_filters_are_anded(client, seed_txns):
    resp = await _post(
        client,
        filter=[
            {"field": "category.name", "type": "like", "value": "dining"},
            {"field": "description", "type": "like", "value": "coffee"},
        ],
    )
    body = resp.json()
    assert body["last_row"] == 1
    assert body["data"][0]["description"] == "Blue Bottle Coffee"


async def test_table_multi_sort(client, seed_txns):
    resp = await _post(
        client,
        sort=[
            {"field": "category.name", "dir": "asc"},
            {"field": "amount", "dir": "desc"},
        ],
    )
    body = resp.json()
    rows = body["data"]
    # Dining (-12.34) then Groceries (-56.00) then Transport (-2.75) then
    # uncategorized (None, sorts first/last depending on DB but present).
    categories = [r["category"]["name"] if r["category"] else None for r in rows]
    assert categories.index("Dining") < categories.index("Groceries")
    assert categories.index("Groceries") < categories.index("Transport")


async def test_table_unknown_field_is_ignored(client, seed_txns):
    resp = await _post(
        client,
        filter=[{"field": "not_a_field", "type": "like", "value": "x"}],
        sort=[{"field": "evil; DROP TABLE", "dir": "asc"}],
    )
    assert resp.status_code == 200
    assert resp.json()["last_row"] == 4


async def test_table_date_range(client, seed_txns):
    resp = await _post(client, date_from="2026-02-01", date_to="2026-03-15")
    body = resp.json()
    assert body["last_row"] == 3
    for row in body["data"]:
        assert "2026-02-01" <= row["date"] <= "2026-03-15"


async def test_table_pagination(client, seed_txns):
    resp = await _post(client, page=2, size=2)
    body = resp.json()
    assert body["last_row"] == 4
    assert body["last_page"] == 2
    assert len(body["data"]) == 2


async def test_table_page_clamped_past_end(client, seed_txns):
    resp = await _post(client, page=99, size=2)
    assert resp.status_code == 200
    assert len(resp.json()["data"]) == 2


async def test_table_size_capped_at_100(client, seed_txns):
    resp = await _post(client, size=100000)
    assert resp.status_code == 200
    assert len(resp.json()["data"]) == 4


async def test_table_empty_filters_returns_everything(client, seed_txns):
    resp = await _post(client, filter=[], sort=[])
    assert resp.json()["last_row"] == 4


# === Server-side name filters (internal/external/category) ===


async def test_table_internal_name_filter(client, seed_txns):
    resp = await _post(client, internal="Savings")
    body = resp.json()
    assert body["last_row"] == 1
    assert body["data"][0]["internal_account"]["name"] == "Savings"


async def test_table_external_name_filter(client, seed_txns):
    resp = await _post(client, external="Blue Bottle")
    body = resp.json()
    assert body["last_row"] == 1
    assert body["data"][0]["external_account"]["name"] == "Blue Bottle"


async def test_table_category_name_filter(client, seed_txns):
    resp = await _post(client, category="Transport")
    body = resp.json()
    assert body["last_row"] == 1
    assert body["data"][0]["category"]["name"] == "Transport"


async def test_table_name_filters_are_exact_matches(client, seed_txns):
    """Unlike header-filter `like` entries, name filters match exactly."""
    resp = await _post(client, external="Blue")
    assert resp.json()["last_row"] == 0


async def test_table_name_filters_combine_with_dates(client, seed_txns):
    resp = await _post(client, external="Green Market", date_from="2026-02-01")
    body = resp.json()
    # Groceries (Feb 3) and bus fare (Mar 1), but not the Jan coffee purchase.
    assert body["last_row"] == 2


async def test_table_name_filters_are_anded(client, seed_txns):
    resp = await _post(client, internal="Checking", category="Dining")
    body = resp.json()
    assert body["last_row"] == 1
    assert body["data"][0]["description"] == "Blue Bottle Coffee"


async def test_table_unknown_name_filter_matches_nothing(client, seed_txns):
    resp = await _post(client, internal="Not An Account")
    assert resp.json()["last_row"] == 0
