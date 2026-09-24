import polars as pl
from fastapi import APIRouter, Request, Response
from fastapi.responses import HTMLResponse
from sqlalchemy import select

from pipances.charts import (
    compute_stats,
    monthly_income_expenses_chart,
    top_expenses_chart,
    weekly_spending_chart,
)
from pipances.db import DatabaseDep
from pipances.db.transactions import (
    VISIBLE_STATUSES,
    apply_filters,
    statuses_where,
    txn_options,
)
from pipances.models import Transaction
from pipances.routes._utils import shared_context, static_version, templates
from pipances.utils import compute_date_range

router = APIRouter()


def _transactions_to_df(transactions) -> pl.DataFrame:
    """Convert transaction ORM objects to a Polars DataFrame."""
    return pl.DataFrame(
        {
            "date": [t.date for t in transactions],
            "amount_cents": [t.amount_cents for t in transactions],
            "description": [t.description or t.raw_description for t in transactions],
            "external_name": [
                t.external.name if t.external else "" for t in transactions
            ],
            "internal_name": [t.internal.name for t in transactions],
            "category_name": [
                t.category.name if t.category else "Uncategorized" for t in transactions
            ],
            "internal_id": [t.internal_id for t in transactions],
        }
    )


@router.get("/explore", response_class=HTMLResponse)
async def explore_page(
    request: Request,
    database: DatabaseDep,
) -> Response:
    """Server-render Explore: stats + charts for all matching transactions.

    The transaction list is a client-side Tabulator remote table fed by
    POST /api/transactions/table; date presets and the custom range do
    full-page navigation so the server-rendered aggregates stay in sync.
    Name filters (internal/external/category) come from the query string and
    seed Tabulator's header filters.
    """
    params = request.query_params

    preset = params.get("preset", "ytd")
    internal_filter = params.get("internal", "")
    external_filter = params.get("external", "")
    category_filter = params.get("category", "")

    date_from, date_to = compute_date_range(
        preset, params.get("date_from"), params.get("date_to")
    )

    preset_ranges = []
    for key, label in (
        ("all", "All"),
        ("ytd", "YTD"),
        ("last_month", "Last 30 Days"),
        ("last_3_months", "Last 90 Days"),
        ("last_year", "Last 365 Days"),
    ):
        df, dt = compute_date_range(key, None, None)
        preset_ranges.append(
            {
                "key": key,
                "label": label,
                "date_from": str(df) if df else "",
                "date_to": str(dt) if dt else "",
            }
        )

    initial_filter = {}
    if internal_filter:
        initial_filter["internal_account.name"] = internal_filter
    if external_filter:
        initial_filter["external_account.name"] = external_filter
    if category_filter:
        initial_filter["category.name"] = category_filter

    async with database.session() as session:
        # All matching transactions feed the charts/stats (transfers included)
        result = await session.execute(
            apply_filters(
                select(Transaction)
                .where(statuses_where(VISIBLE_STATUSES))
                .options(*txn_options()),
                date_from=date_from,
                date_to=date_to,
                internal_filter=internal_filter,
                external_filter=external_filter,
                category_filter=category_filter,
            )
        )
        all_transactions = result.scalars().all()

        shared = await shared_context("explore", session)

    has_data = len(all_transactions) > 0
    stats = None
    monthly_chart = None
    top_chart = None
    weekly_chart = None

    if has_data:
        df = _transactions_to_df(all_transactions)
        stats = compute_stats(df)
        stats["count"] = len(all_transactions)
        monthly_chart = monthly_income_expenses_chart(df)
        top_chart = top_expenses_chart(df)
        weekly_chart = weekly_spending_chart(df)

    ctx = {
        "has_data": has_data,
        "stats": stats,
        "monthly_chart": monthly_chart,
        "top_chart": top_chart,
        "weekly_chart": weekly_chart,
        "preset": preset,
        "date_from": str(date_from) if date_from else "",
        "date_to": str(date_to) if date_to else "",
        "preset_ranges": preset_ranges,
        "has_name_filters": bool(initial_filter),
        "initial_filter": initial_filter,
        "table_js_version": static_version("js", "pages", "explore-table.js"),
    } | shared

    return templates.TemplateResponse(request, "pages/explore.jinja2", ctx)
