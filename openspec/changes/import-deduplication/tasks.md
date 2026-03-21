## 1. Dedup Logic

- [ ] 1.1 Create `IngestResult` dataclass in `ingest.py` with fields: `inserted_count`, `duplicate_count`, `date_min`, `date_max`, `internal_account_name`
- [ ] 1.2 Implement count-based dedup in `ingest()`: group incoming rows by `(date, amount_cents, raw_description)`, query DB for existing counts per key, insert only `max(0, csv_count - db_count)` per key
- [ ] 1.3 Update `ingest()` return type from `int` to `IngestResult`

## 2. raw_description Immutability

- [ ] 2.1 Audit all PATCH/PUT endpoints to verify none allow editing `raw_description`; remove the capability if any do

## 3. Import Feedback

- [ ] 3.1 Update the upload endpoint to use `IngestResult` and pass import summary data (via query params or session) when redirecting to inbox
- [ ] 3.2 Update inbox template to display import result summary (transactions imported, duplicates skipped, date range, account name) when present

## 4. Verification

- [ ] 4.1 Run `just seed` and import `test_export.csv` — verify all 10 transactions are imported with correct feedback
- [ ] 4.2 Re-import `test_export.csv` — verify 0 imported, 10 duplicates skipped, with correct feedback
- [ ] 4.3 Verify `raw_description` cannot be edited from any UI interaction
