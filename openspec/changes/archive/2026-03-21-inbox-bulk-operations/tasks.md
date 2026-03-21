## 1. Selection checkboxes

- [x] 1.1 Add a selection checkbox to each row in `_inbox_row.html` (leftmost element, `class="select-txn"`, `data-txn-id`)
- [x] 1.2 Add a "select all" checkbox in the table header
- [x] 1.3 Add inline JS in `inbox.html` for select-all toggle (check/uncheck all visible `.select-txn` checkboxes) and selection count tracking

## 2. Bulk toolbar

- [x] 2.1 Add a bulk toolbar `<div>` above the table in `inbox.html`, always visible with inputs/buttons disabled when no rows are selected
- [x] 2.2 Add selection count display ("N selected") in the toolbar, showing "0 selected" when nothing is checked
- [x] 2.3 Add category text input in the toolbar (stages a value for bulk apply)
- [x] 2.4 Add external account text input in the toolbar (stages a value for bulk apply)
- [x] 2.5 Add description text input in the toolbar
- [x] 2.6 Add "Apply" button that collects non-empty field values and selected transaction IDs, sends to bulk endpoint
- [x] 2.7 Add "Approve Selected" button in the toolbar

## 3. Bulk edit endpoint

- [x] 3.1 Create `PATCH /transactions/bulk` endpoint accepting `ids` list and optional `description`, `category`, `external` fields
- [x] 3.2 Implement partial-apply logic: only update fields present and non-empty in the request body, skip empty/missing fields
- [x] 3.3 Reuse existing resolve-or-create logic for category and external account
- [x] 3.4 Return updated row partials using OOB swaps (`hx-swap-oob="outerHTML:#txn-{id}"`) for each affected row

## 4. Bulk approve

- [x] 4.1 Handle `marked_for_approval` in the bulk endpoint — set to true only on rows where description is set, silently skip incomplete rows
- [x] 4.2 Return re-rendered rows with updated approve button states via OOB swaps

## 5. Filter bar

- [x] 5.1 Add filter bar HTML in `inbox.html` above the table: two date inputs (from/to), internal account `<select>`, import batch `<select>`, and a "Clear" button
- [x] 5.2 Populate the internal account dropdown with all internal accounts (query in `inbox_page`)
- [x] 5.3 Populate the import batch dropdown with recent imports (institution + date, query in `inbox_page`)
- [x] 5.4 Create `GET /inbox/rows` endpoint that returns only the filtered `<tbody>` content (row partials)
- [x] 5.5 Add query parameter filtering to the rows endpoint: `date_from`, `date_to`, `internal_id`, `import_id` with `.where()` clauses
- [x] 5.6 Wire filter inputs to `hx-get="/inbox/rows"` with `hx-trigger="change"`, targeting the `<tbody>`
- [x] 5.7 Use `hx-include` on filter inputs so filter state is preserved across other HTMX requests (commit, bulk edit)
- [x] 5.8 Implement "Clear" button to reset all filter inputs and re-fetch unfiltered rows

## 6. Filter persistence across commits

- [x] 6.1 Ensure the commit flow includes filter params (via `hx-include`) so the re-rendered tbody respects active filters after commit

## 7. Testing and polish

- [x] 7.1 Browser-test: select multiple rows, bulk set category, verify only category changes (description/external untouched)
- [x] 7.2 Browser-test: select multiple rows, bulk approve, verify incomplete rows are skipped
- [x] 7.3 Browser-test: apply filters, verify table updates; commit with filters active, verify filters persist
- [x] 7.4 Browser-test: select all with filters, verify only filtered rows are selected
- [x] 7.5 Run `just fmt` and `just lint`
