## Why

The current seed data is too simple to exercise real-world scenarios: only 3 internal accounts, 6 months of data, one-sided transfers, and a single importer. We need a richer test bed with multiple banks, credit cards, account closures, paired transfers, and a second importer with a different CSV format to properly validate the system.

## What Changes

- Expand seed data from 6 months to 12 months (Oct 2025 - Sep 2026)
- Add 6 internal accounts across two banks:
  - First National: Checking + Savings (active Oct 2025 - Jan 2026, closed Feb 2026)
  - Metro Credit Union: Checking + Savings (opened Feb 2026, active through Sep 2026)
  - Chase Visa (full year)
  - Amex Blue Cash (opened Dec 2025)
- Generate proper transfer pairs (both sides of each transfer):
  - Monthly savings-to-checking transfers
  - Monthly checking-to-credit-card payments
  - One-time bank switchover transfers (First National to Metro CU in Feb 2026)
- Closed accounts marked with `active=False`
- Add a second importer (`metro_cu.py`) with split debit/credit CSV format
- Add corresponding test CSV (`test_metro_cu.csv`) covering 2 months of Metro CU data
- Scale to ~200-300 approved transactions with a small pending inbox (~8-10)

## Capabilities

### New Capabilities

_(none — this change is purely test data and a new importer, no new user-facing capabilities)_

### Modified Capabilities

_(none — no spec-level behavior changes)_

## Impact

- `scripts/seed.py` — major rewrite to support expanded account set, transfer pairs, bank switchover
- `importers/metro_cu.py` — new importer file
- `test_metro_cu.csv` — new test CSV in project root
- `importers/example.py` — may need minor updates to align with renamed bank
- `test_export.csv` — may need updates to align with new account naming
