## Why

The app can parse CSVs and write to the database, but there's no way for a user to do this through the web UI. We need an upload page, an inbox for reviewing/editing imported transactions, and an approval workflow to commit reviewed transactions.

## What Changes

- Add `marked_for_approval` boolean column to Transaction model
- Add navigation bar (DaisyUI navbar)
- Upload page: select importer + account, upload CSV file, ingest to DB
- Inbox page: table of pending transactions with inline editing, approval marking, and bulk commit
- HTMX for all interactive elements (upload, inline edits, approval, commit)
- Orphan account pruning on commit

## Capabilities

### New Capabilities
- `csv-upload`: Upload a CSV file through the web UI, selecting an importer and internal account
- `inbox-review`: Review, edit, mark, and commit pending transactions

### Modified Capabilities

(none)

## Impact

- Schema change: new `marked_for_approval` column on transactions
- New routes: `/upload`, `/inbox`, `/inbox/commit`, PATCH endpoints for inline edits
- New templates: upload.html, inbox.html, navbar partial
- Index page becomes a redirect or landing with nav
