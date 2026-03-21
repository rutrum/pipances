## Why

The dashboard currently shows all approved transactions with no filtering and no way to focus on specific dimensions (categories, accounts). Users need time-scoped views and drill-down capabilities to understand their finances across different periods and dimensions.

## What Changes

- Add a top-level time range filter to the dashboard with presets: Last Month, Last 3 Months (default), YTD, Last Year, All Time, and Custom date range
- Add `last_year` preset to the existing `_compute_date_range` helper
- Restructure the dashboard into 3 tabs, each rendered as HTMX partials:
  - **Summary**: Current dashboard content (stats bar + 3 charts), filtered by time range. Drop the redundant "Net Total" stat — keep only Income, Expenses, Net.
  - **Categories**: Pie/donut chart of spending by category (uncategorized as its own slice), dropdown to select a category for drill-down showing income/expense totals and top 10 transactions table.
  - **By Account**: Dropdown to select an internal account, showing balance at end of period, income/expenses/net stats, monthly cumulative balance trend chart, and top external accounts chart.
- Add 3 new HTMX endpoints: `/dashboard/summary`, `/dashboard/categories`, `/dashboard/accounts`

## Capabilities

### New Capabilities
(None — all new requirements are additions to the existing dashboard capability)

### Modified Capabilities
- `dashboard`: Add time range filter, tab navigation (Summary/Categories/By Account), category breakdown with drill-down, account drill-down with balance and charts; remove Net Total stat; scope all content to selected time range

## Impact

- `src/financial_pipeline/main.py`: New route handlers for tab partials, modify existing dashboard route to include time range and tab state
- `src/financial_pipeline/charts.py`: New chart functions (category pie, account monthly trend, account top externals); existing chart functions need to accept pre-filtered DataFrames
- `src/financial_pipeline/templates/dashboard.html`: Restructure into tabbed layout with time range controls
- New template partials: `_dashboard_summary.html`, `_dashboard_categories.html`, `_dashboard_accounts.html`, `_dashboard_date_range.html`
- Rename `_date_range.html` to `_txn_date_range.html` for consistency
- `_compute_date_range` helper: Add `last_year` preset
