## Why

The database exists but there's no way to get data into it. We need a CSV parsing layer that lets users define institution-specific importers, and a runtime discovery mechanism to load them. This is the foundation for the upload and inbox features.

## What Changes

- Add patito as a dependency (typed Polars DataFrames)
- Define `ImportedTransaction` patito model — the contract importers must produce
- Create importer discovery logic that scans `importers/` at runtime
- Create `ingest()` function that takes importer output + metadata, resolves accounts, and writes transactions to the DB
- Create `importers/` directory with an example importer for testing

## Capabilities

(none — this is data layer infrastructure)

## Impact

- New dependency: patito
- New files: `schemas.py` (patito models), `ingest.py` (discovery, validation, DB write)
- New convention: `importers/` directory at project root with user-defined Python modules
- Importers depend on `financial_pipeline.schemas` for the `ImportedTransaction` model
