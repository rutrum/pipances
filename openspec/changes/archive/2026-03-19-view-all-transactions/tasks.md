## 1. Navbar Update

- [x] 1.1 Add "Transactions" link to `_navbar.html`

## 2. Route and Query Logic

- [x] 2.1 Create `GET /transactions` route in `main.py` — accepts query params: `date_from`, `date_to`, `sort`, `dir`, `internal`, `external`, `page`, `page_size`
- [x] 2.2 Build SQLAlchemy query with dynamic filtering (date range, account filters), sorting, and offset/limit pagination
- [x] 2.3 Detect HTMX requests via `HX-Request` header — return full page or partial (tbody + pagination)

## 3. Date Range Widget

- [x] 3.1 Create `_date_range.html` partial — DaisyUI `join` button group with YTD, Last Month, Last 3 Months presets, plus Custom toggle
- [x] 3.2 Implement Custom mode: toggling shows two date inputs and Apply button
- [x] 3.3 Wire HTMX: preset clicks and Apply fire requests with `date_from`/`date_to`, reset page to 1

## 4. Transactions Table

- [x] 4.1 Create `transactions.html` page template — extends base, includes date range widget, table, and pagination
- [x] 4.2 Create `_txn_row.html` partial — read-only row with date, formatted amount (color-coded), description, external account, internal account
- [x] 4.3 Implement sortable column headers — click toggles sort, active column shows direction indicator (▲/▼)
- [x] 4.4 Implement account column filter dropdowns — DaisyUI dropdown in `<th>` with account name list, selecting filters and triggers HTMX request

## 5. Pagination

- [x] 5.1 Create `_pagination.html` partial — prev/next buttons, "Page X of Y" indicator, page size selector (25/50/100)
- [x] 5.2 Wire HTMX: pagination controls include all current filter/sort state, update tbody + pagination together

## 6. CSS and Verification

- [x] 6.1 Rebuild Tailwind CSS (`just css`)
- [x] 6.2 Verify full page load at /transactions with default YTD filter and date-descending sort
- [x] 6.3 Verify date range presets and custom range filter transactions correctly
- [x] 6.4 Verify column sorting toggles and account filter dropdowns work
- [x] 6.5 Verify pagination navigates pages while preserving filters/sort
- [x] 6.6 Verify empty state message when no transactions match filters
