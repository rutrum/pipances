## 1. Route and Page Skeleton

- [x] 1.1 Create `routes/import_page.py` with GET `/import` route, register in `main.py`, remove old upload router
- [x] 1.2 Create `import.html` template with tab layout (CSV Upload / Manual Entry), using HTMX tab switching via `/import/csv` and `/import/manual` partials
- [x] 1.3 Create `_import_csv.html` partial with file input and "Scan File" button
- [x] 1.4 Create `_import_manual.html` partial with spreadsheet form (placeholder)
- [x] 1.5 Update `_navbar.html`: rename "Upload" to "Import", change href to `/import`, update icon and active_page check

## 2. CSV Auto-Detection and Preview

- [x] 2.1 Add `try_all_importers(blob: bytes)` function in `ingest.py` that runs every importer's `parse()` in a try/except and returns dict of successes and failures
- [x] 2.2 Add temp file management: save uploaded bytes to `import_{uuid}.csv`, lazy cleanup of files >1hr old
- [x] 2.3 Create POST `/import/preview` endpoint: save file, run auto-detection, return preview partial with importer results and parsed table
- [x] 2.4 Create `_import_preview.html` partial: shows matched/failed importers, preview table (Date, Amount, Description), account dropdown, hidden token input, "Add to Inbox" button

## 3. Duplicate Highlighting in Preview

- [x] 3.1 Extract read-only dedup logic from `ingest()` into `preview_dedup(df, internal_account)` that returns per-row duplicate flags without writing to the database
- [x] 3.2 Add HTMX callback on account dropdown selection that re-renders the preview table with duplicate annotations (strikethrough styling) and new/duplicate count summary
- [x] 3.3 Create POST or GET endpoint for dedup re-render (e.g. `/import/preview/dedup`) that accepts token, importer, and account

## 4. CSV Commit

- [x] 4.1 Create POST `/import/commit` endpoint: read temp file by token, parse with selected importer, call existing `ingest()`, delete temp file, redirect to inbox with toast
- [x] 4.2 Handle error cases: invalid/expired token, parse failure, ingest failure — return inline error messages

## 5. Manual Entry

- [x] 5.1 Flesh out `_import_manual.html`: account dropdown, multi-row table (Date, Amount, Description, remove button), "Add Row" button, "Add to Inbox" button
- [x] 5.2 Add client-side row add/remove (minimal inline JS for adding/removing table rows)
- [x] 5.3 Create POST `/import/manual` endpoint: validate rows, skip empty rows, create Import record with `institution="Manual"`, create Transactions with `raw_description=description=<input>`, run ML predictions, redirect to inbox with toast
- [x] 5.4 Handle edge cases: no valid rows, no accounts available, validation errors

## 6. Cleanup

- [x] 6.1 Delete old `routes/upload.py` and `templates/upload.html`
- [x] 6.2 Remove `upload_mod` monkeypatch from `conftest.py`, add `import_page_mod` monkeypatch for new route module

## 7. Update Existing Tests

- [x] 7.1 Update `test_upload_page_get_200` → `test_import_page_get_200` hitting GET `/import`, assert 200
- [x] 7.2 Update `test_upload_missing_file` → test POST `/import/preview` with no file, assert error response
- [x] 7.3 Update `test_upload_unknown_importer` → test POST `/import/commit` with invalid importer key, assert error
- [x] 7.4 Update `test_upload_error_does_not_leak_internals` → test POST `/import/preview` with unparseable file, assert no traceback in response
- [x] 7.5 Verify `/upload` returns 404 (like existing `test_old_dashboard_returns_404` pattern)

## 8. Unit Tests: Auto-Detection and Preview

- [x] 8.1 Test `try_all_importers()`: valid CSV returns the example importer as a match
- [x] 8.2 Test `try_all_importers()`: garbage bytes returns no matches
- [x] 8.3 Test `preview_dedup()`: returns correct duplicate flags for rows matching existing DB transactions
- [x] 8.4 Test `preview_dedup()`: returns no duplicates when DB is empty
- [x] 8.5 Test `preview_dedup()`: same-file duplicate rows are NOT flagged (only cross-import dupes)

## 9. Integration Tests: CSV Preview and Commit Flow

- [x] 9.1 Test POST `/import/preview` with valid CSV: returns 200, response contains preview table HTML, response contains hidden token input
- [x] 9.2 Test POST `/import/preview` with valid CSV: temp file is created on disk
- [x] 9.3 Test POST `/import/preview` with unparseable CSV: returns error, no temp file created
- [x] 9.4 Test POST `/import/commit` with valid token, importer, and account: transactions are inserted, temp file is deleted, redirects to inbox
- [x] 9.5 Test POST `/import/commit` with invalid/missing token: returns error indicating preview expired
- [x] 9.6 Test POST `/import/commit` with valid token but nonexistent account: returns error
- [x] 9.7 Test dedup endpoint (`/import/preview/dedup`): returns preview table with strikethrough markup for duplicate rows

## 10. Integration Tests: Manual Entry

- [x] 10.1 Test POST `/import/manual` with valid rows: creates Import record with `institution="Manual"`, creates Transaction records, redirects to inbox
- [x] 10.2 Test POST `/import/manual` with mix of filled and empty rows: empty rows are skipped, filled rows are inserted
- [x] 10.3 Test POST `/import/manual` with all empty rows: returns error, no Import record created
- [x] 10.4 Test POST `/import/manual` with no account selected: returns error
- [x] 10.5 Test GET `/import/manual` partial: returns form HTML with account dropdown and spreadsheet table

## 11. Integration Tests: Tab Navigation

- [x] 11.1 Test GET `/import` returns full page with CSV tab content by default
- [x] 11.2 Test GET `/import/csv` with `HX-Request` header returns partial (no `<html>` tag)
- [x] 11.3 Test GET `/import/manual` with `HX-Request` header returns partial (no `<html>` tag)

## 12. Manual Browser Testing

- [x] 12.1 Verify Import page loads, both tabs switch correctly via HTMX
- [x] 12.2 CSV tab: upload `test_export.csv`, verify auto-detection picks the correct importer, preview table renders with parsed rows
- [x] 12.3 CSV tab: select an account, verify duplicate rows get strikethrough styling
- [x] 12.4 CSV tab: click "Add to Inbox", verify redirect to inbox with toast showing import summary
- [x] 12.5 CSV tab: re-upload same file, verify all rows show as duplicates in preview
- [x] 12.6 CSV tab: upload garbage file, verify error message displays
- [x] 12.7 Manual tab: add multiple rows, fill in date/amount/description, select account, submit — verify transactions appear in inbox
- [x] 12.8 Manual tab: submit with empty rows mixed in, verify empty rows are skipped
- [x] 12.9 Manual tab: submit with all empty rows, verify error message
- [x] 12.10 Verify navbar shows "Import" with correct active state highlighting

## 13. Final Checks

- [x] 13.1 Run `just test` — all tests pass
- [x] 13.2 Run `just fmt` and `just check` — no lint/format issues
