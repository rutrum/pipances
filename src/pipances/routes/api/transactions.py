"""JSON API for transactions -- list, single lookup, categories, accounts."""

from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy import select

from pipances.db import DatabaseDep
from pipances.db.accounts import get_active_internal_accounts, get_external_accounts
from pipances.db.categories import get_categories
from pipances.db.transactions import fetch_page, get_txn
from pipances.models import Account, Category, Transaction
from pipances.routes.api.queries import (
    tabulator_page_to_dict,
    transaction_to_dict,
    txn_page_to_dict,
)
from pipances.routes.api.schemas import (
    AccountItem,
    NamedItem,
    PaginatedTransactions,
    TabulatorRequest,
    TabulatorResponse,
    TransactionResponse,
)
from pipances.utils import compute_date_range, escape_like, safe_date, safe_int

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


@router.post(
    "/transactions/table",
    response_model=TabulatorResponse,
    summary="Transactions for Tabulator (remote mode)",
    description=(
        "Tabulator-native endpoint: accepts Tabulator's page/size/sorters/filters"
        " body and returns Tabulator's default remote envelope"
        " (last_page/last_row/data). Used by /data/transactions."
    ),
)
async def transactions_table(
    payload: TabulatorRequest,
    database: DatabaseDep,
):
    async with database.session() as session:
        page = await fetch_page(
            session,
            date_from=safe_date(payload.date_from),
            date_to=safe_date(payload.date_to),
            sorters=[s.model_dump() for s in payload.sort],
            tabulator_filters=[f.model_dump() for f in payload.filter],
            page=max(payload.page, 1),
            page_size=min(max(payload.size, 1), 100),
        )
    return tabulator_page_to_dict(page)


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
async def list_categories(
    database: DatabaseDep,
    q: str = Query("", description="Search filter"),
):
    async with database.session() as session:
        if q:
            result = await session.execute(
                select(Category)
                .where(Category.name.ilike(f"%{escape_like(q)}%"))
                .order_by(Category.name)
                .limit(50)
            )
            return [{"id": c.id, "name": c.name} for c in result.scalars().all()]
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
async def list_external_accounts(
    database: DatabaseDep,
    q: str = Query("", description="Search filter"),
):
    async with database.session() as session:
        if q:
            result = await session.execute(
                select(Account)
                .where(Account.kind == "external")
                .where(Account.name.ilike(f"%{escape_like(q)}%"))
                .order_by(Account.name)
                .limit(50)
            )
            return [
                {"id": a.id, "name": a.name, "kind": a.kind, "active": a.active}
                for a in result.scalars().all()
            ]
        return [
            {"id": a.id, "name": a.name, "kind": a.kind, "active": a.active}
            for a in await get_external_accounts(session)
        ]


@router.get(
    "/descriptions",
    summary="Search transaction descriptions",
    description="Return distinct transaction descriptions matching the query.",
)
async def search_descriptions(
    database: DatabaseDep,
    q: str = Query("", description="Search filter"),
):
    async with database.session() as session:
        query = (
            select(Transaction.description)
            .where(Transaction.description.isnot(None))
            .where(Transaction.description != "")
            .distinct()
            .order_by(Transaction.description)
        )
        if q:
            query = query.where(Transaction.description.ilike(f"%{escape_like(q)}%"))
        result = await session.execute(query.limit(50))
        return [{"id": d[0], "name": d[0]} for d in result.fetchall() if d[0]]
