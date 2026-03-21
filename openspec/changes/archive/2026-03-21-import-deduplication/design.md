## Context

The `ingest()` function in `ingest.py` currently inserts every row from a parsed CSV unconditionally. Bank CSV exports commonly overlap in date ranges (e.g., downloading January then February, where February includes late January). This leads to duplicate transactions. The upload endpoint redirects to the inbox with no feedback about what happened.

The dedup key must use only immutable CSV-derived fields. Fields like `external_id`, `description`, and `category_id` are enriched post-import (by users or future ML) and must not participate in dedup.

## Goals / Non-Goals

**Goals:**
- Skip duplicate transactions automatically during import
- Preserve genuine same-day identical purchases (same-file duplicates)
- Show the user a summary after upload (imported count, duplicates skipped, date range, account)
- Ensure `raw_description` is never editable

**Non-Goals:**
- UI for reviewing/resolving duplicates manually
- Dedup across different internal accounts (same transaction appearing in checking and credit card exports is intentional)
- Retroactive dedup of already-imported data

## Decisions

### Decision: Count-based dedup on `(date, amount_cents, raw_description)`

The dedup key is the tuple `(date, amount_cents, raw_description)`. These three fields are immutable and come directly from the CSV. For each unique key in the incoming file:

```
to_insert = max(0, csv_count - db_count)
```

Where `csv_count` is how many rows in the current file share that key, and `db_count` is how many transactions already in the database match that key.

This handles:
- **Overlapping exports**: Rows already in DB are skipped
- **Same-file duplicates**: Two identical Starbucks purchases in the same CSV are both inserted
- **Partial re-imports**: If a prior import had 1 of 2 identical rows, the second import adds the missing one

**Alternative**: Boolean "exists in DB" check. Rejected because it would drop the second genuine duplicate if imports came in different orders.

**Alternative**: Row-position hashing. Rejected because bank exports don't guarantee stable row ordering.

### Decision: `ingest()` returns a result dataclass

Change the return type from `int` to a dataclass containing: `inserted_count`, `duplicate_count`, `date_min`, `date_max`, and `internal_account_name`. This gives the upload endpoint everything it needs to render feedback without extra queries.

### Decision: Toast-based import feedback

After a successful upload, redirect to the inbox with import results encoded in query parameters. The inbox page renders a toast/alert showing: "Imported N transactions (M duplicates skipped) for [Account] from [date_min] to [date_max]". This reuses the existing redirect-to-inbox flow without adding new pages.

### Decision: `raw_description` is immutable

Verify that no existing endpoint allows PATCH/PUT on `raw_description`. If any do, remove that capability. This field is part of the dedup key and must never change after import.

## Risks / Trade-offs

- **Dedup key doesn't include `internal_id`**: If a user imports the same CSV twice under different internal accounts, both sets of transactions are kept. This is acceptable — it's user error and the transactions genuinely belong to different accounts from the system's perspective.
- **Count-based approach assumes complete files**: If a bank export is truncated mid-download and re-downloaded, the counts could mismatch. This is an extreme edge case and the inbox provides a safety net for review.
- **Query cost at import time**: Dedup requires counting existing matches in the DB for each unique key in the CSV. For typical imports (tens to hundreds of rows), this is negligible. If imports reach thousands of rows, a bulk query approach could optimize this.
