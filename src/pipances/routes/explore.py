from math import ceil

import polars as pl
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from pipances.charts import (
    compute_stats,
    monthly_income_expenses_chart,
    top_expenses_chart,
    weekly_spending_chart,
)
from pipances.db import async_session
from pipances.models import (
    Account,
    AccountKind,
    Category,
    Transaction,
    TransactionStatus,
)
from pipances.routes._utils import shared_context, templates
from pipances.routes.transactions import SORT_COLUMNS
from pipances.utils import compute_date_range, safe_int

router = APIRouter()


def _transactions_to_df(transactions):
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


def _build_filters(
    query,
    date_from,
    date_to,
    internal_filter,
    external_filter,
    category_filter,
    exclude_transfers=False,
):
    """Apply date range and account/category filters to a query."""
    if date_from is not None:
        query = query.where(Transaction.date >= date_from)
    if date_to is not None:
        query = query.where(Transaction.date <= date_to)
    if internal_filter:
        query = query.join(Transaction.internal).where(Account.name == internal_filter)
    if external_filter:
        query = query.join(Transaction.external).where(Account.name == external_filter)
    if category_filter == "__uncategorized__":
        query = query.where(Transaction.category_id.is_(None))
    elif category_filter:
        query = query.join(Transaction.category).where(Category.name == category_filter)
    if exclude_transfers:
        query = query.join(Transaction.external).where(
            Account.kind == AccountKind.EXTERNAL
        )
    return query


@router.get("/explore", response_class=HTMLResponse)
async def explore_page(request: Request):
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

    async with async_session() as session:
        # Base query for all matching transactions (approved + pending)
        base_where = Transaction.status.in_(
            [TransactionStatus.APPROVED, TransactionStatus.PENDING]
        )

        # Query all matching transactions for charts/stats
        all_query = (
            select(Transaction)
            .where(base_where)
            .options(
                selectinload(Transaction.internal),
                selectinload(Transaction.external),
                selectinload(Transaction.category),
            )
        )
        all_query = _build_filters(
            all_query,
            date_from,
            date_to,
            internal_filter,
            external_filter,
            category_filter,
            exclude_transfers=True,
        )
        result = await session.execute(all_query)
        all_transactions = result.scalars().all()

        # Count total for pagination
        count_query = select(func.count()).select_from(Transaction).where(base_where)
        count_query = _build_filters(
            count_query,
            date_from,
            date_to,
            internal_filter,
            external_filter,
            category_filter,
            exclude_transfers=True,
        )
        total_count = await session.scalar(count_query)

        total_pages = max(1, ceil(total_count / page_size))
        page = min(page, total_pages)
        offset = (page - 1) * page_size

        # Paginated query for table
        table_query = (
            select(Transaction)
            .where(base_where)
            .options(
                selectinload(Transaction.internal),
                selectinload(Transaction.external),
                selectinload(Transaction.category),
            )
        )
        table_query = _build_filters(
            table_query,
            date_from,
            date_to,
            internal_filter,
            external_filter,
            category_filter,
        )

        col = SORT_COLUMNS.get(sort_col, Transaction.date)
        if sort_dir == "asc":
            table_query = table_query.order_by(col.asc())
        else:
            table_query = table_query.order_by(col.desc())

        result = await session.execute(table_query.offset(offset).limit(page_size))
        page_transactions = result.scalars().all()

        # Get account lists for filter dropdowns
        int_result = await session.execute(
            select(Account.name)
            .where(Account.kind != AccountKind.EXTERNAL)
            .order_by(Account.name)
        )
        internal_accounts = [r[0] for r in int_result]

        ext_result = await session.execute(
            select(Account.name)
            .where(Account.kind == AccountKind.EXTERNAL)
            .order_by(Account.name)
        )
        external_accounts = [r[0] for r in ext_result]

        # Get category names for filter dropdown
        cat_result = await session.execute(
            select(Category.name)
            .join(Transaction, Transaction.category_id == Category.id)
            .where(base_where)
            .distinct()
            .order_by(Category.name)
        )
        category_options = [r[0] for r in cat_result]

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
        content_html = templates.get_template("_explore_content.html").render(ctx)
        # OOB swap the date range buttons
        date_range_oob = templates.get_template("_explore_date_range.html").render(
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
    return templates.TemplateResponse(request, "explore.html", ctx)
