import polars as pl
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from financial_pipeline.charts import (
    account_monthly_balance,
    account_top_externals,
    category_spending_pie,
    compute_stats,
    monthly_income_expenses_chart,
    top_expenses_chart,
    weekly_spending_chart,
)
from financial_pipeline.db import async_session
from financial_pipeline.models import (
    Account,
    AccountKind,
    Transaction,
    TransactionStatus,
)
from financial_pipeline.routes._utils import shared_context, templates
from financial_pipeline.utils import compute_date_range

router = APIRouter()


async def _dashboard_query(session, date_from, date_to):
    """Query approved transactions filtered by date range, return list of ORM objects."""
    query = (
        select(Transaction)
        .where(Transaction.status == TransactionStatus.APPROVED)
        .options(
            selectinload(Transaction.internal),
            selectinload(Transaction.external),
            selectinload(Transaction.category),
        )
    )
    if date_from is not None:
        query = query.where(Transaction.date >= date_from)
    if date_to is not None:
        query = query.where(Transaction.date <= date_to)
    result = await session.execute(query)
    return result.scalars().all()


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


def _summary_context(df):
    """Build template context for the summary tab."""
    stats = compute_stats(df)
    return {
        "stats": stats,
        "monthly_chart": monthly_income_expenses_chart(df),
        "top_chart": top_expenses_chart(df),
        "weekly_chart": weekly_spending_chart(df),
    }


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    params = request.query_params
    preset = params.get("preset", "last_3_months")
    date_from_str = params.get("date_from")
    date_to_str = params.get("date_to")
    date_from, date_to = compute_date_range(preset, date_from_str, date_to_str)

    async with async_session() as session:
        shared = await shared_context("dashboard", session)
        transactions = await _dashboard_query(session, date_from, date_to)

    if not transactions:
        return templates.TemplateResponse(
            request,
            "dashboard.html",
            {
                "has_data": False,
                **shared,
            },
        )

    df = _transactions_to_df(transactions)

    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "has_data": True,
            "active_tab": "summary",
            "preset": preset,
            "date_from": str(date_from) if date_from else "",
            "date_to": str(date_to) if date_to else "",
            **_summary_context(df),
            **shared,
        },
    )


@router.get("/dashboard/content", response_class=HTMLResponse)
async def dashboard_content(request: Request):
    params = request.query_params
    preset = params.get("preset", "last_3_months")
    date_from_str = params.get("date_from")
    date_to_str = params.get("date_to")
    active_tab = params.get("active_tab", "summary")
    date_from, date_to = compute_date_range(preset, date_from_str, date_to_str)

    date_from_str_out = str(date_from) if date_from else ""
    date_to_str_out = str(date_to) if date_to else ""

    # Update hidden state via OOB swap
    state_oob = (
        f'<div id="dashboard-state" hx-swap-oob="innerHTML:#dashboard-state">'
        f'<input type="hidden" name="preset" value="{preset}">'
        f'<input type="hidden" name="date_from" value="{date_from_str_out}">'
        f'<input type="hidden" name="date_to" value="{date_to_str_out}">'
        f'<input type="hidden" name="active_tab" value="{active_tab}">'
        f"</div>"
    )

    # Re-render date range buttons with updated active state via OOB swap
    date_range_oob = templates.get_template("_dashboard_date_range.html").render(
        {
            "preset": preset,
            "date_from": date_from_str_out,
            "date_to": date_to_str_out,
            "active_tab": active_tab,
        }
    )
    # Add OOB swap attribute to the outer div
    date_range_oob = date_range_oob.replace(
        'id="dashboard-date-range"',
        'id="dashboard-date-range" hx-swap-oob="outerHTML:#dashboard-date-range"',
        1,
    )

    state_oob += date_range_oob

    async with async_session() as session:
        if active_tab == "categories":
            return await _render_categories_tab(
                request, session, date_from, date_to, params, state_oob
            )
        elif active_tab == "accounts":
            return await _render_accounts_tab(
                request, session, date_from, date_to, params, state_oob
            )
        else:
            transactions = await _dashboard_query(session, date_from, date_to)

    if not transactions:
        return HTMLResponse(
            '<div class="alert alert-info"><span>No transactions in this period.</span></div>'
            + state_oob
        )

    df = _transactions_to_df(transactions)
    html = templates.get_template("_dashboard_summary.html").render(
        _summary_context(df)
    )
    return HTMLResponse(html + state_oob)


