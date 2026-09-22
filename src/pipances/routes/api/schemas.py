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
    can_approve: bool = False
    split_count: int | None = None
    ml_confidence: MlConfidence | None = None
    category_id: int | None = None
    external_id: int | None = None
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


class InboxRowUpdate(BaseModel):
    """Single-row edit from the Tabulator inbox. Only provided fields apply."""

    description: str | None = None
    category_id: int | str | None = None
    external_id: int | str | None = None
    marked_for_approval: bool | None = None


class InboxRowBatchUpdate(BaseModel):
    """One row within a range-paste batch.

    Only the fields the clipboard allowlist permits are accepted; the endpoint
    is deliberately narrower than ``InboxRowUpdate`` (no approval toggling).
    """

    id: int
    description: str | None = None
    category_id: int | str | None = None
    external_id: int | str | None = None


class InboxBatchUpdate(BaseModel):
    """All-or-nothing range paste across several inbox rows."""

    updates: list[InboxRowBatchUpdate] = Field(default_factory=list)


class InboxBatchResponse(BaseModel):
    """Updated rows after a successful range paste."""

    data: list[TransactionResponse]


class CommitSummaryResponse(BaseModel):
    """Preview of a pending inbox commit."""

    count: int
    new_categories: list[str]
    new_externals: list[str]


class CommitResult(BaseModel):
    """Outcome of committing marked inbox transactions."""

    committed: int
    remaining: int


class RetrainResponse(BaseModel):
    """Outcome of retraining the suggestion model.

    ``updated_count`` counts individual field suggestions refreshed across the
    pending transactions (a single transaction can contribute up to three).
    """

    updated_count: int


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


class AccountsTableRequest(TabulatorRequest):
    """Accounts table body; adds the show-closed toggle to the base request."""

    show_closed: bool = False


class TabulatorResponse(BaseModel):
    """Tabulator's default remote-pagination response envelope."""

    last_page: int
    last_row: int
    data: list[TransactionResponse]


class TabulatorTableResponse(BaseModel):
    """Tabulator envelope for tables with table-specific row shapes."""

    last_page: int
    last_row: int
    data: list[dict[str, Any]]


class ImporterItem(BaseModel):
    name: str
    filename: str


class CategoryRow(BaseModel):
    id: int
    name: str
    txn_count: int


class CategoryUpdate(BaseModel):
    name: str | None = None


class AccountRow(BaseModel):
    id: int
    name: str
    kind: str
    starting_balance: float
    balance_date: str | None = None
    active: bool


class AccountUpdate(BaseModel):
    name: str | None = None
    kind: str | None = None
    starting_balance: float | None = None
    balance_date: str | None = None
    active: bool | None = None


class AccountCreate(BaseModel):
    name: str
    kind: str
    starting_balance: float | None = None
    balance_date: str | None = None


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
