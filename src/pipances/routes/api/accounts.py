"""JSON API for account tables."""

from fastapi import APIRouter

from pipances.db import DatabaseDep
from pipances.db.accounts import fetch_external_accounts_page
from pipances.routes.api.queries import tabulator_envelope
from pipances.routes.api.schemas import TabulatorRequest, TabulatorTableResponse

router = APIRouter(prefix="/api", tags=["accounts"])


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
