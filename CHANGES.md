# Changes

Incremental, end-to-end changes to build the financial pipeline app. Each change should result in something runnable and verifiable.

## ~~1. Project skeleton~~ DONE

- ~~Create `pyproject.toml` with all dependencies~~
- ~~Create `flake.nix` with dev shell (uv, tailwindcss CLI)~~
- ~~Set up `src/financial_pipeline/` package structure~~
- ~~`uv sync` works, `nix develop` drops into a working shell~~

## ~~2+3. Hello world FastAPI app + Tailwind/DaisyUI~~ DONE

- ~~FastAPI app with Jinja2 templates, HTMX (CDN), static file serving~~
- ~~Tailwind v4 standalone CLI + DaisyUI v5 CSS (flake input, no Node.js)~~
- ~~Compiled CSS build: `tailwindcss -i input.css -o static/css/style.css`~~

## ~~4. Database and models~~ DONE

- ~~`db.py` — async SQLite engine and session factory~~
- ~~`models.py` — Account, Import, Transaction models (unified accounts table, integer cents, dual description)~~
- ~~App startup creates tables automatically via lifespan handler~~
- ~~Seed example internal accounts (placeholder for user config module)~~

## ~~5. CSV parsing with Polars~~ DONE

- ~~`schemas.py` — `ImportedTransaction` patito model (date, amount as Decimal, description)~~
- ~~`ingest.py` — importer discovery via importlib, `ingest()` writes validated DataFrames to DB~~
- ~~`importers/` directory convention — user-managed Python modules with `IMPORTER_NAME` + `parse(blob)`~~
- ~~Deduplication deferred (see TODO.md)~~

## ~~6+7. CSV upload, inbox, and transaction review~~ DONE

- ~~Upload page with importer/account dropdowns, HTMX form submission~~
- ~~Inbox page with pending transactions table, inline editing (description, external account)~~
- ~~Approval workflow: checkbox toggle + commit button for bulk approval~~
- ~~Navigation bar on all pages~~
- ~~Orphaned external account pruning on commit~~

## 8. View all transactions

- Transactions page showing all approved transactions in a sortable/filterable table
- Pagination or infinite scroll for large datasets
- Filter by source, date range
- **Verify:** Approved transactions appear on the transactions page with working filters

## 9. Simple auth (DEFERRED)

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
