## 1. Dependencies

- [x] 1.1 Add patito as a dependency via `uv add`
- [x] 1.2 Spike: verify patito supports `Decimal(38, 2)` in a Model field. If not, determine fallback (e.g. `pl.Float64`)

## 2. Patito Model

- [x] 2.1 Create `src/financial_pipeline/schemas.py` with `ImportedTransaction` patito model (date, amount, description)

## 3. Importer Discovery

- [x] 3.1 Create `src/financial_pipeline/ingest.py` with `discover_importers()` — scans `importers/` directory, loads modules via importlib, validates each has `IMPORTER_NAME` and `parse`, returns dict of available importers

## 4. Ingest Pipeline

- [x] 4.1 Create `ingest()` async function in `ingest.py` — takes validated DataFrame, internal account name, importer name, filename. Creates Import record, resolves/creates external accounts, maps columns (description→raw_description, amount→amount_cents, etc.), writes Transaction rows to DB

## 5. Example Importer and Verification

- [x] 5.1 Create `importers/` directory with an example importer (e.g. `example.py` for a simple CSV with date, amount, description columns)
- [x] 5.2 Create a sample CSV file for testing
- [x] 5.3 Write a verification script that discovers the example importer, parses the sample CSV, ingests to DB, and prints the resulting transactions
