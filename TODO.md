# TODO

Items deferred from design discussions to tackle later.

## Deduplication strategy
When re-importing the same CSV, how do we detect and skip duplicate transactions? Candidate approaches:
- Composite key on `(internal_id, external_id, date, amount, raw_description)`
- Hash of the original CSV row
- Track import date ranges and skip re-imports at the file level

Needs more thought — two legitimate identical transactions on the same day (e.g. same merchant, same amount) complicate any row-level dedup.

## User config module structure
User-managed Python module at `src/config/` (gitignored) defines internal accounts and eventually per-institution CSV parsing schemas. Open questions:
- How to structure the API between `financial_pipeline` and `config` — config calls functions from the library, or library imports config?
- Potential circular dependency if library needs to know about config and config imports library types/functions
- Consider a registry pattern or declarative approach to avoid tight coupling

## Seeding behavior on startup
When syncing internal accounts from config module to DB:
- Upsert-only (create if missing, skip if exists) is safest
- What happens if an account is removed from config but has transactions referencing it? Can't delete due to FK constraints. Soft-delete? Ignore?

## Inbox table refactoring
Consider extracting shared transaction table elements (row partials, column rendering) between the inbox editing view and the read-only transactions view. The inbox has interactive elements (checkboxes, click-to-edit) that the transactions page doesn't need, but the base column rendering (date, amount formatting, account names) could be shared. Revisit after the transactions page is built to see if the overlap justifies extraction.

## Agent browser testing with Nix
Get Chrome DevTools MCP working within the Nix dev environment. May need to build/package the MCP server. Consider migrating the flake to numtide/blueprint to manage it cleanly.

## Transaction categories
Add a category/tagging system for transactions. External accounts currently serve as a rough proxy for "where money goes," but proper categories (groceries, utilities, entertainment, etc.) would enable better chart breakdowns on the dashboard and more meaningful filtering.

## Starting balances for accounts
Internal accounts need a starting balance so we can compute a meaningful "net total" / running balance. Without this, totals only reflect the delta from imported transactions, not actual account state.

## Embed CDN dependencies
Consider self-hosting or bundling CDN dependencies (HTMX, Vega-Embed, Vega-Lite, Vega) instead of loading from unpkg/cdn.jsdelivr. Would make the app fully self-contained for offline/air-gapped use.

## Institution identifier convention
`imports.institution` should match identifiers used in the config module's per-institution parsing schemas. No FK enforcement yet, but worth keeping consistent as a convention.
