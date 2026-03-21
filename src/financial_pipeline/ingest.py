import importlib.util
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import patito as pt
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from financial_pipeline.db import async_session
from financial_pipeline.models import Account, Import, Transaction
from financial_pipeline.schemas import ImportedTransaction

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
IMPORTERS_DIR = PROJECT_ROOT / "importers"


@dataclass
class IngestResult:
    inserted_count: int
    duplicate_count: int
    date_min: date | None
    date_max: date | None
    internal_account_name: str


@dataclass
class ImporterInfo:
    name: str
    module_name: str
    parse: Callable[[bytes], pt.DataFrame[ImportedTransaction]]


def discover_importers() -> dict[str, ImporterInfo]:
    importers: dict[str, ImporterInfo] = {}

    if not IMPORTERS_DIR.is_dir():
        return importers

    for path in sorted(IMPORTERS_DIR.glob("*.py")):
        if path.name.startswith("_"):
            continue

        module_name = path.stem
        spec = importlib.util.spec_from_file_location(f"importers.{module_name}", path)
        if spec is None or spec.loader is None:
            continue

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        if not hasattr(module, "IMPORTER_NAME"):
            raise ValueError(f"Importer {path} missing IMPORTER_NAME")
        if not hasattr(module, "parse"):
            raise ValueError(f"Importer {path} missing parse() function")

        importers[module_name] = ImporterInfo(
            name=module.IMPORTER_NAME,
            module_name=module_name,
            parse=module.parse,
        )

    return importers


async def _resolve_account(
    session: AsyncSession, name: str, kind: str = "external"
) -> Account:
    account = await session.scalar(select(Account).where(Account.name == name))
    if account is None:
        account = Account(name=name, kind=kind)
        session.add(account)
        await session.flush()
    return account


async def ingest(
    df: pt.DataFrame[ImportedTransaction],
    internal_account: str,
    importer_name: str,
    filename: str | None = None,
) -> IngestResult:
    """Ingest a validated ImportedTransaction DataFrame into the database.

    Uses count-based dedup: same-file duplicates are real transactions,
    cross-import duplicates are skipped.
    """
    ImportedTransaction.validate(df)

    rows = df.to_dicts()
    for row in rows:
        row["amount_cents"] = int(row["amount"] * 100)

    # Group incoming rows by dedup key
    csv_counts: Counter[tuple] = Counter()
    for row in rows:
        key = (row["date"], row["amount_cents"], row["description"])
        csv_counts[key] += 1

    async with async_session() as session:
        internal = await session.scalar(
            select(Account).where(Account.name == internal_account)
        )
        if internal is None:
            raise ValueError(f"Internal account {internal_account!r} not found")

        # Query existing counts for each dedup key
        db_counts: dict[tuple, int] = {}
        for key in csv_counts:
            count = await session.scalar(
                select(func.count())
                .select_from(Transaction)
                .where(Transaction.date == key[0])
                .where(Transaction.amount_cents == key[1])
                .where(Transaction.raw_description == key[2])
            )
            db_counts[key] = count or 0

        # Determine how many to insert per key
        to_insert_per_key: dict[tuple, int] = {}
        for key, csv_count in csv_counts.items():
            to_insert_per_key[key] = max(0, csv_count - db_counts.get(key, 0))

        import_record = Import(
            institution=importer_name,
            filename=filename,
            row_count=len(rows),
        )
        session.add(import_record)
        await session.flush()

        inserted_count = 0
        inserted_per_key: Counter[tuple] = Counter()
        all_dates: list[date] = []

        for row in rows:
            key = (row["date"], row["amount_cents"], row["description"])
            if inserted_per_key[key] >= to_insert_per_key[key]:
                continue

            external = await _resolve_account(session, row["description"])
            txn = Transaction(
                import_id=import_record.id,
                internal_id=internal.id,
                external_id=external.id,
                raw_description=row["description"],
                description=None,
                date=row["date"],
                amount_cents=row["amount_cents"],
                status="pending",
            )
            session.add(txn)
            inserted_per_key[key] += 1
            inserted_count += 1
            all_dates.append(row["date"])

        await session.commit()

    duplicate_count = len(rows) - inserted_count
    return IngestResult(
        inserted_count=inserted_count,
        duplicate_count=duplicate_count,
        date_min=min(all_dates) if all_dates else None,
        date_max=max(all_dates) if all_dates else None,
        internal_account_name=internal_account,
    )
