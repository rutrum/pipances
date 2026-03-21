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

## Give this a new name
I like pipeline.  Fin-pipe.  Pipances.  Pipemoney.  |money

## Random fixes

- pagination on inbox
- Sorting in inbox like in transactions
- make the AI inferred fields better: the light blue background could be better...it also breaks the height when you edit the field...and changing the value also breaks
- better "click to edit"
- change Amount ($) and remove $ from records
  - align cell right so . line up
- When I refresh, the filters stay the same but the transactions are no longer filtered
- the custom date filter should appear to the right (all the way), not underneath
- the underline below selected in nav bar is weird

## Drill Downs
Need to design more generic dashboard pages.  When I click on a category in my list of categories, I should go to a dashboard page that shows a breakdown.  Similarly for accounts.

## More schema pages
I need an external account page, and even a importer page.
In light of that, I'm wondering if transactions/accounts/categories should all be under one page.  Not call it settings but something else.
Ideally this page would have a left sidebar thats in two sections: configurations based things, like ML parameters/options and importers, and then data-based things, like viewing all the data in the database.  Or maybe those are just two different tabs at the top.

## Manual Transactions
There should still be a way to define one-off transactions.  Like a form you fill out.  Might be nice to incorporate the ML in this too.  Problem: this removed the "raw description" parameter as being a required field.  Interesting.

## Maybe we should have a test bed
some automated UI testing might help.  We already have test data.
