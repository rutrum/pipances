## 1. Create Shared Macro Template

- [ ] 1.1 Create `src/pipances/templates/_table_macros.html` with `sort_header()` macro extracted from `_explore_table.html`
- [ ] 1.2 Add `filter_header()` macro to `_table_macros.html` (parameters: column, label, accounts, current_filter, endpoint, target, include_selector)
- [ ] 1.3 Verify macros work in isolation by checking template syntax with `just lint`

## 2. Create Unified Transaction Table Template

- [ ] 2.1 Create `src/pipances/templates/_transaction_table.html` with:
  - Filter state container (`<div id="{{ filters_container_id }}">`)
  - No-data alert
  - Table with headers using `sort_header()` and `filter_header()` macros
  - Category filter dropdown (with Uncategorized option)
  - Transaction rows (`_txn_row.html`)
  - Pagination (via `_pagination.html`)
- [ ] 2.2 Document required context variables as comments at the top of the template
- [ ] 2.3 Test template syntax with `just lint`

## 3. Create Shared Date Range Template

- [ ] 3.1 Create `src/pipances/templates/_transaction_date_range.html` with date preset buttons and custom date inputs
- [ ] 3.2 Extract date range code from `_data_transactions.html` into the new template
- [ ] 3.3 Ensure it accepts parameters: endpoint, target, include_selector, preset, date_from, date_to
- [ ] 3.4 Test template syntax with `just lint`

## 4. Update Explore Route

- [ ] 4.1 Update `src/pipances/routes/explore.py` to pass consistent context to templates:
  - `endpoint`: "/explore"
  - `target`: "#explore-content"
  - `include_selector`: "#explore-filters, #explore-pagination-page-size"
  - `filters_container_id`: "explore-filters"
  - `pagination_id`: "explore-pagination"
- [ ] 4.2 Verify all required context variables (filters, sorts, pagination_info, etc.) are passed

## 5. Update Data Route

- [ ] 5.1 Update `src/pipances/routes/data.py` `data_transactions_page()` to pass consistent context:
  - `endpoint`: "/data/transactions"
  - `target`: "#data-content"
  - `include_selector`: "#data-txn-filters, #data-transactions-pagination-page-size"
  - `filters_container_id`: "data-txn-filters"
  - `pagination_id`: "data-transactions-pagination"
- [ ] 5.2 Verify date range context (preset, date_from, date_to) is passed
- [ ] 5.3 Ensure all filter/sort/pagination context variables match current implementation

## 6. Simplify Explore Table Template

- [ ] 6.1 Replace `_explore_table.html` content with single include: `{% include "_transaction_table.html" %}`
- [ ] 6.2 Remove `sort_header()` and `filter_header()` macro definitions from `_explore_table.html`
- [ ] 6.3 Remove the manual table structure (table/thead/tbody/pagination) — all in `_transaction_table.html` now

## 7. Simplify Data Transactions Template

- [ ] 7.1 Remove date range section from `_data_transactions.html` (moved to `_transaction_date_range.html`)
- [ ] 7.2 Remove `sort_header()` and `filter_header()` macro definitions from `_data_transactions.html`
- [ ] 7.3 Replace remaining content with single include: `{% include "_transaction_table.html" %}`
- [ ] 7.4 Verify `_data_transactions.html` is now minimal

## 8. Update Inbox Header Template

- [ ] 8.1 Update `src/pipances/templates/_inbox_thead.html` to import `_table_macros.html`
- [ ] 8.2 Replace hand-coded sort headers with `sort_header()` macro calls
  - For each sortable column (date, amount, description): call `table_macros.sort_header(column, label, '/inbox', '#inbox-table', '#filter-bar, #pagination-page-size', width_class)`
- [ ] 8.3 Test that sort headers still work in browser

## 9. Manual Browser Testing

- [x] 9.1 Start dev server with `just serve`
- [x] 9.2 Test Explore page: verify sorting and filtering work (click sort headers, use filter dropdowns, change date presets)
- [x] 9.3 Test Data/Transactions page: verify sorting, filtering, date presets, and custom date range work
- [x] 9.4 Test Inbox: verify sort headers work and sorting functions correctly
- [x] 9.5 Verify pagination works on all three views
- [x] 9.6 Verify no console errors or HTMX issues
- [x] BUGFIX: Fixed sort arrows not showing and sort toggle not working (macro parameter issue)

## 10. Automated Testing & Code Quality

- [x] 10.1 Run `just lint` to check template syntax across all modified templates
- [x] 10.2 Run `just fmt` to auto-format modified files
- [x] 10.3 Run `just check` for full CI-style verification
- [x] 10.4 Verify no regressions: confirm existing unit tests pass

## 11. Documentation & Cleanup

- [x] 11.1 Add a comment to `_table_macros.html` explaining macro parameters and usage
- [x] 11.2 Add a comment to `_transaction_table.html` documenting all required context variables
- [x] 11.3 Update any team documentation or component library (if applicable)
- [x] 11.4 Consider creating a follow-up task for consolidating the Category filter into a macro (noted in design as deferred)

## 12. Final Verification

- [x] 12.1 Confirm all templates have been consolidated as designed
- [x] 12.2 Double-check that Inbox table is still separate and functional (was not merged into unified table)
- [x] 12.3 Run `just serve` one more time and spot-check all three transaction-viewing pages
- [x] 12.4 Ready to close the change
