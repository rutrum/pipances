## Context

The app has no mechanism for populating test data. Browser testing requires manually uploading CSVs and approving transactions, and the existing test CSVs have 2024 dates that fall outside default filters. The current files are `importers/sample.csv` and `importers/test_data.csv`.

## Goals / Non-Goals

**Goals:**
- Deterministic seed script that produces a known database state
- Realistic transaction data spanning Oct 2025 – Mar 2026
- Test CSV with April 2026 data for import/inbox workflow testing
- Simple `just` recipes for resetting and seeding

**Non-Goals:**
- Randomized/parameterized data generation
- Test framework or automated test suite
- Separate test database (seed operates on the main DB)

## Decisions

### Decision: Python seed script using async ORM
`scripts/seed.py` uses the app's SQLAlchemy models directly to insert data. This means if models change (new columns, new tables), the seed script will either break obviously or can be updated to include the new data. The script uses `asyncio.run()` to call async ORM functions.

**Alternative**: Raw SQL fixtures. Rejected because they're fragile to schema changes and can't leverage model defaults/constraints.

### Decision: Deterministic via `random.seed(42)`
All randomized elements (transaction amounts, dates within a month, merchant selection) use a seeded random generator. This makes the output identical every run, so screenshots and test results are reproducible.

### Decision: Destructive `just seed`
`just seed` always calls `reset-db` first (deletes the DB file), then runs the seed script. There's no "add to existing data" mode. This guarantees a clean, known state.

### Decision: Realistic recurring patterns
The seed data includes recognizable patterns:
- Rent payment (~$1400) on the 1st of each month
- Paychecks ($2800) on the 1st and 15th
- Monthly subscriptions: Netflix ($15.99), Spotify ($12.99)
- Random grocery/dining/gas/shopping transactions throughout each month
- A few large purchases scattered in

This makes the dashboard charts and transaction lists look realistic and helps evaluate UI layout with real-world-like data.

### Decision: Test CSV in project root as `test_export.csv`
The April 2026 import CSV lives at the project root (alongside `financial_pipeline.db`) rather than in the `importers/` directory. It uses the same format as the example importer (date, amount, description). The old `importers/sample.csv` and `importers/test_data.csv` are deleted.

### Decision: Category distribution
Approved transactions are assigned categories from a weighted distribution reflecting realistic spending patterns. ~10% are left with `category_id=NULL` (uncategorized) to support testing the "Uncategorized" filter on the transactions page.

### Decision: "All" date preset on transactions page
Add an "All" button to the date range preset bar. When selected, `_compute_date_range` returns `None, None` and the transactions query skips the date WHERE clauses entirely. This is the simplest approach — no sentinel dates, just conditional query building.

## Risks / Trade-offs

- **Seed script couples to ORM models**: If models change significantly, the seed script needs updating. This is acceptable — it's a feature, not a bug, since it surfaces schema drift.
- **Fixed dates will eventually feel stale**: The Oct 2025 – Mar 2026 range works now but will drift from "current" over time. Acceptable for a single-user self-hosted app where the seed is a dev tool.
