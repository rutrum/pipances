# TODO

Items deferred from design discussions to tackle later.

## Institution identifier convention
`imports.institution` should match identifiers used in the config module's per-institution parsing schemas. No FK enforcement yet, but worth keeping consistent as a convention.

## Dashboard tabs and expanded charts
The dashboard should support multiple views via tabs: Overview (current), By Source (per-account trends/balances), Category Breakdown (once categories exist). Each tab can have its own set of charts and summaries.

## Dashboard time filter
Add a time range filter to the dashboard so users can drill into specific periods. Should be independent from the transactions page date range. Could reuse the `_date_range.html` partial with HTMX to re-render dashboard content.

## Simple auth
Login page with single-user password (configured via environment variable). Session cookie via `itsdangerous`. Protected routes redirect to login. Logout clears session.

## Interactive chart click-to-filter
On the dashboard Categories tab, clicking a pie chart slice could auto-select that category in the dropdown. Requires Vega signal handling and bridging to HTMX. Deferred until we have a pattern for Vega-to-HTMX interactivity.

## ML-assisted inbox (long-term)
Use historical transaction data to pre-fill description, external account, and (eventually) category during inbox review. Key UX challenge: clearly distinguish ML suggestions from original data (e.g. robot icon, colored background, confidence score). Needs a training corpus and model choice. Depends on categories being implemented first.

## Deployment as a nix module and container (running nix?)
