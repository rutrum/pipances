import asyncio
import logging
from collections import Counter
from dataclasses import dataclass
from datetime import date
from typing import cast

import patito as pt
from sqlalchemy import func, select

from pipances.db import Database
from pipances.db.accounts import get_counter_or_create_external
from pipances.db.importers import list_importers
from pipances.db.transactions import txn_options
from pipances.duckdb_transform import ImporterSqlError, run_importers_sql
from pipances.models import (
    Account,
    Import,
    Transaction,
    TransactionStatus,
)
from pipances.predict import TransactionPredictor
from pipances.schemas import ImportedTransaction

logger = logging.getLogger(__name__)


@dataclass
class IngestResult:
    inserted_count: int
    duplicate_count: int
    date_min: date | None
    date_max: date | None
    internal_account_name: str


@dataclass
class ImporterInfo:
    id: int
    name: str
    sql: str


async def discover_importers(database: Database) -> dict[int, ImporterInfo]:
    """All saved SQL importers, keyed by id."""
    async with database.session() as session:
        rows = await list_importers(session)
    return {row.id: ImporterInfo(id=row.id, name=row.name, sql=row.sql) for row in rows}


async def try_all_importers(database: Database, blob: bytes) -> dict[int, dict]:
    """Try every saved importer against the given file bytes.

    Returns a dict keyed by importer id with:
      - success: bool
      - name: importer display name
      - df: validated DataFrame (if success)
      - error: error message (if failure)
    """
    importers = await discover_importers(database)
    if not importers:
        return {}

    raw_results = await asyncio.to_thread(
        run_importers_sql,
        {importer_id: info.sql for importer_id, info in importers.items()},
        blob,
    )

    results: dict[int, dict] = {}
    for importer_id, info in importers.items():
        outcome = raw_results[importer_id]
        if isinstance(outcome, ImporterSqlError):
            results[importer_id] = {
                "success": False,
                "name": info.name,
                "error": str(outcome),
            }
        else:
            results[importer_id] = {
                "success": True,
                "name": info.name,
                "df": outcome,
            }
    return results


async def preview_dedup(
    database: Database,
    df: pt.DataFrame[ImportedTransaction],
    internal_account: str,
) -> list[bool]:
    """Check which rows in df are duplicates of existing DB transactions.

    Returns a list of bools parallel to df rows: True = duplicate, False = new.
    Does NOT write anything to the database.
    """
    ImportedTransaction.validate(df)
    rows = df.to_dicts()
    for row in rows:
        row["amount_cents"] = int(round(row["amount"] * 100))

    # Group incoming rows by dedup key
    csv_counts: Counter[tuple] = Counter()
    for row in rows:
        key = (row["date"], row["amount_cents"], row["description"], internal_account)
        csv_counts[key] += 1

    async with database.session() as session:
        internal = await session.scalar(
            select(Account).where(Account.name == internal_account)
        )
        if internal is None:
            raise ValueError(f"Internal account {internal_account!r} not found")

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

    # Walk rows in order, marking which ones would be duplicates
    inserted_per_key: Counter[tuple] = Counter()
    flags: list[bool] = []
    for row in rows:
        key = (row["date"], row["amount_cents"], row["description"], internal_account)
        if inserted_per_key[key] >= to_insert_per_key[key]:
            flags.append(True)  # duplicate
        else:
            flags.append(False)  # new
            inserted_per_key[key] += 1

    return flags


async def ingest(
    database: Database,
    df: pt.DataFrame[ImportedTransaction],
    internal_account: str,
    importer_name: str,
    filename: str | None = None,
    *,
    importer_id: int | None = None,
    importer_sql: str | None = None,
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

    async with database.session() as session:
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
            importer_id=importer_id,
            importer_name=importer_name,
            importer_sql=importer_sql,
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

            counter_account = await get_counter_or_create_external(
                session, row["description"]
            )
            txn = Transaction(
                import_id=import_record.id,
                internal_id=internal.id,
                counter_account_id=counter_account.id,
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
        await _predict_for_transactions(database, new_txn_ids)

    duplicate_count = len(rows) - inserted_count
    return IngestResult(
        inserted_count=inserted_count,
        duplicate_count=duplicate_count,
        date_min=min(all_dates) if all_dates else None,
        date_max=max(all_dates) if all_dates else None,
        internal_account_name=internal_account,
    )


async def _predict_for_transactions(database: Database, txn_ids: list[int]) -> None:
    """Run ML predictions on the given transaction IDs."""
    async with database.session() as session:
        # Load approved transactions as training data
        result = await session.execute(
            select(Transaction)
            .where(Transaction.status == TransactionStatus.APPROVED)
            .options(*txn_options(import_record=True))
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
        train_counter = [t.counter_account_id for t in approved]

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
            train_counter,
        )

        # Load new pending transactions
        result = await session.execute(
            select(Transaction)
            .where(Transaction.id.in_(txn_ids))
            .options(*txn_options(import_record=True))
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
            if pred.description is not None and pred.description.value is not None:
                txn.description = str(pred.description.value)
                txn.ml_confidence_description = pred.description.confidence
            if pred.category_id is not None and pred.category_id.value is not None:
                txn.category_id = cast(int, pred.category_id.value)
                txn.ml_confidence_category = pred.category_id.confidence
            if (
                pred.counter_account_id is not None
                and pred.counter_account_id.value is not None
            ):
                txn.counter_account_id = cast(int, pred.counter_account_id.value)
                txn.ml_confidence_counter_account = pred.counter_account_id.confidence

        await session.commit()
