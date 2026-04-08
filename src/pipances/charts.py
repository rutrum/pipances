import altair as alt
import polars as pl


def compute_stats(df: pl.DataFrame) -> dict:
    total_income = df.filter(pl.col("amount_cents") > 0)["amount_cents"].sum() or 0
    total_expenses = df.filter(pl.col("amount_cents") < 0)["amount_cents"].sum() or 0
    net = total_income + total_expenses
    return {
        "total_income": total_income,
        "total_expenses": total_expenses,
        "net": net,
    }


def _format_dollars(cents: int) -> str:
    return f"${cents / 100:,.2f}"


def monthly_income_expenses_chart(df: pl.DataFrame) -> str:
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
        .with_columns(
            pl.col("income").truediv(100).alias("income"),
            pl.col("expenses").truediv(100).alias("expenses"),
        )
    )

    data = monthly.unpivot(
        index="month",
        on=["income", "expenses"],
        variable_name="type",
        value_name="amount",
    ).to_pandas()

    chart = (
        alt.Chart(data)
        .mark_bar()
        .encode(
            x=alt.X(
                "yearmonth(month):T", title="Month", scale=alt.Scale(bandPosition=0)
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
                "yearmonth(month):T",
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


def category_spending_pie(df: pl.DataFrame) -> str:
    """Pie chart of expenses by category. Expects 'category_name' column."""
    by_cat = (
        df.filter(pl.col("amount_cents") < 0)
        .group_by("category_name")
        .agg(pl.col("amount_cents").sum().abs().alias("total"))
        .sort("total", descending=True)
        .with_columns(pl.col("total").truediv(100).alias("total"))
    ).to_pandas()

    chart = (
        alt.Chart(by_cat)
        .mark_arc(innerRadius=50)
        .encode(
            theta=alt.Theta("total:Q"),
            color=alt.Color("category_name:N", title="Category"),
            tooltip=[
                alt.Tooltip("category_name:N", title="Category"),
                alt.Tooltip("total:Q", format="$,.2f", title="Amount"),
            ],
        )
        .properties(title="Spending by Category", width="container", height=350)
    )

    return chart.to_json()


def account_monthly_balance(df: pl.DataFrame, starting_balance_cents: int) -> str:
    """Cumulative monthly balance line chart for a single account."""
    monthly = (
        df.with_columns(pl.col("date").dt.truncate("1mo").alias("month"))
        .group_by("month")
        .agg(pl.col("amount_cents").sum().alias("net"))
        .sort("month")
        .with_columns(
            (pl.lit(starting_balance_cents) + pl.col("net").cum_sum())
            .truediv(100)
            .alias("balance")
        )
    ).to_pandas()

    chart = (
        alt.Chart(monthly)
        .mark_line(point=True)
        .encode(
            x=alt.X("yearmonth(month):T", title="Month"),
            y=alt.Y("balance:Q", title="Balance ($)"),
            tooltip=[
                "yearmonth(month):T",
                alt.Tooltip("balance:Q", format="$,.2f"),
            ],
        )
        .properties(title="Monthly Balance", width="container", height=300)
    )

    return chart.to_json()


def account_top_externals(df: pl.DataFrame, n: int = 10) -> str:
    """Top external accounts by total absolute transaction amount."""
    by_ext = (
        df.group_by("external_name")
        .agg(pl.col("amount_cents").abs().sum().alias("total"))
        .sort("total", descending=True)
        .head(n)
        .with_columns(pl.col("total").truediv(100).alias("total"))
    ).to_pandas()

    chart = (
        alt.Chart(by_ext)
        .mark_bar()
        .encode(
            x=alt.X("total:Q", title="Total ($)"),
            y=alt.Y("external_name:N", title="", sort="-x"),
            tooltip=[
                "external_name:N",
                alt.Tooltip("total:Q", format="$,.2f"),
            ],
        )
        .properties(title="Top External Accounts", width="container", height=300)
    )

    return chart.to_json()
