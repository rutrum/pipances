"""JSON API for account tables and account edits."""

from fastapi import APIRouter, HTTPException
from sqlalchemy.exc import IntegrityError

from pipances.db import DatabaseDep
from pipances.db.accounts import fetch_accounts_page, fetch_external_accounts_page
from pipances.models import Account
from pipances.routes.api.queries import tabulator_envelope
from pipances.routes.api.schemas import (
    AccountCreate,
    AccountRow,
    AccountsTableRequest,
    AccountUpdate,
    TabulatorRequest,
    TabulatorTableResponse,
)
from pipances.utils import safe_date

router = APIRouter(prefix="/api", tags=["accounts"])

_VALID_KINDS = {"checking", "savings", "credit_card"}


def _account_to_dict(account: Account) -> dict:
    return {
        "id": account.id,
        "name": account.name,
        "kind": account.kind,
        "starting_balance": account.starting_balance_cents / 100,
        "balance_date": str(account.balance_date) if account.balance_date else None,
        "active": account.active,
    }


@router.post(
    "/external-accounts/table",
    response_model=TabulatorTableResponse,
    summary="External accounts for Tabulator (remote mode)",
    description=(
        "Tabulator-native endpoint: accepts Tabulator's page/size/sort/filter"
        " body and returns Tabulator's default remote envelope."
        " Used by /data/external-accounts."
    ),
)
async def external_accounts_table(
    payload: TabulatorRequest,
    database: DatabaseDep,
):
    async with database.session() as session:
        page = await fetch_external_accounts_page(
            session,
            sorters=[s.model_dump() for s in payload.sort],
            filters=[f.model_dump() for f in payload.filter],
            page=max(payload.page, 1),
            page_size=min(max(payload.size, 1), 100),
        )
    return tabulator_envelope(
        [
            {"id": row.id, "name": row.name, "txn_count": row.txn_count}
            for row in page.rows
        ],
        page.total_count,
        page.total_pages,
    )


@router.post(
    "/accounts/table",
    response_model=TabulatorTableResponse,
    summary="Internal accounts for Tabulator (remote mode)",
    description=(
        "Tabulator-native endpoint used by /data/accounts. Accepts a"
        " show_closed flag to include inactive accounts."
    ),
)
async def accounts_table(
    payload: AccountsTableRequest,
    database: DatabaseDep,
):
    async with database.session() as session:
        page = await fetch_accounts_page(
            session,
            show_closed=payload.show_closed,
            sorters=[s.model_dump() for s in payload.sort],
            filters=[f.model_dump() for f in payload.filter],
            page=max(payload.page, 1),
            page_size=min(max(payload.size, 1), 100),
        )
    return tabulator_envelope(
        [_account_to_dict(account) for account in page.rows],
        page.total_count,
        page.total_pages,
    )


@router.post(
    "/accounts",
    response_model=AccountRow,
    status_code=201,
    summary="Create an internal account",
    description="Create a checking/savings/credit-card account.",
)
async def create_account(
    payload: AccountCreate,
    database: DatabaseDep,
):
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="Name is required")
    kind = payload.kind.strip()
    if kind not in _VALID_KINDS:
        raise HTTPException(status_code=422, detail="Invalid account type")

    async with database.session() as session:
        account = Account(
            name=name,
            kind=kind,
            starting_balance_cents=round((payload.starting_balance or 0) * 100),
            balance_date=safe_date(payload.balance_date),
            active=True,
        )
        session.add(account)
        try:
            await session.commit()
        except IntegrityError:
            await session.rollback()
            raise HTTPException(
                status_code=422,
                detail="An account with that name already exists.",
            ) from None
        await session.refresh(account)
    return _account_to_dict(account)


@router.patch(
    "/accounts/{account_id}",
    response_model=AccountRow,
    summary="Update an internal account",
    description="Edit name/type/balance/balance date, or close/reopen via active.",
)
async def update_account(
    account_id: int,
    payload: AccountUpdate,
    database: DatabaseDep,
):
    async with database.session() as session:
        account = await session.get(Account, account_id)
        if account is None:
            raise HTTPException(status_code=404, detail="Account not found")

        fields = payload.model_fields_set
        if "name" in fields:
            name = (payload.name or "").strip()
            if not name:
                raise HTTPException(status_code=422, detail="Name is required")
            account.name = name
        if "kind" in fields:
            kind = (payload.kind or "").strip()
            if kind not in _VALID_KINDS:
                raise HTTPException(status_code=422, detail="Invalid account type")
            account.kind = kind
        if "starting_balance" in fields:
            account.starting_balance_cents = round(
                (payload.starting_balance or 0) * 100
            )
        if "balance_date" in fields:
            account.balance_date = safe_date(payload.balance_date)
        if "active" in fields:
            account.active = bool(payload.active)

        try:
            await session.commit()
        except IntegrityError:
            await session.rollback()
            raise HTTPException(
                status_code=422,
                detail="An account with that name already exists.",
            ) from None
        await session.refresh(account)
    return _account_to_dict(account)
