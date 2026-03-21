## 1. Time Range Infrastructure

- [ ] 1.1 Add `last_year` preset to `_compute_date_range` in main.py
- [ ] 1.2 Rename `_date_range.html` to `_txn_date_range.html` and update the transactions template include
- [ ] 1.3 Create `_dashboard_date_range.html` partial with all presets (Last Month, Last 3 Months, YTD, Last Year, All Time, Custom) targeting dashboard content area

## 2. Dashboard Shell and Tab Navigation

- [ ] 2.1 Restructure `dashboard.html` into tabbed layout: time range at top, tab bar (Summary / Categories / By Account), content div for HTMX partials
- [ ] 2.2 Move Vega script tags into the page shell (outside tab content area) so they're available for all tabs
- [ ] 2.3 Add hidden inputs for active tab and time range state, wire tab buttons with `hx-get` and `hx-include`

## 3. Summary Tab

- [ ] 3.1 Extract current dashboard content into `_dashboard_summary.html` partial (stats bar + 3 charts)
- [ ] 3.2 Remove Net Total stat, keep only Income, Expenses, Net
- [ ] 3.3 Add `GET /dashboard/summary` endpoint that accepts time range params, filters transactions, returns the partial
- [ ] 3.4 Update `GET /dashboard` to render summary tab inline on first load with default preset `last_3_months`

## 4. Category Charts

- [ ] 4.1 Add `category_spending_pie(df)` function in charts.py — pie/donut chart of expenses by category with "Uncategorized" slice
- [ ] 4.2 Create `_dashboard_categories.html` partial with pie chart and category dropdown
- [ ] 4.3 Add `GET /dashboard/categories` endpoint that accepts time range params and optional `category_id`, returns the partial

## 5. Category Drill-Down

- [ ] 5.1 Add category drill-down section to `_dashboard_categories.html` — income/expense totals and top 10 transactions table
- [ ] 5.2 Wire category dropdown `hx-get` to re-render drill-down section with selected category
- [ ] 5.3 Include "Uncategorized" option in the dropdown when uncategorized transactions exist

## 6. Account Drill-Down

- [ ] 6.1 Create `_dashboard_accounts.html` partial with account dropdown
- [ ] 6.2 Add `GET /dashboard/accounts` endpoint that accepts time range params and optional `account_id`, returns the partial
- [ ] 6.3 Add account drill-down section: balance at end of period, income/expenses/net stats

## 7. Account Charts

- [ ] 7.1 Add `account_monthly_balance(df, starting_balance_cents)` function in charts.py — cumulative monthly balance line chart
- [ ] 7.2 Add `account_top_externals(df)` function in charts.py — horizontal bar chart of top external accounts
- [ ] 7.3 Wire account charts into `_dashboard_accounts.html` drill-down section

## 8. Polish and Verify

- [ ] 8.1 Verify time range changes re-render the active tab correctly
- [ ] 8.2 Verify tab switches preserve the current time range
- [ ] 8.3 Run `just fmt` and `just lint`
