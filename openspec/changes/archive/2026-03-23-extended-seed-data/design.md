## Context

The seed script (`scripts/seed.py`) currently creates 3 internal accounts, ~50 approved transactions across 6 months, and 8 pending inbox items. All transactions route through a single Import record. Transfers are one-sided (only the checking debit, no savings credit). There is one importer (`importers/example.py`) with a simple date/amount/description CSV format.

This is insufficient to test account lifecycle (opening/closing), transfer pair handling, multi-importer workflows, and realistic data volumes.

## Goals / Non-Goals

**Goals:**
- Realistic 12-month dataset with ~200-300 transactions
- Multiple banks with account lifecycle (open, active, closed)
- Proper paired transfers (both sides of every transfer)
- Second importer with a different CSV format (split debit/credit columns)
- Deterministic output (seeded RNG, same as current approach)

**Non-Goals:**
- Changing the Import/Transaction data model
- Adding new UI features
- Modifying the import pipeline logic
- Auto-matching transfer pairs in the application (that's a future feature)

## Decisions

### Account structure

Six internal accounts across two banks plus two credit cards:

| Account | Kind | Active Period | Notes |
|---|---|---|---|
| First National Checking | checking | Oct 2025 - Jan 2026 | Closed Feb 2026 |
| First National Savings | savings | Oct 2025 - Jan 2026 | Closed Feb 2026 |
| Metro CU Checking | checking | Feb 2026 - Sep 2026 | Opens Feb 2026 |
| Metro CU Savings | savings | Feb 2026 - Sep 2026 | Opens Feb 2026 |
| Chase Visa | credit_card | Oct 2025 - Sep 2026 | Full year |
| Amex Blue Cash | credit_card | Dec 2025 - Sep 2026 | Opens Dec 2025 |

Closed accounts use `active=False`. Balance dates set to Sep 30, 2025 for First National accounts (pre-existing), and to the month before opening for Metro CU/Amex.

**Alternative considered:** Using a single bank throughout. Rejected because the switchover scenario exercises account closure, paired transfers between institutions, and is a common real-world pattern.

### Transfer pairs

Every transfer generates two Transaction rows with matching dates and inverse amounts:

- **Savings → Checking** (~$500/month, 25th): debit on savings, credit on checking
- **Checking → Chase Visa** (payment, ~5th): debit on checking, credit on credit card
- **Checking → Amex** (payment, ~8th, starting Jan 2026): debit on checking, credit on credit card
- **Bank switchover** (Feb 2026): large lump transfers from FN Checking → Metro CU Checking and FN Savings → Metro CU Savings

Both sides of each transfer use the same external account (e.g., "Transfer" or the target account name), same date, and inverse amounts. Each side is tied to its respective internal account.

**Alternative considered:** One-sided transfers (current approach). Rejected because paired transfers are part of the system design and must be tested.

### Metro CU importer format

Split debit/credit columns, which is a common bank CSV format:

```
Transaction Date,Debit,Credit,Memo
02/15/2026,,2800.00,EMPLOYER DIRECT DEP
02/16/2026,87.43,,KROGER #1234
```

- Date format: `MM/DD/YYYY` (vs `YYYY-MM-DD` in the example importer)
- Empty debit = credit transaction, empty credit = debit transaction
- Column name `Memo` instead of `description`

This exercises different parsing logic in the importer: date format conversion, debit/credit merging, and column renaming.

### Seed structure

The seed script will be reorganized into phases:
1. Create internal accounts (with active/inactive flags)
2. Create categories (same set, possibly expanded)
3. Create external accounts (merchants + transfer counterparties)
4. Create Import records (one per "institution" for realism)
5. Generate transactions per month, routing to the correct bank based on the timeline
6. Generate transfer pairs
7. Generate small pending inbox batch (~8-10 items from most recent month)

### Test CSV files

- `test_export.csv` — updated to reference First National-style data, covering a couple months
- `test_metro_cu.csv` — Metro CU format, covering Feb-Mar 2026 (overlaps with seeded data for dedup testing)

## Risks / Trade-offs

- [More complex seed script] → Organize with clear sections and helper functions; deterministic RNG keeps it reproducible
- [Transfer pairs double transaction count] → Expected; realistic data volume is a goal
- [test_metro_cu.csv overlaps seeded data] → This is intentional to test dedup, but could cause confusion if not documented
