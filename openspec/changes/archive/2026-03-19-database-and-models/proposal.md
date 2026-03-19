## Why

The app has a running web server but no data layer. We need a database schema and SQLAlchemy models before CSV import, inbox review, or any analysis features can be built. The schema design is informed by prior experience normalizing bank CSV exports into a unified transaction format.

## What Changes

- Create async SQLite engine and session factory (`db.py`)
- Create SQLAlchemy models for `accounts`, `imports`, and `transactions`
- Auto-create tables on app startup
- Seed a set of internal accounts (user's bank accounts, credit cards, etc.)

## Capabilities

(none — this is data layer infrastructure)

## Impact

- New files: `db.py`, `models.py`
- App startup now creates `financial_pipeline.db` with three tables
- Foundation for all subsequent features (CSV import, inbox, analysis)
