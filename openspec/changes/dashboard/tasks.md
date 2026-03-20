## 1. Navbar Update

- [x] 1.1 Add "Dashboard" link to `_navbar.html`

## 2. Charts Module

- [x] 2.1 Create `src/financial_pipeline/charts.py` with `compute_stats(df)` — returns dict with total_income, total_expenses, net, net_total (all in cents)
- [x] 2.2 Add `monthly_income_expenses_chart(df)` — Polars aggregation by year-month, Altair grouped bar chart, returns Vega-Lite JSON string
- [x] 2.3 Add `top_expenses_chart(df, n=10)` — Polars group-by external account, sum expenses, top N, Altair horizontal bar chart, returns JSON string
- [x] 2.4 Add `weekly_spending_chart(df)` — Polars group-by ISO week, sum expenses, Altair line chart, returns JSON string

## 3. Dashboard Route

- [x] 3.1 Create `GET /dashboard` route — query approved transactions, convert to Polars DataFrame, call chart functions, pass stats + chart specs to template
- [x] 3.2 Handle empty state — if no approved transactions, render message with link to upload

## 4. Dashboard Template

- [x] 4.1 Create `dashboard.html` — extends base, DaisyUI `stats` component for summary cards, 2-column grid for charts
- [x] 4.2 Add Vega-Embed CDN scripts (vega, vega-lite, vega-embed) to dashboard template
- [x] 4.3 Embed chart specs in inline `<script>` blocks using `vegaEmbed()` calls

## 5. CSS and Verification

- [x] 5.1 Rebuild Tailwind CSS (`just css`)
- [x] 5.2 Verify dashboard loads at /dashboard with summary stats and all three charts
- [x] 5.3 Verify empty state when no approved transactions exist
- [x] 5.4 Verify navbar shows Dashboard link on all pages
