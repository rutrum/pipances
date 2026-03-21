## Context

The dashboard currently renders all approved transactions in a single view with no filtering. It computes stats and 3 Altair charts server-side, passing Vega-Lite JSON specs to the template for client-side rendering. The transactions page already has a time range filter using `_compute_date_range` with presets (YTD, last month, last 3 months, all, custom) and an `_date_range.html` partial.

## Goals / Non-Goals

**Goals:**
- Add time range filtering to the dashboard, reusing the existing `_compute_date_range` helper
- Split the dashboard into 3 HTMX-driven tabs: Summary, Categories, By Account
- Each tab loads as a partial via its own endpoint, filtered by the shared time range
- Categories tab provides a per-category drill-down with transaction listing
- Accounts tab provides a per-account drill-down with balance and trend charts

**Non-Goals:**
- Interactive chart click-to-filter (e.g., clicking a pie slice to select a category) — deferred
- Running balance line chart on the accounts tab — just cumulative monthly balance for now
- Custom chart date granularity (weekly vs monthly toggle)

## Decisions

### 1. Tab content via HTMX partials

Each tab has its own GET endpoint returning an HTML partial:
- `GET /dashboard/summary` — summary stats + 3 charts
- `GET /dashboard/categories` — category pie + optional drill-down
- `GET /dashboard/accounts` — account selector + optional drill-down

The main `GET /dashboard` renders the full page shell (time range + tab bar) and includes the default tab (summary) inline on first load.

**Rationale**: Keeps each tab's data fetching independent. Avoids loading all chart data upfront. Consistent with existing HTMX patterns in the app.

### 2. Time range state management

The time range controls sit above the tabs. A hidden input tracks the active tab name. When:
- **Time range changes**: re-fetches the active tab's endpoint with new time params
- **Tab changes**: fetches the new tab's endpoint with current time params

Both use `hx-include` on a shared form/div containing preset, date_from, date_to, and active_tab inputs.

**Alternative considered**: URL query params for everything. But HTMX's `hx-include` pattern is simpler and already used on the transactions page.

### 3. Reuse and extend `_compute_date_range`

Add `last_year` preset to the existing helper. Change the dashboard's default preset to `last_3_months`. The helper is shared between transactions and dashboard.

### 4. Dashboard date range partial

Create a new `_dashboard_date_range.html` partial rather than reusing `_date_range.html`. The transactions version hard-codes `hx-get="/transactions"` and `hx-target="#txn-table-wrapper"`. The dashboard version needs to target the dashboard content area and include the active tab in requests.

**Alternative considered**: Making `_date_range.html` generic with configurable targets. Adds complexity for two consumers — simpler to have a dashboard-specific version.

### 5. Category pie chart with "Uncategorized" slice

Transactions with `category_id IS NULL` are grouped as "Uncategorized" in the pie chart. This gives visibility into how much data still needs categorization.

### 6. Account balance at end of period

The accounts tab shows "Balance at end of period" computed as:
`starting_balance_cents + SUM(amount_cents WHERE date <= date_to)`

This sums ALL transactions up through `date_to` (not just those after `date_from`), giving a true balance snapshot at the end of the selected period. The income/expenses/net stats below are scoped to the time range.

### 7. Template structure

```
dashboard.html          — full page: time range + tab bar + content div
_dashboard_summary.html — summary tab partial
_dashboard_categories.html — categories tab partial
_dashboard_accounts.html   — accounts tab partial
```

### 8. Chart functions

New functions in `charts.py`:
- `category_spending_pie(df)` — pie/donut chart, expenses by category
- `account_monthly_balance(df, starting_balance_cents)` — cumulative monthly balance line
- `account_top_externals(df)` — horizontal bar of top external accounts

Existing chart functions remain unchanged — the caller passes a pre-filtered DataFrame.

## Risks / Trade-offs

- **Multiple queries per tab**: Each tab endpoint queries the database independently. For now this is fine — the dataset is personal-scale. If it becomes slow, we could cache the filtered DataFrame per request.
- **Vega script loading**: Vega/Vega-Lite/Vega-Embed scripts are currently loaded inside the `{% else %}` block of dashboard.html. With HTMX partials, they need to be available before any tab loads. Move them to the page shell or use `hx-on::after-swap` to initialize charts.
- **Chart re-initialization**: When swapping tab content via HTMX, Vega charts in the new partial need explicit `vegaEmbed()` calls. Inline `<script>` tags in partials execute on HTMX swap by default, so this should work naturally.
