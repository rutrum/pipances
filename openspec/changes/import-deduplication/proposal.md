## Why

Re-importing a CSV that overlaps with previously imported data creates duplicate transactions. Bank exports commonly overlap (e.g., downloading January then February, where February's export includes the last days of January). There's no mechanism to detect and skip already-imported rows. Additionally, the upload flow gives no feedback about what happened — the user is silently redirected to the inbox with no indication of how many transactions were imported.

## What Changes

- Add count-based deduplication to the `ingest()` function using an immutable key of `(date, amount_cents, raw_description)`
- Same-file duplicates (e.g., two identical Starbucks purchases on the same day) are treated as real, distinct transactions
- Cross-import duplicates (rows matching transactions already in the DB) are skipped
- Enforce `raw_description` immutability — ensure no endpoint allows editing it
- Add import result feedback: after upload, show the user how many transactions were imported, how many duplicates were skipped, the date range of imported transactions, and which internal account they were associated with

## Capabilities

### New Capabilities
- `import-feedback`: Post-upload summary showing import results (count imported, duplicates skipped, date range, account)

### Modified Capabilities
- `csv-upload`: Add deduplication behavior to the upload/ingest flow — duplicate rows from prior imports are silently skipped rather than re-inserted

## Impact

- **Modified files**: `ingest.py` (dedup logic), `main.py` (upload endpoint response + feedback rendering), upload/inbox templates (result display)
- **Models**: No schema changes needed — dedup uses existing columns
- **Behavior change**: `ingest()` return value changes from a simple count to include dedup statistics
