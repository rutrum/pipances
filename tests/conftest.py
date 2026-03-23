import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from financial_pipeline.models import Account, Base, Category, Import


@pytest.fixture
async def engine():
    eng = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest.fixture
async def session(engine):
    async with AsyncSession(engine, expire_on_commit=False) as sess:
        yield sess


@pytest.fixture(autouse=True)
def patch_db(engine, monkeypatch):
    test_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    import financial_pipeline.db as db_mod
    import financial_pipeline.ingest as ingest_mod
    import financial_pipeline.routes.data as data_mod
    import financial_pipeline.routes.explore as explore_mod
    import financial_pipeline.routes.inbox as inbox_mod
    import financial_pipeline.routes.transactions as transactions_mod
    import financial_pipeline.routes.upload as upload_mod
    import financial_pipeline.routes.widgets as widgets_mod

    monkeypatch.setattr(db_mod, "async_session", test_session)
    monkeypatch.setattr(ingest_mod, "async_session", test_session)
    monkeypatch.setattr(explore_mod, "async_session", test_session)
    monkeypatch.setattr(inbox_mod, "async_session", test_session)
    monkeypatch.setattr(data_mod, "async_session", test_session)
    monkeypatch.setattr(transactions_mod, "async_session", test_session)
    monkeypatch.setattr(upload_mod, "async_session", test_session)
    monkeypatch.setattr(widgets_mod, "async_session", test_session)


@pytest.fixture
async def client():
    from httpx import ASGITransport, AsyncClient

    from financial_pipeline.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


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
async def seed_import(session):
    imp = Import(institution="test_bank", filename="test.csv", row_count=0)
    session.add(imp)
    await session.commit()
    await session.refresh(imp)
    return imp
