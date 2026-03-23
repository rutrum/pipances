# Proposal: Explore Page (Phase 1 of 3)

## Problem

The app has separate Dashboard (charts/stats) and Transactions (table) pages that show overlapping data but can't be used together. There's no way to see charts scoped to a specific account or category, and the transaction table lacks analytical context. Users have to mentally bridge two pages.

## Solution

Create a unified `/explore` page that combines the dashboard charts and the transaction table into one filterable view. Any combination of filters (internal account, external account, category) + date range applies to both the charts and the table simultaneously.

Delete the existing `/dashboard` and `/transactions` routes. (Transactions table will be re-added under `/data/transactions` in phase 2.)

Update the navbar: replace "Dashboard" and "Transactions" links with a single "Explore" link.

## Scope

- New `/explore` route and template with: date range selector, filter dropdowns, stats row, charts (monthly income/expenses, top expenses, weekly spending), and paginated/sortable transaction table
- Reuse existing chart functions from `charts.py` and transaction table partials
- Delete `/dashboard` route, `dashboard.html`, and dashboard tab partials (`_dashboard_summary.html`, `_dashboard_categories.html`, `_dashboard_accounts.html`, `_dashboard_date_range.html`)
- Delete `/transactions` GET route from the transactions router (keep PATCH/edit endpoints)
- Delete `transactions.html` template
- Update navbar: remove Dashboard and Transactions links, add Explore
- Show all transactions (approved + pending), not just approved
- Deep-linkable: `/explore?internal=X&category=Y&preset=ytd` restores the full filter state

## Capabilities

### New Capabilities
- `explore`: Unified filtered view with charts + transaction table

### Modified Capabilities
- `navigation`: Replace Dashboard and Transactions links with Explore

### Removed Capabilities
- `dashboard`: Absorbed into explore (charts + stats)
- `transaction-browsing`: Absorbed into explore (table) and later into data page (phase 2)

## Impact

- New: `routes/explore.py`, `explore.html`, `_explore_content.html` (HTMX partial)
- Modified: `_navbar.html`, `main.py` (router registration), `charts.py` (if any adaptation needed)
- Deleted: `routes/dashboard.py`, `dashboard.html`, `_dashboard_*.html` templates, `transactions.html`, GET `/transactions` route
- Reused: `_txn_table_body.html`, `_txn_row.html`, `_txn_date_range.html`, `_pagination.html`, `charts.py` functions
