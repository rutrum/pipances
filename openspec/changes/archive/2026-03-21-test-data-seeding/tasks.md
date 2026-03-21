## 1. Seed Script

- [x] 1.1 Create `scripts/seed.py` with deterministic data generation using `random.seed(42)` and async ORM
- [x] 1.2 Seed internal accounts: Checking, Savings, Credit Card (with starting balances and balance dates)
- [x] 1.3 Seed categories: Groceries, Dining, Entertainment, Utilities, Rent, Transportation, Shopping, Income, Transfers
- [x] 1.4 Seed external accounts: ~15-20 realistic merchants (Kroger, Netflix, Shell, etc.)
- [x] 1.5 Seed ~80 approved transactions (Oct 2025 – Mar 2026) with recurring patterns (rent on 1st, paychecks on 1st/15th, monthly subscriptions) and random transactions, ~10% uncategorized
- [x] 1.6 Seed ~8 pending transactions (recent dates) for inbox testing
- [x] 1.7 Create import record(s) for seeded transactions

## 2. Justfile Recipes

- [x] 2.1 Add `just reset-db` recipe that deletes `financial_pipeline.db`
- [x] 2.2 Add `just seed` recipe that runs `reset-db` then `uv run python scripts/seed.py`

## 3. Test CSV

- [x] 3.1 Create `test_export.csv` in project root with ~10 April 2026 transactions in example importer format (date, amount, description)
- [x] 3.2 Delete `importers/sample.csv` and `importers/test_data.csv`

## 4. "All" Date Preset

- [x] 4.1 Add "All" button to `_date_range.html` preset bar
- [x] 4.2 Update `_compute_date_range` to return `None, None` for the "all" preset
- [x] 4.3 Update `transactions_page` to skip date WHERE clauses when date range is None

## 5. Verification

- [x] 5.1 Run `just seed` and verify the app starts with seeded data
- [x] 5.2 Browser test: verify dashboard shows charts with seeded data
- [x] 5.3 Browser test: verify inbox shows pending transactions
- [x] 5.4 Browser test: verify transactions page shows approved transactions with "All" preset and category filter working
