# TODO

Items deferred from design discussions to tackle later.

## Deduplication strategy
When re-importing the same CSV, how do we detect and skip duplicate transactions? Candidate approaches:
- Composite key on `(internal_id, external_id, date, amount, raw_description)`
- Hash of the original CSV row
- Track import date ranges and skip re-imports at the file level

Needs more thought — two legitimate identical transactions on the same day (e.g. same merchant, same amount) complicate any row-level dedup.

## Inbox table refactoring
Consider extracting shared transaction table elements (row partials, column rendering) between the inbox editing view and the read-only transactions view. The inbox has interactive elements (checkboxes, click-to-edit) that the transactions page doesn't need, but the base column rendering (date, amount formatting, account names) could be shared. Revisit after the transactions page is built to see if the overlap justifies extraction.

## Transaction categories
Add a category/tagging system for transactions. External accounts currently serve as a rough proxy for "where money goes," but proper categories (groceries, utilities, entertainment, etc.) would enable better chart breakdowns on the dashboard and more meaningful filtering. This will touch:
- New DB model (Category table, FK on transactions)
- Inbox editing (assign category during review)
- Transaction filtering (by category)
- Dashboard breakdowns (spending by category)
- A management page for CRUD on categories

## Test data management
Add a `just reset-db` recipe that deletes `financial_pipeline.db` for a clean start. Consider also a separate test database or fixture system so browser testing doesn't pollute real data.

## Embed CDN dependencies
Consider self-hosting or bundling CDN dependencies (HTMX, Vega-Embed, Vega-Lite, Vega) instead of loading from unpkg/cdn.jsdelivr. Would make the app fully self-contained for offline/air-gapped use.

## Institution identifier convention
`imports.institution` should match identifiers used in the config module's per-institution parsing schemas. No FK enforcement yet, but worth keeping consistent as a convention.

## Categories management page
Once transaction categories are added, provide a management page for CRUD on categories. Could live under `/settings/categories` as a new tab alongside the existing accounts tab.

## Dashboard tabs and expanded charts
The dashboard should support multiple views via tabs: Overview (current), By Source (per-account trends/balances), Category Breakdown (once categories exist). Each tab can have its own set of charts and summaries.

## Dashboard time filter
Add a time range filter to the dashboard so users can drill into specific periods. Should be independent from the transactions page date range. Could reuse the `_date_range.html` partial with HTMX to re-render dashboard content.

## Simple auth
Login page with single-user password (configured via environment variable). Session cookie via `itsdangerous`. Protected routes redirect to login. Logout clears session.

## ML-assisted inbox (long-term)
Use historical transaction data to pre-fill description, external account, and (eventually) category during inbox review. Key UX challenge: clearly distinguish ML suggestions from original data (e.g. robot icon, colored background, confidence score). Needs a training corpus and model choice. Depends on categories being implemented first.

## Linting / Formatting
Integrate some code quality/checking tools.  Ruff for python, maybe something else for the HTMX code.  Then integrate them in the workflow somehow: precommit, agent rules, something
