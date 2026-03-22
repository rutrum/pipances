## 1. External Accounts Section

- [ ] 1.1 Create `GET /data/external-accounts` route — query all accounts with `kind='external'`, join with transaction count (COUNT grouped by external_id)
- [ ] 1.2 Create `_data_external_accounts.html` partial — table with columns: Name, Transaction Count, Explore link
- [ ] 1.3 Explore link per row: `<a href="/explore?external={{ account.name | urlencode }}">` with Lucide icon

## 2. Importers Section

- [ ] 2.1 Create `GET /data/importers` route — scan `importers/` directory for `.py` files (excluding `__pycache__`), import each module, read `IMPORTER_NAME`
- [ ] 2.2 Create `_data_importers.html` partial — table with columns: Importer Name, Filename
- [ ] 2.3 Handle missing `IMPORTER_NAME` gracefully (show filename as fallback)

## 3. Import History Section

- [ ] 3.1 Create `GET /data/imports` route — query all Import records ordered by `imported_at` descending
- [ ] 3.2 Create `_data_imports.html` partial — table with columns: Institution, Filename, Imported At (formatted), Row Count

## 4. Add Explore Links to Existing Sections

- [ ] 4.1 Update `_account_row.html` — add Explore link column: `<a href="/explore?internal={{ account.name | urlencode }}">`
- [ ] 4.2 Update `_data_accounts.html` table header to include the new Explore column
- [ ] 4.3 Update `_category_row.html` — add Transaction Count column and Explore link column: `<a href="/explore?category={{ category.name | urlencode }}">`
- [ ] 4.4 Update `_data_categories.html` — modify categories query to include transaction counts (LEFT JOIN with COUNT)
- [ ] 4.5 Update table headers in `_data_categories.html` for new columns

## 5. Update Sidebar

- [ ] 5.1 Ensure all sidebar menu items are active (remove any placeholders/disabled states from phase 2)

## 6. Verification

- [ ] 6.1 Verify `/data/external-accounts` shows all external accounts with correct transaction counts
- [ ] 6.2 Verify `/data/importers` lists importer files with names
- [ ] 6.3 Verify `/data/imports` shows import history in reverse chronological order
- [ ] 6.4 Verify Explore links on internal accounts navigate to correctly filtered Explore page
- [ ] 6.5 Verify Explore links on external accounts navigate to correctly filtered Explore page
- [ ] 6.6 Verify Explore links on categories navigate to correctly filtered Explore page
- [ ] 6.7 Verify sidebar navigation works for all new sections
- [ ] 6.8 Run `just check`
