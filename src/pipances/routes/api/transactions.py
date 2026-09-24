"""JSON API for transactions -- list, single lookup, categories, accounts."""

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from sqlalchemy import select

from pipances.db import DatabaseDep
from pipances.db.accounts import get_active_internal_accounts, get_external_accounts
from pipances.db.categories import get_categories
from pipances.db.transactions import fetch_page, get_txn
from pipances.models import Account, Category
from pipances.routes.api.queries import (
    tabulator_page_to_dict,
    transaction_to_dict,
)
from pipances.routes.api.schemas import (
    AccountItem,
    NamedItem,
    TabulatorResponse,
    TransactionResponse,
    TransactionsTableRequest,
)
from pipances.utils import escape_like, safe_date

router = APIRouter(prefix="/api", tags=["transactions"])


@router.post(
    "/transactions/table",
    response_model=TabulatorResponse,
    summary="Transactions for Tabulator (remote mode)",
    description=(
        "Tabulator-native endpoint: accepts Tabulator's page/size/sorters/filters"
        " body and returns Tabulator's default remote envelope"
        " (last_page/last_row/data). Used by /data/transactions and /explore."
    ),
)
async def transactions_table(
    payload: TransactionsTableRequest,
    database: DatabaseDep,
):
    async with database.session() as session:
        page = await fetch_page(
            session,
            date_from=safe_date(payload.date_from),
            date_to=safe_date(payload.date_to),
            internal_filter=payload.internal or None,
            external_filter=payload.external or None,
            category_filter=payload.category or None,
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
