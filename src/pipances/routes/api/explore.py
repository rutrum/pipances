"""JSON API for the explore page -- transactions, stats, and charts."""

import polars as pl
from fastapi import APIRouter, Request

from pipances.charts import (
    compute_stats,
    monthly_income_expenses_chart,
    top_expenses_chart,
    weekly_spending_chart,
)
from pipances.routes.api.queries import query_transactions
from pipances.routes.api.schemas import ExploreResponse
from pipances.utils import compute_date_range, safe_int

router = APIRouter(prefix="/api", tags=["explore"])


def _transactions_to_df(transactions: list[dict]) -> pl.DataFrame:
    """Convert transaction dicts to a Polars DataFrame for charting."""
    return pl.DataFrame(
        {
            "date": pl.Series([t["date"] for t in transactions]).str.to_date(
                "%Y-%m-%d"
            ),
            "amount_cents": [t["amount_cents"] for t in transactions],
            "description": [
                t.get("description") or t["raw_description"] for t in transactions
            ],
            "external_name": [
                t.get("external_account", {}).get("name", "")
                if t.get("external_account")
                else ""
                for t in transactions
            ],
            "internal_name": [
                t.get("internal_account", {}).get("name", "")
                if t.get("internal_account")
                else ""
                for t in transactions
            ],
            "category_name": [
                t.get("category", {}).get("name", "Uncategorized")
                if t.get("category")
                else "Uncategorized"
                for t in transactions
            ],
            "internal_id": [
                t.get("internal_account", {}).get("id")
                if t.get("internal_account")
                else None
                for t in transactions
            ],
        }
    )


@router.get(
    "/explore",
    response_model=ExploreResponse,
    summary="Explore page data",
    description=(
        "Return all data needed for the Explore page: paginated transactions,"
        " summary stats, and Vega-Lite chart specs."
        " Used by the explore page Tabulator table and chart containers."
    ),
)
async def explore_data(request: Request):
    params = request.query_params
    preset = params.get("preset", "ytd")
    date_from_str = params.get("date_from")
    date_to_str = params.get("date_to")
    date_from, date_to = compute_date_range(preset, date_from_str, date_to_str)

    internal_filter = params.get("internal") or None
    external_filter = params.get("external") or None
    category_filter = params.get("category") or None
    sort_col = params.get("sort", "date")
    sort_dir = params.get("dir", "desc")
    page = safe_int(params.get("page"), 1, min_val=1)
    page_size = safe_int(params.get("page_size"), 25, min_val=1, max_val=100)

    all_result = await query_transactions(
        date_from=date_from,
        date_to=date_to,
        internal_filter=internal_filter,
        external_filter=external_filter,
        category_filter=category_filter,
        exclude_transfers=True,
        page=1,
        page_size=100000,
    )

    table_result = await query_transactions(
        date_from=date_from,
        date_to=date_to,
        internal_filter=internal_filter,
        external_filter=external_filter,
        category_filter=category_filter,
        sort_col=sort_col,
        sort_dir=sort_dir,
        page=page,
        page_size=page_size,
    )

    all_txns = all_result["data"]
    has_data = len(all_txns) > 0
    stats = None
    monthly_chart = None
    top_chart = None
    weekly_chart = None

    if has_data:
        df = _transactions_to_df(all_txns)
        stats = compute_stats(df)
        stats["count"] = len(all_txns)
        monthly_chart = monthly_income_expenses_chart(df)
        top_chart = top_expenses_chart(df)
        weekly_chart = weekly_spending_chart(df)

    return {
        "data": table_result["data"],
        "pagination": table_result["pagination"],
        "stats": {
            "total_income": stats["total_income"],
            "total_expenses": stats["total_expenses"],
            "net": stats["net"],
            "count": stats["count"],
        }
        if stats
        else None,
        "charts": {
            "monthly": monthly_chart,
            "top": top_chart,
            "weekly": weekly_chart,
        }
        if has_data
        else None,
        "has_data": has_data,
    }
