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

## Deployment as a nix module and container (running nix?)