async def _render_categories_tab(
    request, session, date_from, date_to, params, state_oob
):
    """Render the categories dashboard tab."""
    transactions = await _dashboard_query(session, date_from, date_to)

    # Build category list from transactions in range
    cat_map = {}
    has_uncategorized = False
    for t in transactions:
        if t.category:
            cat_map[t.category.id] = t.category
        else:
            has_uncategorized = True
    categories = sorted(cat_map.values(), key=lambda c: c.name)

    has_expenses = any(t.amount_cents < 0 for t in transactions)

    ctx = {
        "categories": categories,
        "has_uncategorized": has_uncategorized,
        "has_expenses": has_expenses,
        "selected_category_id": None,
        "drilldown": None,
    }

    if has_expenses:
        df = _transactions_to_df(transactions)
        ctx["pie_chart"] = category_spending_pie(df)

    # Handle drill-down
    category_id_param = params.get("category_id", "")
    if category_id_param:
        ctx["selected_category_id"] = category_id_param
        if category_id_param == "uncategorized":
            filtered = [t for t in transactions if t.category is None]
        else:
            cid = int(category_id_param)
            filtered = [t for t in transactions if t.category_id == cid]
            ctx["selected_category_id"] = cid

        income = sum(t.amount_cents for t in filtered if t.amount_cents > 0)
        expenses = sum(t.amount_cents for t in filtered if t.amount_cents < 0)
        top_txns = sorted(filtered, key=lambda t: abs(t.amount_cents), reverse=True)[
            :10
        ]
        ctx["drilldown"] = {
            "income": income,
            "expenses": expenses,
            "transactions": [
                {
                    "date": t.date,
                    "description": t.description or t.raw_description,
                    "amount_cents": t.amount_cents,
                }
                for t in top_txns
            ],
        }

    html = templates.get_template("_dashboard_categories.html").render(ctx)
    return HTMLResponse(html + state_oob)


async def _render_accounts_tab(request, session, date_from, date_to, params, state_oob):
    """Render the accounts dashboard tab."""
    # Get all internal accounts
    result = await session.execute(
        select(Account)
        .where(Account.kind != AccountKind.EXTERNAL, Account.active == True)
        .order_by(Account.name)
    )
    accounts = result.scalars().all()

    ctx = {
        "accounts": accounts,
        "selected_account_id": None,
        "drilldown": None,
    }

    account_id_param = params.get("account_id", "")
    if account_id_param:
        account_id = int(account_id_param)
        ctx["selected_account_id"] = account_id

        account = await session.get(Account, account_id)
        if account:
            transactions = await _dashboard_query(session, date_from, date_to)
            acct_txns = [t for t in transactions if t.internal_id == account_id]

            income = sum(t.amount_cents for t in acct_txns if t.amount_cents > 0)
            expenses = sum(t.amount_cents for t in acct_txns if t.amount_cents < 0)
            net = income + expenses

            # Balance at end of period: starting_balance + all txns up through date_to
            balance_query = select(
                func.coalesce(func.sum(Transaction.amount_cents), 0)
            ).where(
                Transaction.status == TransactionStatus.APPROVED,
                Transaction.internal_id == account_id,
            )
            if date_to is not None:
                balance_query = balance_query.where(Transaction.date <= date_to)
            balance_sum = await session.scalar(balance_query)
            balance = account.starting_balance_cents + balance_sum

            drilldown = {
                "account_name": account.name,
                "balance": balance,
                "income": income,
                "expenses": expenses,
                "net": net,
            }

            if acct_txns:
                df = _transactions_to_df(acct_txns)
                drilldown["monthly_chart"] = account_monthly_balance(
                    df, account.starting_balance_cents
                )
                drilldown["top_externals_chart"] = account_top_externals(df)

            ctx["drilldown"] = drilldown

    html = templates.get_template("_dashboard_accounts.html").render(ctx)
    return HTMLResponse(html + state_oob)
