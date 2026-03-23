## 1. Create Explore Route

- [x] 1.1 Create `src/financial_pipeline/routes/explore.py` with `GET /explore` endpoint
- [x] 1.2 Parse query params: `preset`, `date_from`, `date_to`, `internal`, `external`, `category`, `sort`, `dir`, `page`, `page_size`
- [x] 1.3 Query all transactions (approved + pending) with filters applied, joining internal/external/category relationships
- [x] 1.4 Compute total count for pagination (separate count query with same filters)
- [x] 1.5 For charts: convert all matching transactions to Polars DataFrame, call `compute_stats()`, `monthly_income_expenses_chart()`, `top_expenses_chart()`, `weekly_spending_chart()`
- [x] 1.6 For table: apply pagination (LIMIT/OFFSET) to get the current page of transactions
- [x] 1.7 Fetch account and category lists for filter dropdowns
- [x] 1.8 Return full page for direct navigation, or HTMX partial for filter/sort/pagination interactions

## 2. Create Explore Template

- [x] 2.1 Create `explore.html` extending `base.html` — page title "Explore", includes date range selector, filter row, stats, charts, and transaction table
- [x] 2.2 Date range selector: reuse the preset button pattern from dashboard/transactions (YTD, Last Month, Last 3 Months, Last Year, All, Custom)
- [x] 2.3 Filter row: three `<select>` dropdowns for internal account, external account, category — each triggers HTMX reload of content
- [x] 2.4 Stats row: DaisyUI `stats` component showing Income, Expenses, Net, Count
- [x] 2.5 Charts section: monthly income/expenses (full width), top expenses + weekly spending (2-column grid), with Vega-Embed rendering
- [x] 2.6 Transaction table: include `_txn_table_body.html` partial (reuse existing)
- [x] 2.7 Create `_explore_content.html` partial for HTMX updates (stats + charts + table body, returned on HX-Request)

## 3. HTMX Interactions

- [x] 3.1 Filter dropdowns: `hx-get="/explore"` with `hx-include` to send all current state (date range, filters, sort, page)
- [x] 3.2 Date range presets: same pattern, include all state
- [x] 3.3 Sorting and pagination: same pattern, preserve filters
- [x] 3.4 OOB swap for date range buttons to reflect active preset
- [x] 3.5 Handle empty state: if no transactions match, show info message instead of charts/table

## 4. Delete Old Routes and Templates

- [x] 4.1 Delete `routes/dashboard.py` and remove router registration from `main.py`
- [x] 4.2 Delete dashboard templates: `dashboard.html`, `_dashboard_summary.html`, `_dashboard_categories.html`, `_dashboard_accounts.html`, `_dashboard_date_range.html`
- [x] 4.3 Remove `GET /transactions` endpoint from `routes/transactions.py` (keep PATCH and edit endpoints)
- [x] 4.4 Delete `transactions.html` template
- [x] 4.5 Register explore router in `main.py`

## 5. Navbar Update

- [x] 5.1 Update `_navbar.html`: remove Dashboard and Transactions links, add Explore link with icon

## 6. Verification

- [x] 6.1 Rebuild CSS (`just css`)
- [x] 6.2 Verify `/explore` loads with stats, charts, and transaction table
- [x] 6.3 Verify filter dropdowns filter both charts and table
- [x] 6.4 Verify date range presets work
- [x] 6.5 Verify pagination and sorting work within filtered results
- [x] 6.6 Verify deep linking: `/explore?category=Groceries` loads with filter pre-selected
- [x] 6.7 Verify empty state when no transactions match filters
- [x] 6.8 Verify old `/dashboard` and `/transactions` URLs return 404
- [x] 6.9 Run `just check` to ensure tests pass and linting is clean
