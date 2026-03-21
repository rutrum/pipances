## Why

The app can ingest, review, and browse transactions, but there's no way to see the big picture. A dashboard page provides at-a-glance summary statistics and visual charts computed from all approved transactions, giving the user immediate insight into their financial health — income, expenses, spending patterns, and where money goes.

## What Changes

- Add a `/dashboard` page with summary stat cards and Altair (Vega-Lite) charts
- Summary cards: Total Income, Total Expenses, Net (income - expenses), Net Total (all-time sum)
- Chart: Monthly income vs. expenses (side-by-side grouped bar chart)
- Chart: Top 10 expenses by external account (horizontal bar chart)
- Chart: Weekly spending trend (per-week expense totals as a line chart)
- All aggregation done server-side with Polars; charts rendered client-side via Vega-Embed from Altair-generated JSON specs
- No date filtering for now — dashboard covers all approved transactions
- Add "Dashboard" link to the navbar

## Capabilities

### New Capabilities
- `dashboard`: Summary statistics and charts for all approved transactions

### Modified Capabilities
- `navigation`: Add Dashboard link to the navbar

## Impact

- `main.py` — new GET `/dashboard` route
- New module for chart/stat computation (Polars aggregation + Altair chart specs)
- Templates — new `dashboard.html`
- `_navbar.html` — add Dashboard link
- New frontend dependency: Vega-Embed CDN script for rendering Altair charts
- CSS rebuild for new DaisyUI classes (stat cards, grid layout)
