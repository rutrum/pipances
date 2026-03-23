# Proposal: Data Page Sections (Phase 3 of 3)

## Problem

After phase 2 creates the Data page layout with sidebar, only Internal Accounts, Categories, and Transactions sections exist. External accounts, importers, and import history have no UI representation. Users can't see which external accounts exist, what importers are available, or review past imports.

## Solution

Add the remaining Data page sections:

- **External Accounts** (`/data/external-accounts`): Read-only table listing all external accounts with transaction counts, each linking to `/explore?external=X`
- **Importers** (`/data/importers`): Read-only table listing discovered importer files from the `importers/` directory, showing name and filename
- **Import History** (`/data/imports`): Read-only table listing all imports with institution, filename, timestamp, and row count

Also add [Explore] links to Internal Accounts rows and Categories rows, so every entity type can drill down into the Explore page.

## Scope

- New `/data/external-accounts` route and partial template
- New `/data/importers` route and partial template
- New `/data/imports` route and partial template
- Add [Explore] link column to internal accounts table rows
- Add [Explore] link column to categories table rows
- Add transaction count column to categories list
- Update sidebar menu to include all sections (some may have been placeholders from phase 2)

## Capabilities

### New Capabilities
- `external-account-browsing`: View all external accounts with transaction counts and Explore links
- `importer-listing`: View discovered importer files
- `import-history`: View past imports with metadata

### Modified Capabilities
- `account-management`: Add Explore link per account row
- `data-page`: Complete all sidebar sections

## Impact

- New: `_data_external_accounts.html`, `_data_importers.html`, `_data_imports.html` partials
- Modified: `routes/settings.py` (or renamed data route file) — new GET endpoints, `_account_row.html` (add Explore link), `_category_row.html` (add Explore link + txn count), sidebar menu template
- No model changes needed — external accounts are already in the Account table with kind=external, imports are in the Import table
