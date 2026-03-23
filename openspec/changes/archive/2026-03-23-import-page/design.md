## Context

The current upload page (`/upload`) is a single-step form: select importer, select account, pick file, submit. All parsing, dedup, and ingestion happen in one POST. Users have no visibility into what will be imported or which rows are duplicates. There is no way to manually enter transactions.

The ingest pipeline (`ingest.py`) handles CSV parsing, dedup, DB writes, and ML predictions. Importers are Python modules discovered from the `importers/` directory, each exposing `IMPORTER_NAME` and `parse(blob) -> DataFrame`.

## Goals / Non-Goals

**Goals:**
- Two-step CSV import: preview parsed data (with duplicate highlighting) before committing
- Auto-detect which importers can parse a given file
- Manual transaction entry via multi-row spreadsheet form
- Manual entries flow through the same ingest/ML pipeline as CSV imports
- Clean tab-based UI at `/import` replacing `/upload`

**Non-Goals:**
- Editing transactions during the preview step (that's what the inbox is for)
- Drag-and-drop file upload
- Streaming/chunked upload for very large files
- Category or external account selection during manual entry (ML handles this)

## Decisions

### 1. Server-side temp file for CSV preview-to-commit flow

**Decision:** After the user uploads a CSV for preview, store the raw bytes in a temp file on the server keyed by a UUID token. The commit step reads from this temp file.

**Alternatives considered:**
- *One form, two POSTs (re-upload file):* HTMX can't easily re-send a file input from a replaced form region. Fragile if user clears the input.
- *In-memory cache:* Memory pressure risk if users upload large files and abandon. No persistence across server restarts.

**Rationale:** Temp files are simple, persist across requests, don't consume memory, and the token pattern is straightforward. Cleanup is easy (delete on commit, TTL for abandoned files).

**Temp file location:** Use Python's `tempfile` module with a configurable directory. Files named `import_{uuid}.csv`. Lazy cleanup: on each new upload, delete any temp files older than 1 hour.

### 2. Auto-detection by trying all importers

**Decision:** When a file is uploaded for preview, try every discovered importer's `parse()` function against the file. Collect which ones succeed (return a valid DataFrame) and which fail (raise an exception).

**Rationale:** Importers already raise on bad input. This is a simple try/except loop. If exactly one succeeds, auto-select it. If multiple succeed, let the user pick. If none succeed, show an error.

### 3. Read-only dedup preview

**Decision:** Extract the dedup logic from `ingest()` into a separate `preview_dedup()` function that performs the same duplicate detection but returns results without writing to the database.

**Rationale:** The preview step needs to show which rows are duplicates, but nothing should be written until the user confirms. Sharing the dedup logic ensures the preview matches what commit will actually do. The preview function needs an account name to check against, so account selection happens before (or alongside) the preview display.

**Refinement:** Account selection is part of the preview step. The initial scan shows importer results and the parsed table. The user selects an account, and the dedup check runs (or re-runs) with that account context. This could be a second HTMX call, or the dedup could be deferred to the commit step with the preview just showing raw parsed rows. For simplicity, defer dedup highlighting until account is selected — an HTMX call from the account dropdown re-renders the preview table with dupe annotations.

### 4. Manual entry creates standard Import records

**Decision:** Manual entries create an `Import` record with `institution="Manual"` and `filename=None`. Each row becomes a Transaction with `raw_description = <user input>`, `description = <user input>`. ML predictions run on the batch normally.

**Rationale:** No schema changes needed. The ML predictor operates on `raw_description` regardless of source, so category suggestions still work. Transactions start as pending and flow through the inbox like CSV imports.

### 5. Tab-based page layout with HTMX

**Decision:** The `/import` page has two tabs ("CSV Upload" and "Manual Entry"). Tab switching uses HTMX to swap the content area, loading partials from `/import/csv` and `/import/manual`.

**Rationale:** Consistent with the existing sidebar pattern on the Data page (pre-render partial, pass as context variable for full-page load, HTMX swap for tab clicks).

### 6. Route structure

| Endpoint | Method | Purpose |
|---|---|---|
| `/import` | GET | Full page, default to CSV tab |
| `/import/csv` | GET | CSV upload partial (for HTMX tab swap) |
| `/import/manual` | GET | Manual entry partial (for HTMX tab swap) |
| `/import/preview` | POST | Upload file, auto-detect, return preview partial |
| `/import/commit` | POST | Commit previewed CSV to database |
| `/import/manual` | POST | Submit manual entries to database |

## Risks / Trade-offs

- **Temp file cleanup on abandoned uploads** -> Lazy cleanup (delete files >1hr old on each new upload) is simple but could leave orphans if no one uploads for a while. Acceptable for a single-user app.
- **Auto-detect false positives** -> Two importers could both successfully parse the same file but produce different results. -> Mitigation: show the user which importers matched and let them pick. The preview table makes it obvious if the wrong importer was selected.
- **Dedup requires account selection** -> The preview can show parsed rows immediately, but duplicate highlighting requires knowing which account to check against. -> Mitigation: show the table immediately, add dupe highlighting when account is selected via HTMX callback.
- **Manual entry has no raw bank description** -> ML predictions may be less useful since the input is already human-readable. -> Accepted: category prediction from description text still provides value.
