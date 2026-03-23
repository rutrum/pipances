## 1. External Accounts Section

- [x] 1.1 Create `GET /data/external-accounts` route — query all accounts with `kind='external'`, join with transaction count (COUNT grouped by external_id)
- [x] 1.2 Create `_data_external_accounts.html` partial — table with columns: Name, Transaction Count, Explore link
- [x] 1.3 Explore link per row: `<a href="/explore?external={{ account.name | urlencode }}">` with Lucide icon

## 2. Importers Section

- [x] 2.1 Create `GET /data/importers` route — scan `importers/` directory for `.py` files (excluding `__pycache__`), import each module, read `IMPORTER_NAME`
- [x] 2.2 Create `_data_importers.html` partial — table with columns: Importer Name, Filename
- [x] 2.3 Handle missing `IMPORTER_NAME` gracefully (show filename as fallback)

## 3. Import History Section

- [x] 3.1 Create `GET /data/imports` route — query all Import records ordered by `imported_at` descending
- [x] 3.2 Create `_data_imports.html` partial — table with columns: Institution, Filename, Imported At (formatted), Row Count

## 4. Add Explore Links to Existing Sections

- [x] 4.1 Update `_account_row.html` — add Explore link column: `<a href="/explore?internal={{ account.name | urlencode }}">`
- [x] 4.2 Update `_data_accounts.html` table header to include the new Explore column
- [x] 4.3 Update `_category_row.html` — add Transaction Count column and Explore link column: `<a href="/explore?category={{ category.name | urlencode }}">`
- [x] 4.4 Update `_data_categories.html` — modify categories query to include transaction counts (LEFT JOIN with COUNT)
- [x] 4.5 Update table headers in `_data_categories.html` for new columns

## 5. Update Sidebar

- [x] 5.1 Ensure all sidebar menu items are active (remove any placeholders/disabled states from phase 2)

## 6. Tests

- [x] 6.1 Test `GET /data/external-accounts` returns 200
- [x] 6.2 Test `GET /data/importers` returns 200 (verifies filesystem scanning works)
- [x] 6.3 Test `GET /data/imports` returns 200
- [x] 6.4 Test external accounts response includes transaction counts when transactions exist
- [x] 6.5 Test categories response includes transaction count and Explore link
- [x] 6.6 Test importer listing handles missing `IMPORTER_NAME` gracefully (falls back to filename)
- [x] 6.7 Test Explore links use correct URL encoding (e.g. "Chase Checking" → `?internal=Chase+Checking`)

## 7. Verification

- [x] 7.1 Verify `/data/external-accounts` shows all external accounts with correct transaction counts
- [x] 7.2 Verify `/data/importers` lists importer files with names
- [x] 7.3 Verify `/data/imports` shows import history in reverse chronological order
- [x] 7.4 Verify Explore links on internal accounts navigate to correctly filtered Explore page
- [x] 7.5 Verify Explore links on external accounts navigate to correctly filtered Explore page
- [x] 7.6 Verify Explore links on categories navigate to correctly filtered Explore page
- [x] 7.7 Verify sidebar navigation works for all new sections
- [x] 7.8 Run `just check`
