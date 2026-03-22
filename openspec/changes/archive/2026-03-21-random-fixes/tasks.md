## 1. Nav Bar Active State

- [x] 1.1 Update `_navbar.html`: replace manual `font-bold border-b-2 border-primary text-primary` with DaisyUI `active` class on the `<a>` element

## 2. Amount Column Cleanup

- [x] 2.1 Update `_inbox_row.html`: remove `$` prefix from amount, add `text-right` to amount `<td>`
- [x] 2.2 Update `_txn_row.html`: remove `$` prefix from amount, add `text-right` to amount `<td>`
- [x] 2.3 Update inbox table header: change "Amount" to indicate currency unit (e.g. "Amount ($)")
- [x] 2.4 Update transactions table header in `_txn_table_body.html`: change amount sort_header label to indicate currency unit

## 3. ML Indicator Blue Dot

- [x] 3.1 Update `_inbox_row.html`: replace `bg-info/10 rounded px-1` on description/category/external spans with absolutely-positioned blue dot; ensure `<td>` has left padding for dot space
- [x] 3.2 Verify blue dot disappears after user edits a field (ml_confidence cleared on PATCH already handles this)

## 4. Click-to-Edit Improvements

- [x] 4.1 Update `_inbox_row.html`: replace `badge badge-ghost badge-sm` "click to edit" placeholders with `italic text-base-content/40` styled text
- [x] 4.2 Update `_combo_edit.html`: change input from `input input-bordered input-sm` to `input input-ghost input-sm`

## 5. Custom Date Range Inline Layout

- [x] 5.1 Update `_txn_date_range.html`: change layout to single flex row with `flex-wrap` so custom date inputs appear to the right of preset buttons

## 6. Inbox Pagination

- [x] 6.1 Create `_inbox_pagination.html` partial (based on `_pagination.html` but targeting `/inbox` and `#inbox-table`)
- [x] 6.2 Update `/inbox` endpoint in `main.py`: accept `page` and `page_size` params, apply LIMIT/OFFSET, return total count/pages
- [x] 6.3 Include `_inbox_pagination.html` in inbox response (render via OOB swap for HTMX, inline for full page)
- [x] 6.4 Update `inbox.html`: add hidden inputs for page/page_size state in the filter bar

## 7. Inbox Sorting

- [x] 7.1 Update `inbox.html`: add sortable column headers for Date, Amount, Description with sort indicators
- [x] 7.2 Update `/inbox` endpoint: accept `sort` and `dir` params, apply ORDER BY accordingly
- [x] 7.3 Update `inbox.html`: add hidden inputs for sort/dir state in the filter bar

## 8. Filter Persistence (URL State)

- [x] 8.1 Add `hx-push-url="true"` to inbox filter/sort/pagination HTMX triggers (filter bar inputs, sort headers, pagination controls)
- [x] 8.2 Update `/inbox` GET endpoint: read filter/sort/page query params, apply them to the initial query, pass values to template for pre-populating controls
- [x] 8.3 Add `hx-push-url="true"` to transactions filter/sort/pagination HTMX triggers (date range, column filters, sort headers, pagination)
- [x] 8.4 Update `/transactions` GET endpoint: read filter/sort/page query params on full page load, pass to template for pre-populating controls and initial query
- [x] 8.5 Verify: changing a filter updates URL; refreshing the page restores the same filtered view

## 9. Verification

- [x] 9.1 Run `just fmt` and `just lint` to ensure code quality
- [x] 9.2 Browser test: inbox pagination, sorting, filter persistence on refresh
- [x] 9.3 Browser test: transactions filter persistence on refresh, custom date range layout
- [x] 9.4 Browser test: ML blue dot appears for predicted fields, disappears after edit (no ML data in seed; template logic verified)
- [x] 9.5 Browser test: click-to-edit shows italic grey placeholder, ghost input on edit
- [x] 9.6 Browser test: nav bar active state uses DaisyUI styling
