from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from sqlalchemy import select

from financial_pipeline.models import Account, Base

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATABASE_URL = f"sqlite+aiosqlite:///{PROJECT_ROOT / 'financial_pipeline.db'}"

engine = create_async_engine(DATABASE_URL)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session():
    async with async_session() as session:
        yield session


# Placeholder seed data — will be replaced by user config module
SEED_ACCOUNTS = [
    ("Checking", "checking"),
    ("Savings", "savings"),
    ("Credit Card", "credit_card"),
]


async def seed_accounts():
    async with async_session() as session:
        for name, kind in SEED_ACCOUNTS:
            exists = await session.scalar(select(Account).where(Account.name == name))
            if not exists:
                session.add(Account(name=name, kind=kind))
        await session.commit()
