"""Pydantic response models for the JSON API.

These models drive FastAPI's OpenAPI schema generation.
They document the shape of every API response.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class MlConfidence(BaseModel):
    description: float | None = None
    category: float | None = None
    external: float | None = None


class TransactionRef(BaseModel):
    id: int
    name: str


class TransactionResponse(BaseModel):
    id: int
    date: str
    amount_cents: int
    amount: float
    raw_description: str
    description: str | None = None
    status: str
    marked_for_approval: bool
    ml_confidence: MlConfidence | None = None
    category: TransactionRef | None = None
    external_account: TransactionRef | None = None
    internal_account: TransactionRef | None = None
    import_id: int | None = None
    splits: list[dict[str, Any]] | None = None


class PaginationInfo(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int


class PaginatedTransactions(BaseModel):
    data: list[TransactionResponse]
    pagination: PaginationInfo


class NamedItem(BaseModel):
    id: int
    name: str


class TabulatorSorter(BaseModel):
    field: str
    dir: str = "asc"


class TabulatorFilter(BaseModel):
    field: str
    type: str = "like"
    value: Any = None


class TabulatorRequest(BaseModel):
    """Body Tabulator 6.5.0 sends when all modes are remote, plus page dates."""

    page: int = 1
    size: int = 25
    sort: list[TabulatorSorter] = Field(default_factory=list)
    filter: list[TabulatorFilter] = Field(default_factory=list)
    date_from: str | None = None
    date_to: str | None = None


class TabulatorResponse(BaseModel):
    """Tabulator's default remote-pagination response envelope."""

    last_page: int
    last_row: int
    data: list[TransactionResponse]


class AccountItem(BaseModel):
    id: int
    name: str
    kind: str
    active: bool


class ImportItem(BaseModel):
    id: int
    institution: str
    filename: str | None = None
    imported_at: str
    row_count: int | None = None


class ExploreStats(BaseModel):
    total_income: int
    total_expenses: int
    net: int
    count: int


class ExploreCharts(BaseModel):
    monthly: str | None = None
    top: str | None = None
    weekly: str | None = None


class ExploreResponse(BaseModel):
    data: list[TransactionResponse]
    pagination: PaginationInfo
    stats: ExploreStats | None = None
    charts: ExploreCharts | None = None
    has_data: bool
