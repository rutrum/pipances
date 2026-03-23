## Why

The current upload page is a single-step form that requires the user to manually select an importer, account, and file before blindly committing transactions. There's no preview of what will be imported, no visibility into which rows are duplicates, and no way to manually enter transactions without a CSV. This change replaces the upload page with a richer "Import" page that gives users more control and a second import method.

## What Changes

- **Replace `/upload` with `/import`** — new page with two tabs: "CSV Upload" and "Manual Entry"
- **CSV Upload: auto-detect importers** — after file upload, the system tries all importers and shows which ones matched, auto-selecting if only one succeeds
- **CSV Upload: preview before commit** — parsed transactions are shown in a table with duplicates highlighted (strikethrough), using server-side temp file storage between preview and commit steps
- **CSV Upload: deferred account selection** — account dropdown moves to the preview step, not the initial upload
- **Manual Entry: spreadsheet-style form** — multi-row table for hand-entering transactions (date, amount, description) with an account selector and "Add to Inbox" button
- **Manual Entry: pipeline integration** — manual entries create an Import record (`institution="Manual"`) and flow through the same ML prediction pipeline as CSV imports, using the user-provided description as `raw_description`
- **Navbar: rename "Upload" to "Import"** and update the route

## Capabilities

### New Capabilities
- `manual-transaction-entry`: Spreadsheet-style multi-row form for manually entering transactions, creating Import records and flowing through the standard pipeline
- `csv-import-preview`: Two-step CSV import flow with auto-detection of importers, preview table with duplicate highlighting, and server-side temp file storage

### Modified Capabilities
- `csv-upload`: The upload flow changes from single-step to two-step (preview then commit), importer selection becomes automatic, and the route moves from `/upload` to `/import`
- `navigation`: Navbar link changes from "Upload" (`/upload`) to "Import" (`/import`)

## Impact

- **Routes**: `routes/upload.py` replaced by `routes/import_page.py` with new endpoints (`/import`, `/import/preview`, `/import/commit`, `/import/manual`)
- **Templates**: `upload.html` replaced by `import.html` with tab layout, plus partials for CSV preview and manual entry
- **Ingest**: New `preview_dedup()` function needed (read-only dedup check without DB writes); existing `ingest()` remains for commit step
- **Temp files**: New server-side temp file management for storing uploaded CSVs between preview and commit
- **Navbar**: Link text and href updated
- **Models**: No schema changes — manual entries use existing Import and Transaction models
