# TODO

Items deferred from design discussions to tackle later.

## Institution identifier convention
`imports.institution` should match identifiers used in the config module's per-institution parsing schemas. No FK enforcement yet, but worth keeping consistent as a convention.

## Simple auth
Login page with single-user password (configured via environment variable). Session cookie via `itsdangerous`. Protected routes redirect to login. Logout clears session.

## Interactive chart click-to-filter
On the dashboard Categories tab, clicking a pie chart slice could auto-select that category in the dropdown. Requires Vega signal handling and bridging to HTMX. Deferred until we have a pattern for Vega-to-HTMX interactivity.

## ML predictions: on-demand re-prediction in inbox
During a long inbox review session, the user may approve transactions that provide new training data. A "Re-predict" button in the inbox could re-run the model against remaining pending transactions using the freshly approved data. Deferred — start with import-time prediction only.

## ML predictions: multiple suggestions per field
Instead of a single suggestion, show the top 2-3 most likely values for a field (e.g. category dropdown pre-sorted by confidence). Useful when the model is uncertain. Deferred — start with single best suggestion or nothing.

## ML predictions: model caching
Rebuild the TF-IDF + kNN model on every import for now. If performance becomes an issue with large datasets (10k+ approved transactions), cache the fitted model and invalidate on new approvals.

## ML predictions: upgrade to embedding model
If TF-IDF char n-grams prove insufficient (e.g. can't match "WHOLEFDS" to "Whole Foods"), consider Model2Vec (numpy-only, 8-30MB) or FastEmbed (ONNX-based, ~50MB) as a drop-in upgrade for the vectorization step.

## Auto-consume upload directory
A configured directory that the application watches/scans for CSV files. When files appear, they are automatically ingested (parsed, deduplicated, added to inbox). This would complement the web upload flow for users who want to drop files via cron/script.

## Category editing in Data page
Categories are currently read-only (rename only, no delete, no create) in the Data page. May want to revisit adding more editing capabilities later.

## CI/CD pipeline
Set up automated testing (and possibly linting/formatting checks) on push/PR. Now that `just check` runs tests, a CI pipeline can gate merges on passing checks.

## Fix OOB swap fragility

The codebase uses three different patterns for HTMX out-of-band swaps, all based on string manipulation:

1. **str.replace() injection** — Render a template normally, then inject `hx-swap-oob` by replacing the `id="..."` attribute via string replacement. Fragile: if the template changes attribute order, the replace silently fails and the OOB swap doesn't happen. Used for date range, pagination, thead, and transaction row OOB updates.

2. **Inline HTML strings** — Hand-constructed HTML fragments with `hx-swap-oob` baked in (toasts, badge updates, dialog clears). Not fragile per se, but mixes HTML into Python.

3. **Class-string matching** — The inbox pagination OOB replaces on a Tailwind class string (`<div class="flex items-center..."`). Any CSS change breaks it. Worst of the three.

The proper fix: make templates themselves OOB-aware. Pass an `oob=True` parameter when rendering a partial, and the template conditionally includes the `hx-swap-oob` attribute. This eliminates all post-render string manipulation.

## NixOS module: auth option
Once simple auth is implemented, add a `passwordFile` option to the NixOS module (sops/agenix friendly).

## More details on ML results
I want to drill down onto all results and see what the best guesses were for the ML model.  Even better if I can pick from them.  Maybe thats the default drop down when I enter an empty value: I get the top 5 closest with the percentage confidence next to each.  That'd be cool.

## Consider Duckdb over SQLITE
One source of complexity (imo) is that SQLITE doesn't maintain types our types (like decimal), so we have this disconnect between the data storage and the parsing.  I think duckdb will help permit us to have less overhead in the database abstraction layer.

## Category splits
When I enter a new item, I need to be able to "split" the transaction such that it contributes to multiple categories.

## dark mode/theme toggle

## Minor bugs/tweaks
* the account dropdown in import transactions/csv upload is wierdly not centered vertically
* transactions marked "approved" should be un-editable
* hitting tab should move you from one editable box to the next (I think I want just htose, not checkboxes of approved boxes (maybe))
* drop down suggestions should not be just the top 5...why not top 50?
* hitting retrain messes up the ordering of hte transactions (newest first all the sudden)
* retrain probably ought to happen after every commit
* the user experience when typing in the field is buggy/weird.  It needs a fine tooth comb on reactions to enter, tab, arrows, un-focus, etc.
* description should also be a dropdown
* we should not permit approval if the external account is not filled out: further, we probably shouldn't even fill it with the description by default, its nearly never right
* the date bar charts have the bars in locations I wouldn't expect.  Id put the month tick in between the red/green.  Not however its doing it (randomly?  Sometimes padding on one side and not the other)
### Checkboxes in Inbox
1. When I select I think I want the row to highlight blue or something so its more obvious
2. Theres a bug that whne I refresh the page (or apply in bulk) it doesn't reset whats checked off
### Pagination
1. The page x of x is greyed out (its not clickable but it shouldn't look disabled, see daisy UI examples)
2. When I hit commit, the page count doesn't update (but the transactions list does)

## Editing Transactions in post
If I make a mistake in the inbox, (I have) then it should allow me to edit afterwards
CRITICAL BUG MAYBE: it might have committed transacations that I didn't actually select.  Is the indexing off?  It shouldn't have let me approve without assigning everything...NO, its just that the transactions SHOWS THOSE HTINGS IN THE INBOX...feature: we should have a button at the top for that page exclusively that says "include inbox" or not.

## Quick action buttons on inbox records
1. Wipe all (clear all fields)
2. Re-predict this row

## Investigate the formula
* In my mind, its rare that two different external account could nearly ever share the same description, but that seems to be what I'm finding out a lot.
* It clear to me that each one is being estimated independently, when in reality the results are heavily correlated, so they probably ought to not be.
* The (external, description) and the raw_description should be correlated with one another.  I dont see that happening.
* The inficon description might be bug: It can't handle "Deposit from INFICON, Inc-OSV PAYROLL565" well.  Those numbers might be whats up.
* It could also be the price that's driving the proximity too good.  Really the description should have the greatest impact, IMO.

## Clean up Task
* Add a task to normalize very similar descriptions, or fix casing, etc.
  * "Water & Gas" and "Gas & Water" should be shown as similar
  * Typos

## Critical:
* The other internal accounts don't show up in the dropdown.
