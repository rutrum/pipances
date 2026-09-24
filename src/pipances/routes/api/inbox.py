"""JSON API for inbox -- pending transactions with filtering."""

from fastapi import APIRouter, HTTPException
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
from pipances.models import Account, Category, Transaction, TransactionStatus
from pipances.retrain import retrain_pending_suggestions
from pipances.routes.api.queries import (
    tabulator_page_to_dict,
    transaction_to_dict,
)
from pipances.routes.api.schemas import (
    CommitResult,
    CommitSummaryResponse,
    InboxBatchResponse,
    InboxBatchUpdate,
    InboxRowUpdate,
    RetrainResponse,
    TabulatorRequest,
    TabulatorResponse,
    TransactionResponse,
)

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


@router.post(
    "/inbox/table",
    response_model=TabulatorResponse,
    summary="Pending transactions for Tabulator (remote mode)",
    description=(
        "Tabulator-native endpoint: accepts Tabulator's page/size/sort/filter"
        " body and returns Tabulator's default remote envelope"
        " (last_page/last_row/data). Used by the /inbox page."
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
    "/inbox/transactions/batch",
    response_model=InboxBatchResponse,
    summary="Batch-update pending inbox transactions (range paste)",
    description=(
        "Apply inline edits across several pending transactions in one request."
        " All-or-nothing: any unknown transaction rolls the whole batch back and"
        " returns 422. Only description, category and external account are"
        " accepted. Empty values clear the field."
    ),
)
async def batch_update_inbox_transactions(
    payload: InboxBatchUpdate,
    database: DatabaseDep,
):
    if not payload.updates:
        return {"data": []}

    async with database.session() as session:
        updated: dict[int, Transaction] = {}
        for update in payload.updates:
            txn = await get_txn(session, update.id, splits=True)
            if txn is None:
                raise HTTPException(
                    status_code=422,
                    detail=f"Transaction {update.id} not found",
                )
            if "description" in update.model_fields_set:
                description = (update.description or "").strip()
                set_txn_description(txn, description or None)
            if "category_id" in update.model_fields_set:
                set_txn_category(
                    txn, await _resolve_category(session, update.category_id)
                )
            if "external_id" in update.model_fields_set:
                set_txn_external(
                    txn, await _resolve_external(session, update.external_id)
                )
            updated[update.id] = txn

        await session.commit()
        for txn in updated.values():
            await session.refresh(txn, ["internal", "external", "category", "splits"])

    return {"data": [transaction_to_dict(txn) for txn in updated.values()]}


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


@router.post(
    "/inbox/retrain",
    response_model=RetrainResponse,
    summary="Retrain the suggestion model",
    description=(
        "Retrain the ML model on approved transactions and refresh pending"
        " suggestions. Returns the number of individual field suggestions"
        " updated (zero when there is nothing to train on or change)."
    ),
)
async def inbox_retrain(database: DatabaseDep):
    async with database.session() as session:
        result = await retrain_pending_suggestions(session)
    return {"updated_count": result.updated_count}
