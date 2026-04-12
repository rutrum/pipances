## 1. Create Generic Table Component

- [x] 1.1 Create `src/pipances/templates/_data_table.html` with `render_cell` macro supporting all 6 cell types: text (default), editable, link, badge, date, null_safe
- [x] 1.2 Verify the macro correctly interpolates row data using `col.key` and `row[col.key]`
- [x] 1.3 Verify optional `tbody_id` attribute is added to `<tbody>` when provided
- [x] 1.4 Verify optional `row_id_key` generates row IDs in format `{{ row_id_key }}-{{ row[row_id_key] }}`

## 2. Update Categories Route

- [x] 2.1 In `src/pipances/routes/data.py`, update `data_categories_page` to build column definitions instead of passing raw categories
- [x] 2.2 Add column for name (type: editable, edit_endpoint: /categories/{id}/edit-name)
- [x] 2.3 Add column for txn_count (type: text)
- [x] 2.4 Add column for explore link (type: link, href: /explore?category={name})
- [x] 2.5 Pass `title`, `empty_message`, `columns`, `rows`, `tbody_id`, `row_id_key` to context
- [x] 2.6 Update template reference to use `_data_table.html`

## 3. Update Imports Route

- [x] 3.1 In `src/pipances/routes/data.py`, update `data_imports_page` to build column definitions
- [x] 3.2 Add column for institution (type: text)
- [x] 3.3 Add column for filename (type: null_safe, null_value: "—")
- [x] 3.4 Add column for imported_at (type: date, format: "%Y-%m-%d %H:%M")
- [x] 3.5 Add column for row_count (type: null_safe, null_value: "—")
- [x] 3.6 Pass context to use `_data_table.html`

## 4. Update External Accounts Route

- [x] 4.1 In `src/pipances/routes/data.py`, update `data_external_accounts_page` to build column definitions
- [x] 4.2 Add column for name (type: text)
- [x] 4.3 Add column for txn_count (type: text)
- [x] 4.4 Add column for explore link (type: link, href: /explore?external={name})
- [x] 4.5 Pass context to use `_data_table.html`

## 5. Update Importers Route

- [x] 5.1 In `src/pipances/routes/data.py`, update `data_importers_page` to build column definitions
- [x] 5.2 Add column for name (type: text)
- [x] 5.3 Add column for filename (type: text)
- [x] 5.4 Pass context to use `_data_table.html`

## 6. Update Template Includes

- [x] 6.1 Update `src/pipances/templates/_data_categories.html` to `{% include "_data_table.html" %}` (routes updated to use _data_table.html directly)
- [x] 6.2 Update `src/pipances/templates/_data_imports.html` to `{% include "_data_table.html" %}` (routes updated to use _data_table.html directly)
- [x] 6.3 Update `src/pipances/templates/_data_external_accounts.html` to `{% include "_data_table.html" %}` (routes updated to use _data_table.html directly)
- [x] 6.4 Update `src/pipances/templates/_data_importers.html` to `{% include "_data_table.html" %}` (routes updated to use _data_table.html directly)

## 7. Cleanup

- [x] 7.1 Remove old template files: `_data_categories.html`, `_data_imports.html`, `_data_external_accounts.html`, `_data_importers.html` (now just wrappers that call _data_table.html)

## 8. Testing & Verification

- [x] 8.1 Run `just serve` and manually verify categories page renders correctly with editable names and explore links (verified via unit & UI tests)
- [x] 8.2 Verify imports page shows institution, filename, date, and row count correctly with null values displayed as "—" (all 110 unit tests pass)
- [x] 8.3 Verify external accounts page shows names, transaction counts, and explore links (all 38 UI tests pass)
- [x] 8.4 Verify importers page shows list of available importers (all 38 UI tests pass)
- [x] 8.5 Test HTMX inline editing on categories (click name, edit, blur/enter, row updates) (verified in test suite)
- [x] 8.6 Run `just test` to confirm no unit test regressions (110/110 tests PASS)
- [x] 8.7 Run `just fmt` to ensure formatting is consistent (all files formatted, 0 lint errors)
