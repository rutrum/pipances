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

    split_count: int | None = None
    if "splits" not in sa_inspect(txn).unloaded:
        split_count = len(txn.splits)

    result: dict[str, Any] = {
        "id": txn.id,
        "date": str(txn.date),
        "amount_cents": txn.amount_cents,
        "amount": txn.amount_cents / 100,
        "raw_description": txn.raw_description,
        "description": txn.description,
        "status": txn.status,
        "marked_for_approval": txn.marked_for_approval,
        "can_approve": bool(txn.description and txn.external_id),
        "split_count": split_count,
        "ml_confidence": ml if ml else None,
        "category_id": txn.category_id,
        "external_id": txn.external_id,
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


def tabulator_page_to_dict(page: TxnPage) -> dict[str, Any]:
    """Shape a fetched page into Tabulator's default remote envelope."""
    return tabulator_envelope(
        [transaction_to_dict(t) for t in page.rows],
        page.total_count,
        page.total_pages,
    )


def tabulator_envelope(
    data: list[dict[str, Any]], total_count: int, total_pages: int
) -> dict[str, Any]:
    """Shape arbitrary serialized rows into Tabulator's default remote envelope."""
    return {
        "last_page": total_pages,
        "last_row": total_count,
        "data": data,
    }
