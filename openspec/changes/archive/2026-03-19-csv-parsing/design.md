## Context

The database schema is in place (accounts, imports, transactions). Now we need a way to parse bank CSV exports into a normalized format. The user has prior experience with Polars-based CSV normalization and wants typed DataFrame schemas via patito.

The key insight: importers are user-managed, institution-specific Python modules. The library provides the contract (a patito model), the user provides the parsing logic. Validation happens at the boundary — if an importer produces bad data, it fails clearly.

## Goals / Non-Goals

**Goals:**
- `ImportedTransaction` patito model defining the importer output contract
- Runtime discovery of importer modules from `importers/` directory
- Validation of importer output against the patito model
- An example importer for reference

**Non-Goals:**
- No upload UI or inbox flow
- No deduplication (deferred, see TODO.md)
- No data access layer / read-back API (later change)

## Decisions

### ImportedTransaction patito model
The importer contract is intentionally minimal — three fields:

```
ImportedTransaction (patito Model)
├── date: date
├── amount: Decimal(38, 2)     signed, dollars
├── description: str
```

This is distinct from whatever model the DB-facing or web-facing layer uses. The importer's only job is to extract core transaction data from a CSV. Everything else gets added by the ingest layer when writing to the DB:
- `internal` ← user picks during upload
- `external` ← defaults to `description` (auto-created account)
- `raw_description` ← copy of `description`
- `description` ← set to NULL (user fills in during review)
- `amount_cents` ← `int(amount * 100)`
- `status` ← `"pending"`

### Importer module convention
Each importer is a `.py` file in the `importers/` directory at the project root. A module must export:
- `IMPORTER_NAME: str` — human-readable name (e.g. "Chase Credit Card")
- `def parse(blob: bytes) -> pt.DataFrame[ImportedTransaction]` — parse CSV bytes into the normalized schema

The importer is responsible for all institution-specific logic: column mapping, date parsing, amount sign conventions, filtering irrelevant rows, etc.

A single importer may be used for multiple accounts (e.g. two Chase credit cards use the same CSV format). The user selects which internal account a CSV belongs to at upload time, not in the importer.

### Runtime discovery via importlib
`ingest.py` scans the `importers/` directory for `.py` files and loads them dynamically using `importlib.util`. No package `__init__.py` required — just loose Python files in a known directory. Each module is validated to have the required exports (`IMPORTER_NAME`, `parse`).

Discovery returns a dict of `{module_name: ImporterInfo}` where `ImporterInfo` holds the name and parse function. This powers the upload UI's importer selection dropdown.

### Validation at the boundary
After an importer's `parse()` returns, the ingest layer validates the DataFrame against `ImportedTransaction` using patito's `validate()`. If validation fails, the error is surfaced to the user — the importer is broken and needs fixing. The app never writes invalid data to the DB.

### Ingest pipeline: DataFrame to DB
The `ingest()` function bridges the importer output and the database. It takes:
- The validated `DataFrame[ImportedTransaction]`
- The internal account name (user-selected at upload time)
- The importer name / institution identifier
- The filename (for the Import record)

It performs:
1. **Create Import record** — institution, filename, timestamp, row count
2. **Resolve internal account** — look up by name in accounts table, error if not found
3. **Resolve/create external accounts** — for each unique `description`, find-or-create an account with `kind="external"`
4. **Map columns:**
   - `description` → `raw_description`
   - `NULL` → `description` (user fills in during inbox review)
   - `amount * 100` → `amount_cents` (integer)
   - `"pending"` → `status`
5. **Write Transaction rows** to DB with all FKs resolved

This is an async function since it touches the DB. It's the single entry point for getting parsed CSV data into the database.

## File Layout

```
importers/                          (user-managed, not gitignored for now)
├── chase_credit.py                 IMPORTER_NAME + parse(blob)
├── ally_savings.py
└── ...

src/financial_pipeline/
├── schemas.py                      ImportedTransaction patito model
├── ingest.py                       discover_importers(), validate, ingest to DB
└── ...
```

## Risks / Trade-offs

- [importlib dynamic loading is implicit] → Mitigated by validating module exports at discovery time. Missing `IMPORTER_NAME` or `parse` raises a clear error.
- [patito Decimal support unclear] → Need to verify patito handles `Decimal(38, 2)`. Fallback: use `pl.Float64` and convert at the boundary. Should spike this early.
- [importers/ not gitignored yet] → Will contain test/example importers for now. Should be gitignored once the app is used with real financial data.
