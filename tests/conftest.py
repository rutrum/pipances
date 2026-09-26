import pytest

from pipances.db import Database, get_database
from pipances.models import Account, Category, Import, Importer


@pytest.fixture
async def database():
    db = Database("sqlite+aiosqlite:///:memory:")
    await db.create_tables()
    yield db
    await db.dispose()


@pytest.fixture
async def session(database):
    async with database.session() as sess:
        yield sess


@pytest.fixture
async def client(database):
    from pipances.main import app

    app.dependency_overrides[get_database] = lambda: database
    from httpx2 import ASGITransport, AsyncClient

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
async def seed_accounts(session):
    accounts = {
        "Checking": Account(name="Checking", kind="checking"),
        "Savings": Account(name="Savings", kind="savings"),
        "Credit Card": Account(name="Credit Card", kind="credit_card"),
    }
    for a in accounts.values():
        session.add(a)
    await session.commit()
    for a in accounts.values():
        await session.refresh(a)
    return accounts


@pytest.fixture
async def seed_categories(session):
    categories = {
        "Groceries": Category(name="Groceries"),
        "Dining": Category(name="Dining"),
        "Transport": Category(name="Transport"),
    }
    for c in categories.values():
        session.add(c)
    await session.commit()
    for c in categories.values():
        await session.refresh(c)
    return categories


@pytest.fixture
async def seed_import(
    session,
):
    imp = Import(institution="test_bank", filename="test.csv", row_count=0)
    session.add(imp)
    await session.commit()
    await session.refresh(imp)
    return imp


@pytest.fixture
async def seed_importers(session):
    """Two saved SQL importers matching the historical Python examples.

    Returns a dict keyed by display name. "Example Bank" handles a simple
    ``date,amount,description`` CSV; "Metro Credit Union" handles the split
    debit/credit shape.
    """
    simple_sql = """
    SELECT
      CAST(date AS DATE) AS date,
      CAST(amount AS DECIMAL(38,2)) AS amount,
      CAST(description AS VARCHAR) AS description
    FROM raw
    """
    metro_sql = """
    SELECT
      CAST("Transaction Date" AS DATE) AS date,
      CASE
        WHEN "Credit" IS NOT NULL THEN CAST("Credit" AS DECIMAL(38,2))
        ELSE -CAST("Debit" AS DECIMAL(38,2))
      END AS amount,
      CAST("Memo" AS VARCHAR) AS description
    FROM raw
    """

    importers = {
        "Example Bank": Importer(name="Example Bank", sql=simple_sql),
        "Metro Credit Union": Importer(name="Metro Credit Union", sql=metro_sql),
    }
    for imp in importers.values():
        session.add(imp)
    await session.commit()
    for imp in importers.values():
        await session.refresh(imp)
    return importers
