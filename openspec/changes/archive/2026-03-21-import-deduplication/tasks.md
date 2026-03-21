## 1. Dedup Logic

- [x] 1.1 Create `IngestResult` dataclass in `ingest.py` with fields: `inserted_count`, `duplicate_count`, `date_min`, `date_max`, `internal_account_name`
- [x] 1.2 Implement count-based dedup in `ingest()`: group incoming rows by `(date, amount_cents, raw_description)`, query DB for existing counts per key, insert only `max(0, csv_count - db_count)` per key
- [x] 1.3 Update `ingest()` return type from `int` to `IngestResult`

## 2. raw_description Immutability

- [x] 2.1 Audit all PATCH/PUT endpoints to verify none allow editing `raw_description`; remove the capability if any do

## 3. Import Feedback

- [x] 3.1 Update the upload endpoint to use `IngestResult` and pass import summary data (via query params or session) when redirecting to inbox
- [x] 3.2 Update inbox template to display import result summary (transactions imported, duplicates skipped, date range, account name) when present

## 4. Verification

- [x] 4.1 Run `just seed` and import `test_export.csv` — verify 10 new transactions imported, 1 duplicate skipped (March 18 Spotify), with correct feedback
- [x] 4.2 Re-import `test_export.csv` — verify 0 imported, 11 duplicates skipped, with correct feedback
- [x] 4.3 Verify `raw_description` cannot be edited from any UI interaction
