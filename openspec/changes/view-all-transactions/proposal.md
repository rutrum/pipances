## Why

The app can ingest and approve transactions, but there's no way to browse approved transaction history. Users need a read-only view of all approved transactions with filtering (especially by time), sorting, and pagination to make sense of their financial data. This page also establishes reusable table components (date range widget, pagination, column filters) that future pages (e.g. account drill-downs) can adopt.

## What Changes

- Add a `/transactions` page displaying all approved transactions in a server-side paginated, sortable, filterable table
- Add a date range widget with presets (YTD, Last Month, Last 3 Months) and a custom date range option
- Add sortable column headers (click to toggle sort direction)
- Add spreadsheet-style auto-filter dropdowns on account columns (internal, external)
- Add pagination controls (prev/next, page number, configurable page size)
- All filtering, sorting, and pagination is server-side via HTMX — no client-side JS state
- Add "Transactions" link to the navbar

## Capabilities

### New Capabilities
- `transaction-browsing`: Read-only paginated table of approved transactions with date range filtering, column sorting, and account column filters
- `navigation`: Global navigation bar with links to all major sections (extracted from inbox-review)

### Modified Capabilities
None.

## Impact

- `main.py` — new GET `/transactions` route with query param handling for sort/filter/page
- Templates — new `transactions.html`, reusable partials: `_date_range.html`, `_pagination.html`, `_txn_row.html`
- `_navbar.html` — add Transactions link
- CSS rebuild needed for new DaisyUI classes
