## Why

There's no way to get the app into a known data state for testing. Browser testing of features like dashboard charts, transaction filters, and category breakdowns depends on having realistic data across the right date ranges. The current test CSVs contain 2024 data which falls outside default filters (YTD 2026), making it impossible to verify many features. A deterministic seed script and updated test CSV are needed to make testing reliable and repeatable.

## What Changes

- New `scripts/seed.py` that populates the database with realistic fabricated data via the ORM:
  - Internal accounts (Checking, Savings, Credit Card)
  - Categories (Groceries, Dining, Entertainment, Utilities, Rent, Transportation, Shopping, Income, Transfers)
  - ~15-20 external accounts (realistic merchant names)
  - ~80 approved transactions (Oct 2025 – Mar 2026) with recurring patterns (rent, paychecks, subscriptions)
  - ~8 pending transactions for inbox testing
  - ~10% of approved transactions left uncategorized
- New `just reset-db` recipe: deletes `financial_pipeline.db`
- New `just seed` recipe: runs `reset-db` then `seed.py`
- Replace `importers/test_data.csv` with `test_export.csv` in the project root containing April 2026 data (~10 transactions) for import testing
- Delete `importers/sample.csv` (redundant)
- Add "All" preset to the transactions page date range filter, showing all approved transactions unbounded by date

## Capabilities

### New Capabilities
- `test-data-seeding`: Seed script, justfile recipes, and test CSV for reproducible test data

### Modified Capabilities
- `transaction-browsing`: Add "All" date preset to show transactions without date bounds

## Impact

- **New files**: `scripts/seed.py`, `test_export.csv`
- **Deleted files**: `importers/sample.csv`, `importers/test_data.csv`
- **Modified files**: `justfile` (new recipes), `_date_range.html` (new button), `main.py` (handle "all" preset)
