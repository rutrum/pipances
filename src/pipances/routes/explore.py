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
from pipances.db.accounts import get_active_internal_accounts, get_external_accounts
from pipances.db.categories import category_names_with_transactions
from pipances.db.transactions import (
    VISIBLE_STATUSES,
    apply_filters,
    fetch_page,
    statuses_where,
    txn_options,
)
from pipances.models import Transaction
from pipances.routes._utils import shared_context, templates
from pipances.utils import compute_date_range, safe_int

router = APIRouter()


def _transactions_to_df(transactions) -> pl.DataFrame:
    """Convert transaction ORM objects to a Polars DataFrame."""
    return pl.DataFrame(
        {
            "date": [t.date for t in transactions],
            "amount_cents": [t.amount_cents for t in transactions],
            "description": [t.description or t.raw_description for t in transactions],
            "external_name": [t.external.name for t in transactions],
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
    params = request.query_params

    preset = params.get("preset", "ytd")
    date_from_str = params.get("date_from")
    date_to_str = params.get("date_to")
    sort_col = params.get("sort", "date")
    sort_dir = params.get("dir", "desc")
    internal_filter = params.get("internal", "")
    external_filter = params.get("external", "")
    category_filter = params.get("category", "")
    page = safe_int(params.get("page"), 1, min_val=1)
    page_size = safe_int(params.get("page_size"), 25, min_val=1, max_val=100)

    date_from, date_to = compute_date_range(preset, date_from_str, date_to_str)

    async with database.session() as session:
        # All matching transactions feed the charts/stats (transfers excluded)
        all_result = await session.execute(
            apply_filters(
                select(Transaction)
                .where(statuses_where(VISIBLE_STATUSES))
                .options(*txn_options()),
                date_from=date_from,
                date_to=date_to,
                internal_filter=internal_filter,
                external_filter=external_filter,
                category_filter=category_filter,
                exclude_transfers=True,
            )
        )
        all_transactions = all_result.scalars().all()

        # Count + one sorted page for the table
        txn_page = await fetch_page(
            session,
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
        total_count = txn_page.total_count
        total_pages = txn_page.total_pages
        page = txn_page.page
        page_transactions = txn_page.rows

        # Filter dropdowns
        internal_accounts = [
            a.name for a in await get_active_internal_accounts(session)
        ]
        external_accounts = [a.name for a in await get_external_accounts(session)]
        category_options = await category_names_with_transactions(session)

        shared = await shared_context("explore", session)

    # Build stats and charts from all matching transactions
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
        # Chart and stats data
        "has_data": has_data,
        "stats": stats,
        "monthly_chart": monthly_chart,
        "top_chart": top_chart,
        "weekly_chart": weekly_chart,
        # Transaction table data
        "transactions": page_transactions,
        # Filters and sorting
        "preset": preset,
        "date_from": str(date_from) if date_from else "",
        "date_to": str(date_to) if date_to else "",
        "sort": sort_col,
        "dir": sort_dir,
        "internal_filter": internal_filter,
        "external_filter": external_filter,
        "category_filter": category_filter,
        "internal_accounts": internal_accounts,
        "external_accounts": external_accounts,
        "category_options": category_options,
        # Pagination
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "total_count": total_count,
        # Table template parameters (for _transaction_table.html)
        "endpoint": "/explore",
        "target": "#explore-content",
        "include_selector": "#explore-filters, #explore-pagination-page-size",
        "filters_container_id": "explore-filters",
        "pagination_id": "explore-pagination",
    }

    is_htmx = request.headers.get("HX-Request") == "true"
    if is_htmx:
        content_html = templates.get_template("explore/_explore_content.jinja2").render(
            ctx
        )
        # OOB swap the date range buttons
        date_range_oob = templates.get_template(
            "explore/_explore_date_range.jinja2"
        ).render(
            {"preset": preset, "date_from": ctx["date_from"], "date_to": ctx["date_to"]}
        )
        # OOB swap the hidden filter inputs so they stay in sync
        filters_oob = (
            '<div id="explore-filters" hx-swap-oob="outerHTML:#explore-filters">'
        )
        filters_oob += f'<input type="hidden" name="sort" value="{sort_col}">'
        filters_oob += f'<input type="hidden" name="dir" value="{sort_dir}">'
        if internal_filter:
            filters_oob += (
                f'<input type="hidden" name="internal" value="{internal_filter}">'
            )
        if external_filter:
            filters_oob += (
                f'<input type="hidden" name="external" value="{external_filter}">'
            )
        if category_filter:
            filters_oob += (
                f'<input type="hidden" name="category" value="{category_filter}">'
            )
        filters_oob += "</div>"
        return HTMLResponse(content_html + date_range_oob + filters_oob)

    ctx |= shared
    return templates.TemplateResponse(request, "pages/explore.jinja2", ctx)
