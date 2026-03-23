## 1. Rewrite seed script

- [x] 1.1 Define expanded internal accounts (6 accounts across two banks + two credit cards) with correct active flags and balance dates
- [x] 1.2 Add transfer-related external accounts (e.g. "Transfer" accounts for each institution pair)
- [x] 1.3 Refactor transaction generation to route spending to the correct bank based on the month (First National Oct-Jan, Metro CU Feb-Sep)
- [x] 1.4 Generate paired transfer transactions (savings-to-checking monthly, checking-to-credit-card payments, bank switchover lump transfers in Feb 2026)
- [x] 1.5 Expand timeline to 12 months (Oct 2025 - Sep 2026) with ~200-300 approved transactions
- [x] 1.6 Mark First National accounts as `active=False` after the switchover month
- [x] 1.7 Generate a small pending inbox batch (~8-10 transactions from most recent month)
- [x] 1.8 Create separate Import records per institution for realism

## 2. Metro CU importer

- [x] 2.1 Create `importers/metro_cu.py` with split debit/credit CSV parsing (columns: Transaction Date, Debit, Credit, Memo; date format MM/DD/YYYY)
- [x] 2.2 Create `test_metro_cu.csv` with ~2 months of Metro CU data (Feb-Mar 2026)

## 3. Update existing test data

- [x] 3.1 Update `test_export.csv` to align with renamed/expanded account context if needed
- [x] 3.2 Review `importers/example.py` for any needed adjustments (IMPORTER_NAME, etc.)

## 4. Verify

- [x] 4.1 Run `just seed` and verify expected account/transaction counts in output
- [x] 4.2 Run `just serve` and visually confirm data looks correct in the UI (accounts page, transaction browsing, explore page)
- [x] 4.3 Test importing `test_metro_cu.csv` through the import workflow
- [x] 4.4 Run `just check` to ensure no lint/format issues
