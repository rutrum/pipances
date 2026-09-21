"""JSON API for inbox -- pending transactions with filtering."""

from fastapi import APIRouter, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from pipances.db import DatabaseDep
from pipances.db.accounts import get_or_create_external_account
from pipances.db.categories import get_or_create_category
from pipances.db.transactions import (
    commit_marked_transactions,
    commit_summary,
    fetch_page,
    get_txn,
    pending_txn_count,
    set_txn_category,
    set_txn_description,
    set_txn_external,
)
from pipances.models import Account, Category, TransactionStatus
from pipances.routes.api.queries import (
    tabulator_page_to_dict,
    transaction_to_dict,
    txn_page_to_dict,
)
from pipances.routes.api.schemas import (
    CommitResult,
    CommitSummaryResponse,
    InboxRowUpdate,
    PaginatedTransactions,
    TabulatorRequest,
    TabulatorResponse,
    TransactionResponse,
)
from pipances.utils import safe_date, safe_int

router = APIRouter(prefix="/api", tags=["inbox"])


async def _resolve_category(
    session: AsyncSession, value: int | str | None
) -> Category | None:
    """Resolve a category by id or (case-insensitive) name, creating if needed.

    An empty value clears the category. A value that is not an existing id is
    treated as a name, matching the old inbox modal's behaviour.
    """
    raw = str(value).strip() if value is not None else ""
    if not raw:
        return None
    try:
        category = await session.get(Category, int(raw))
    except (TypeError, ValueError):
        category = None
    if category is not None:
        return category
    return await get_or_create_category(session, raw)


async def _resolve_external(
    session: AsyncSession, value: int | str | None
) -> Account | None:
    """Resolve an external account by id or name, creating if needed."""
    raw = str(value).strip() if value is not None else ""
    if not raw:
        return None
    try:
        external = await session.get(Account, int(raw))
    except (TypeError, ValueError):
        external = None
    if external is not None:
        return external
    return await get_or_create_external_account(session, raw)


@router.get(
    "/inbox",
    response_model=PaginatedTransactions,
    summary="List pending (inbox) transactions",
    description=(
        "Return paginated, filterable, sortable pending transactions."
        " Used by the inbox Tabulator table."
    ),
)
async def list_inbox_transactions(
    request: Request,
    database: DatabaseDep,
):
    params = request.query_params
    internal_id_str = params.get("internal_id", "").strip()
    import_id_str = params.get("import_id", "").strip()

    async with database.session() as session:
        page = await fetch_page(
            session,
            statuses=(TransactionStatus.PENDING,),
            date_from=(
                safe_date(params.get("date_from", "").strip())
                if params.get("date_from", "").strip()
                else None
            ),
            date_to=(
                safe_date(params.get("date_to", "").strip())
                if params.get("date_to", "").strip()
                else None
            ),
            internal_id=(safe_int(internal_id_str, 0) if internal_id_str else None),
            import_id=(safe_int(import_id_str, 0) if import_id_str else None),
            sort_col=params.get("sort", "date"),
            sort_dir=params.get("dir", "asc"),
            page=safe_int(params.get("page"), 1, min_val=1),
            page_size=safe_int(params.get("page_size"), 25, min_val=1, max_val=100),
        )
    return txn_page_to_dict(page)


@router.post(
    "/inbox/table",
    response_model=TabulatorResponse,
    summary="Pending transactions for Tabulator (remote mode)",
    description=(
        "Tabulator-native endpoint: accepts Tabulator's page/size/sort/filter"
        " body and returns Tabulator's default remote envelope"
        " (last_page/last_row/data). Used by the /inbox-tabulator page."
    ),
)
async def inbox_table(
    payload: TabulatorRequest,
    database: DatabaseDep,
):
    async with database.session() as session:
        page = await fetch_page(
            session,
            statuses=(TransactionStatus.PENDING,),
            sorters=[s.model_dump() for s in payload.sort],
            tabulator_filters=[f.model_dump() for f in payload.filter],
            page=max(payload.page, 1),
            page_size=min(max(payload.size, 1), 100),
            splits=True,
        )
    return tabulator_page_to_dict(page)


@router.patch(
    "/inbox/transactions/{txn_id}",
    response_model=TransactionResponse,
    summary="Update a pending inbox transaction",
    description=(
        "Apply inline edits to description, category, or external account."
        " Empty values clear the field. Returns the updated inbox row."
    ),
)
async def update_inbox_transaction(
    txn_id: int,
    payload: InboxRowUpdate,
    database: DatabaseDep,
):
    async with database.session() as session:
        txn = await get_txn(session, txn_id, splits=True)
        if txn is None:
            raise HTTPException(status_code=404, detail="Transaction not found")

        if "description" in payload.model_fields_set:
            description = (payload.description or "").strip()
            set_txn_description(txn, description or None)

        if "category_id" in payload.model_fields_set:
            set_txn_category(txn, await _resolve_category(session, payload.category_id))

        if "external_id" in payload.model_fields_set:
            set_txn_external(txn, await _resolve_external(session, payload.external_id))

        if (
            "marked_for_approval" in payload.model_fields_set
            and payload.marked_for_approval is not None
        ):
            if payload.marked_for_approval:
                if not (txn.description or "").strip():
                    raise HTTPException(
                        status_code=422,
                        detail="Description is required for approval",
                    )
                if not txn.external_id:
                    raise HTTPException(
                        status_code=422,
                        detail="External account is required for approval",
                    )
                txn.marked_for_approval = True
            else:
                txn.marked_for_approval = False

        await session.commit()
        await session.refresh(txn, ["internal", "external", "category", "splits"])

    return transaction_to_dict(txn)


@router.get(
    "/inbox/commit-summary",
    response_model=CommitSummaryResponse,
    summary="Preview the pending inbox commit",
    description=(
        "Count the marked pending transactions and list categories / external"
        " accounts that committing them would newly create."
    ),
)
async def inbox_commit_summary(database: DatabaseDep):
    async with database.session() as session:
        summary = await commit_summary(session)
    return {
        "count": summary.count,
        "new_categories": summary.new_categories,
        "new_externals": summary.new_externals,
    }


@router.post(
    "/inbox/commit",
    response_model=CommitResult,
    summary="Commit marked inbox transactions",
    description=(
        "Approve every marked pending transaction, prune orphaned external"
        " accounts, and return the committed and remaining counts."
    ),
)
async def inbox_commit(database: DatabaseDep):
    async with database.session() as session:
        committed = await commit_marked_transactions(session)
        remaining = await pending_txn_count(session)
    return {"committed": committed, "remaining": remaining}
