"""Retrain the ML suggestion model and refresh pending transaction suggestions.

Shared by the legacy HTMX inbox route and the JSON API used by the Tabulator
inbox. Training data is the set of approved transactions; predictions are
applied to pending transactions when the new prediction's confidence beats the
suggestion already stored on the row.
"""

from __future__ import annotations

from typing import NamedTuple, cast

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from pipances.db.transactions import resolve_order, txn_options
from pipances.models import Transaction, TransactionStatus


class RetrainResult(NamedTuple):
    """Outcome of a retrain run.

    ``updated_count`` counts individual field suggestions updated, so a single
    transaction can contribute up to three. ``pending_count`` and
    ``approved_count`` describe the prediction and training sets and let callers
    tell an empty inbox from an empty training set.
    """

    updated_count: int
    pending_count: int
    approved_count: int


async def retrain_pending_suggestions(
    session: AsyncSession,
    *,
    sort_col: str = "date",
    sort_dir: str = "asc",
) -> RetrainResult:
    """Retrain on approved transactions and update pending suggestions.

    Commits the session when suggestions change; callers own the session.
    """
    pending = (
        (
            await session.execute(
                select(Transaction)
                .where(Transaction.status == TransactionStatus.PENDING)
                .options(*txn_options(import_record=True))
                .order_by(resolve_order(sort_col, sort_dir))
            )
        )
        .scalars()
        .all()
    )
    if not pending:
        return RetrainResult(0, 0, 0)

    approved = (
        (
            await session.execute(
                select(Transaction)
                .where(Transaction.status == TransactionStatus.APPROVED)
                .options(*txn_options(import_record=True))
            )
        )
        .scalars()
        .all()
    )
    if not approved:
        return RetrainResult(0, len(pending), 0)

    # Imported lazily so sklearn / TF-IDF are only loaded when a retrain runs.
    from pipances.predict import TransactionPredictor

    train_external_ids = [t.external_id for t in approved]
    predictor = TransactionPredictor()
    predictor.fit(
        [t.raw_description for t in approved],
        [t.amount_cents for t in approved],
        [t.date.weekday() for t in approved],
        [t.date.day for t in approved],
        [str(t.internal_id) for t in approved],
        [t.import_record.institution for t in approved],
        [t.description for t in approved],
        [t.category_id for t in approved],
        [e for e in train_external_ids if e is not None],
    )

    predictions = predictor.predict(
        [t.raw_description for t in pending],
        [t.amount_cents for t in pending],
        [t.date.weekday() for t in pending],
        [t.date.day for t in pending],
        [str(t.internal_id) for t in pending],
        [t.import_record.institution for t in pending],
    )

    updated_count = 0
    for txn, pred in zip(pending, predictions, strict=True):
        if (
            pred.description
            and pred.description.value is not None
            and (
                txn.ml_confidence_description is None
                or pred.description.confidence > txn.ml_confidence_description
            )
        ):
            txn.description = str(pred.description.value)
            txn.ml_confidence_description = pred.description.confidence
            updated_count += 1
        if (
            pred.category_id
            and pred.category_id.value is not None
            and (
                txn.ml_confidence_category is None
                or pred.category_id.confidence > txn.ml_confidence_category
            )
        ):
            txn.category_id = cast(int, pred.category_id.value)
            txn.ml_confidence_category = pred.category_id.confidence
            updated_count += 1
        if (
            pred.external_id
            and pred.external_id.value is not None
            and (
                txn.ml_confidence_external is None
                or pred.external_id.confidence > txn.ml_confidence_external
            )
        ):
            txn.external_id = cast(int, pred.external_id.value)
            txn.ml_confidence_external = pred.external_id.confidence
            updated_count += 1

    await session.commit()
    return RetrainResult(updated_count, len(pending), len(approved))
