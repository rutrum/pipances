"""JSON API for transactions -- list, single lookup, categories, accounts."""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from pipances.db import DatabaseDep
from pipances.db.accounts import get_active_internal_accounts, get_external_accounts
from pipances.db.categories import get_categories
from pipances.db.transactions import fetch_page, get_txn
from pipances.routes.api.queries import transaction_to_dict, txn_page_to_dict
from pipances.routes.api.schemas import (
    AccountItem,
    NamedItem,
    PaginatedTransactions,
    TransactionResponse,
)
from pipances.utils import compute_date_range, safe_int

router = APIRouter(prefix="/api", tags=["transactions"])


@router.get(
    "/transactions",
    response_model=PaginatedTransactions,
    summary="List all transactions",
    description=(
        "Return paginated, filterable, sortable transactions"
        " (approved + pending). Used by the explore and data/transactions tables."
    ),
)
async def list_transactions(
    request: Request,
    database: DatabaseDep,
):
    params = request.query_params
    date_from, date_to = compute_date_range(
        params.get("preset", "all"),
        params.get("date_from"),
        params.get("date_to"),
    )
    async with database.session() as session:
        page = await fetch_page(
            session,
            date_from=date_from,
            date_to=date_to,
            internal_filter=params.get("internal") or None,
            external_filter=params.get("external") or None,
            category_filter=params.get("category") or None,
            sort_col=params.get("sort", "date"),
            sort_dir=params.get("dir", "desc"),
            page=safe_int(params.get("page"), 1, min_val=1),
            page_size=safe_int(params.get("page_size"), 25, min_val=1, max_val=100),
            description_filter=params.get("description") or None,
            category_name_filter=params.get("category_name") or None,
            external_name_filter=params.get("external_name") or None,
            internal_name_filter=params.get("internal_name") or None,
        )
    return txn_page_to_dict(page)


@router.get(
    "/transactions/{transaction_id}",
    response_model=TransactionResponse,
    summary="Get a single transaction",
    description="Return a single transaction by ID with all related entities.",
)
async def get_transaction(
    transaction_id: int,
    database: DatabaseDep,
):
    async with database.session() as session:
        txn = await get_txn(session, transaction_id, splits=True)
    if txn is None:
        return JSONResponse({"detail": "Transaction not found"}, status_code=404)
    return transaction_to_dict(txn)


@router.get(
    "/categories",
    response_model=list[NamedItem],
    summary="List all categories",
    description=(
        "Return all categories ordered by name."
        " Used by Tabulator list editors for inline category selection."
    ),
)
async def list_categories(database: DatabaseDep):
    async with database.session() as session:
        return [{"id": c.id, "name": c.name} for c in await get_categories(session)]


@router.get(
    "/accounts",
    response_model=list[AccountItem],
    summary="List internal accounts",
    description=(
        "Return all active internal accounts (checking, savings, credit_card)"
        " ordered by name."
    ),
)
async def list_accounts(database: DatabaseDep):
    async with database.session() as session:
        accounts = await get_active_internal_accounts(session)
        return [
            {"id": a.id, "name": a.name, "kind": a.kind, "active": a.active}
            for a in accounts
        ]


@router.get(
    "/external-accounts",
    response_model=list[AccountItem],
    summary="List external accounts",
    description="Return all external (merchant) accounts ordered by name.",
)
async def list_external_accounts(database: DatabaseDep):
    async with database.session() as session:
        return [
            {"id": a.id, "name": a.name, "kind": a.kind, "active": a.active}
            for a in await get_external_accounts(session)
        ]
