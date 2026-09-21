from datetime import date
from typing import cast

import altair as alt
import polars as pl


def compute_stats(df: pl.DataFrame) -> dict:
    total_income = int(df.filter(pl.col("amount_cents") > 0)["amount_cents"].sum() or 0)
    total_expenses = int(
        df.filter(pl.col("amount_cents") < 0)["amount_cents"].sum() or 0
    )
    net = total_income + total_expenses
    return {
        "total_income": total_income,
        "total_expenses": total_expenses,
        "net": net,
    }


def monthly_income_expenses_chart(df: pl.DataFrame) -> str:
    if len(df) == 0:
        return alt.Chart(pl.DataFrame()).to_json()

    # Truncate dates to month start
    monthly = (
        df.with_columns(
            pl.col("date").dt.truncate("1mo").alias("month"),
        )
        .group_by("month")
        .agg(
            pl.col("amount_cents")
            .filter(pl.col("amount_cents") > 0)
            .sum()
            .alias("income"),
            pl.col("amount_cents")
            .filter(pl.col("amount_cents") < 0)
            .sum()
            .abs()
            .alias("expenses"),
        )
        .sort("month")
    )

    # Get min and max months
    min_month = cast(date | None, monthly["month"].min())
    max_month = cast(date | None, monthly["month"].max())

    # Generate all months in range
    if min_month is None or max_month is None:
        return alt.Chart(pl.DataFrame()).to_json()
    all_months = pl.date_range(
        min_month, max_month, interval="1mo", closed="both", eager=True
    )

    # Create full month range with 0 values for missing months
    full_range = pl.DataFrame({"month": all_months})
    monthly = full_range.join(monthly, on="month", how="left").fill_null(0)

    # Convert to dollar amounts and format month for display
    monthly = monthly.with_columns(
        pl.col("income").truediv(100).alias("income"),
        pl.col("expenses").truediv(100).alias("expenses"),
        pl.col("month").dt.strftime("%b %Y").alias("month_label"),
    )

    data = monthly.unpivot(
        index=["month", "month_label"],
        on=["income", "expenses"],
        variable_name="type",
        value_name="amount",
    ).to_pandas()

    chart = (
        alt.Chart(data)
        .mark_bar()
        .encode(
            x=alt.X(
                "month_label:N",
                title="Month",
                sort=None,  # Preserve the chronological order from data
                axis=alt.Axis(labelAngle=0),
            ),
            y=alt.Y("amount:Q", title="Amount ($)"),
            color=alt.Color(
                "type:N",
                title="Type",
                scale=alt.Scale(
                    domain=["income", "expenses"],
                    range=["#36d399", "#f87272"],
                ),
            ),
            xOffset="type:N",
            tooltip=[
                "month_label:N",
                "type:N",
                alt.Tooltip("amount:Q", format="$,.2f"),
            ],
        )
        .properties(title="Monthly Income vs Expenses", width="container", height=300)
    )

    return chart.to_json()


def top_expenses_chart(df: pl.DataFrame, n: int = 10) -> str:
    expenses = (
        df.filter(pl.col("amount_cents") < 0)
        .group_by("external_name")
        .agg(pl.col("amount_cents").sum().abs().alias("total"))
        .sort("total", descending=True)
        .head(n)
        .with_columns(pl.col("total").truediv(100).alias("total"))
    ).to_pandas()

    chart = (
        alt.Chart(expenses)
        .mark_bar()
        .encode(
            x=alt.X("total:Q", title="Total ($)"),
            y=alt.Y("external_name:N", title="", sort="-x"),
            tooltip=["external_name:N", alt.Tooltip("total:Q", format="$,.2f")],
            color=alt.value("#f87272"),
        )
        .properties(title="Top Expenses by Account", width="container", height=300)
    )

    return chart.to_json()


def weekly_spending_chart(df: pl.DataFrame) -> str:
    weekly = (
        df.filter(pl.col("amount_cents") < 0)
        .with_columns(
            pl.col("date").dt.truncate("1w").alias("week_start"),
        )
        .group_by("week_start")
        .agg(pl.col("amount_cents").sum().abs().alias("total"))
        .sort("week_start")
        .with_columns(pl.col("total").truediv(100).alias("total"))
    ).to_pandas()

    chart = (
        alt.Chart(weekly)
        .mark_line(point=True)
        .encode(
            x=alt.X("week_start:T", title="Week"),
            y=alt.Y("total:Q", title="Expenses ($)"),
            tooltip=["week_start:T", alt.Tooltip("total:Q", format="$,.2f")],
        )
        .properties(title="Weekly Spending Trend", width="container", height=300)
    )

    return chart.to_json()
