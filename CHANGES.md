# Changes

Incremental, end-to-end changes to build the financial pipeline app. Each change should result in something runnable and verifiable.

## ~~1. Project skeleton~~ DONE

- ~~Create `pyproject.toml` with all dependencies~~
- ~~Create `flake.nix` with dev shell (uv, tailwindcss CLI)~~
- ~~Set up `src/financial_pipeline/` package structure~~
- ~~`uv sync` works, `nix develop` drops into a working shell~~

## 2. Hello world FastAPI app

- `main.py` with a FastAPI app and a single index route
- `base.html` Jinja2 template loading HTMX (CDN) and DaisyUI (CDN for now)
- Static file serving configured
- **Verify:** `uv run python -m financial_pipeline.main` serves a styled page at localhost:8000

## 3. Tailwind + DaisyUI build pipeline

- `tailwind.config.js` with DaisyUI plugin, content paths to templates
- Input CSS with `@tailwind` directives
- Replace CDN with compiled CSS output
- **Verify:** Tailwind builds, DaisyUI classes render correctly in the browser

## 4. Database and models

- `db.py` — async SQLite engine and session factory
- `models.py` — `Source` and `Transaction` SQLAlchemy models
- App startup creates tables automatically
- Seed a few source accounts (checking, savings, credit card) via a script or startup
- **Verify:** App starts, `financial_pipeline.db` is created with correct tables

## 5. CSV parsing with Polars

- `schemas.py` — define parsing schemas as polars expressions for different CSV formats
- `ingest.py` — load CSV, apply schema, return a polars DataFrame of parsed transactions
- Deduplication logic: detect transactions already in the database
- **Verify:** Write a test or script that parses a sample CSV and prints the resulting DataFrame

## 6. CSV upload and inbox

- Upload route: accept CSV file, parse with polars, store transactions as "pending" in DB
- Inbox page: table showing pending transactions using DaisyUI table component
- HTMX: upload form submits without full page reload
- **Verify:** Upload a CSV via the browser, see parsed transactions appear in the inbox table

## 7. Transaction review and approval

- Inbox table rows have an "approve" button
- Approving a transaction moves it from pending to approved (status field)
- Bulk approve option (select all / select multiple)
- HTMX: approve actions update the table without full reload
- **Verify:** Upload CSV, review inbox, approve individual and bulk transactions

## 8. View all transactions

- Transactions page showing all approved transactions in a sortable/filterable table
- Pagination or infinite scroll for large datasets
- Filter by source, date range
- **Verify:** Approved transactions appear on the transactions page with working filters

## 9. Simple auth

- Login page with single-user password (configured via environment variable)
- Session cookie via `itsdangerous`
- Protected routes redirect to login
- Logout clears session
- **Verify:** Cannot access app without logging in, login works, logout works

## 10. Statistics and charts

- Stats page with Altair charts rendered as Vega-Lite JSON in the browser
- Charts: spending over time, spending by category/source, monthly summaries
- Summary statistics computed with Polars
- **Verify:** Stats page shows interactive charts based on transaction data
