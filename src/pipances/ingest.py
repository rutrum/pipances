import importlib.util
import logging
import os
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import patito as pt
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from pipances.db import async_session
from pipances.models import (
    Account,
    AccountKind,
    Import,
    Transaction,
    TransactionStatus,
)
from pipances.predict import TransactionPredictor
from pipances.schemas import ImportedTransaction

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
IMPORTERS_DIR = Path(
    os.environ.get("PIPANCES_IMPORTERS_DIR", str(PROJECT_ROOT / "importers"))
)


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
    session: AsyncSession, name: str, kind: str = AccountKind.EXTERNAL
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
        row["amount_cents"] = int(round(row["amount"] * 100))

    # Group incoming rows by dedup key (includes internal account)
    csv_counts: Counter[tuple] = Counter()
    for row in rows:
        key = (row["date"], row["amount_cents"], row["description"], internal_account)
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
                .where(Transaction.internal_id == internal.id)
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
        new_txn_ids: list[int] = []

        for row in rows:
            key = (
                row["date"],
                row["amount_cents"],
                row["description"],
                internal_account,
            )
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
                status=TransactionStatus.PENDING,
            )
            session.add(txn)
            await session.flush()
            new_txn_ids.append(txn.id)
            inserted_per_key[key] += 1
            inserted_count += 1
            all_dates.append(row["date"])

        await session.commit()

    # Run ML predictions on newly inserted transactions
    if new_txn_ids:
        await _predict_for_transactions(new_txn_ids)

    duplicate_count = len(rows) - inserted_count
    return IngestResult(
        inserted_count=inserted_count,
        duplicate_count=duplicate_count,
        date_min=min(all_dates) if all_dates else None,
        date_max=max(all_dates) if all_dates else None,
        internal_account_name=internal_account,
    )


async def _predict_for_transactions(txn_ids: list[int]) -> None:
    """Run ML predictions on the given transaction IDs."""
    async with async_session() as session:
        # Load approved transactions as training data
        result = await session.execute(
            select(Transaction)
            .where(Transaction.status == TransactionStatus.APPROVED)
            .options(selectinload(Transaction.import_record))
        )
        approved = result.scalars().all()

        if not approved:
            logger.info("No approved transactions; skipping ML predictions")
            return

        # Build training data
        train_raw = [t.raw_description for t in approved]
        train_amounts = [t.amount_cents for t in approved]
        train_dow = [t.date.weekday() for t in approved]
        train_dom = [t.date.day for t in approved]
        train_internal = [str(t.internal_id) for t in approved]
        train_institution = [t.import_record.institution for t in approved]
        train_desc = [t.description for t in approved]
        train_cat = [t.category_id for t in approved]
        train_ext = [t.external_id for t in approved]

        predictor = TransactionPredictor()
        predictor.fit(
            train_raw,
            train_amounts,
            train_dow,
            train_dom,
            train_internal,
            train_institution,
            train_desc,
            train_cat,
            train_ext,
        )

        # Load new pending transactions
        result = await session.execute(
            select(Transaction)
            .where(Transaction.id.in_(txn_ids))
            .options(selectinload(Transaction.import_record))
        )
        pending = result.scalars().all()

        if not pending:
            return

        pred_raw = [t.raw_description for t in pending]
        pred_amounts = [t.amount_cents for t in pending]
        pred_dow = [t.date.weekday() for t in pending]
        pred_dom = [t.date.day for t in pending]
        pred_internal = [str(t.internal_id) for t in pending]
        pred_institution = [t.import_record.institution for t in pending]

        predictions = predictor.predict(
            pred_raw,
            pred_amounts,
            pred_dow,
            pred_dom,
            pred_internal,
            pred_institution,
        )

        # Apply predictions
        for txn, pred in zip(pending, predictions, strict=True):
            if pred.description:
                txn.description = pred.description.value
                txn.ml_confidence_description = pred.description.confidence
            if pred.category_id:
                txn.category_id = pred.category_id.value
                txn.ml_confidence_category = pred.category_id.confidence
            if pred.external_id:
                txn.external_id = pred.external_id.value
                txn.ml_confidence_external = pred.external_id.confidence

        await session.commit()
