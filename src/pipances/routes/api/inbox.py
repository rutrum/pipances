"""JSON API for inbox -- pending transactions with filtering."""

from fastapi import APIRouter, Request

from pipances.db import DatabaseDep
from pipances.db.transactions import fetch_page
from pipances.models import TransactionStatus
from pipances.routes.api.queries import txn_page_to_dict
from pipances.routes.api.schemas import PaginatedTransactions
from pipances.utils import safe_date, safe_int

router = APIRouter(prefix="/api", tags=["inbox"])


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
