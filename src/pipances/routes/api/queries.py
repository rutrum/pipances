"""Serializers shaping ORM objects into JSON API payloads."""

from __future__ import annotations

from typing import Any

from sqlalchemy import inspect as sa_inspect

from pipances.db.transactions import TxnPage
from pipances.models import Transaction


def transaction_to_dict(txn: Transaction) -> dict[str, Any]:
    ml: dict[str, float | None] = {}
    if txn.ml_confidence_description is not None:
        ml["description"] = txn.ml_confidence_description
    if txn.ml_confidence_category is not None:
        ml["category"] = txn.ml_confidence_category
    if txn.ml_confidence_external is not None:
        ml["external"] = txn.ml_confidence_external

    result: dict[str, Any] = {
        "id": txn.id,
        "date": str(txn.date),
        "amount_cents": txn.amount_cents,
        "raw_description": txn.raw_description,
        "description": txn.description,
        "status": txn.status,
        "marked_for_approval": txn.marked_for_approval,
        "ml_confidence": ml if ml else None,
        "category": (
            {"id": txn.category.id, "name": txn.category.name} if txn.category else None
        ),
        "external_account": (
            {"id": txn.external.id, "name": txn.external.name} if txn.external else None
        ),
        "internal_account": (
            {"id": txn.internal.id, "name": txn.internal.name} if txn.internal else None
        ),
        "import_id": txn.import_id,
    }
    if "splits" not in sa_inspect(txn).unloaded:
        result["splits"] = [
            {
                "id": s.id,
                "amount_cents": s.amount_cents,
                "category": (
                    {"id": s.category.id, "name": s.category.name}
                    if s.category
                    else None
                ),
            }
            for s in txn.splits
        ]
    return result


def txn_page_to_dict(page: TxnPage) -> dict[str, Any]:
    """Shape a fetched page into the paginated API envelope."""
    return {
        "data": [transaction_to_dict(t) for t in page.rows],
        "pagination": {
            "page": page.page,
            "page_size": page.page_size,
            "total": page.total_count,
            "total_pages": page.total_pages,
        },
    }
