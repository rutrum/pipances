## Why

A comprehensive code review (PR_REVIEW.md) identified 8 critical and 10 high-severity issues across the codebase. The most urgent are: XSS vulnerabilities in 3 different contexts (f-string HTML, JavaScript interpolation, hx-vals JSON injection), a floating-point currency bug that silently loses cents on every import, missing null checks that crash the server, and unvalidated user input that causes unhandled exceptions. These need to be fixed before any other work proceeds.

## What Changes

- Fix all XSS vectors: replace f-string HTML construction with Jinja2 template partials or `html.escape()`, use `|tojson` filter in JavaScript contexts, and fix `hx-vals` JSON injection in combo results and table body templates
- Fix the floating-point currency conversion in `ingest.py` (`int(amount * 100)` -> `int(round(amount * 100))`)
- Add null checks on all 8 edit endpoints that crash with `AttributeError` on invalid IDs (4 account, 1 category, 3 transaction)
- Wrap all `int()` conversions from query params in try/except with safe defaults
- Clamp `page_size` to a reasonable range (1-100)
- Wrap all `date.fromisoformat()` calls on user input in try/except
- Fix the bare `except Exception` in upload to not render raw error messages as HTML
- Escape SQL LIKE wildcards (`%`, `_`) in combo search queries
- Include internal account in the dedup key to prevent false-positive deduplication across accounts
- Enable SQLite foreign key enforcement (`PRAGMA foreign_keys = ON`)
- Add `server_default` to Transaction `status` and `marked_for_approval` columns

## Capabilities

### New Capabilities

(none - this is a bugfix/hardening change, not a new feature)

### Modified Capabilities

- `csv-upload`: Fix currency conversion precision and dedup key scope
- `inbox-review`: Fix XSS in edit endpoints, add null checks, validate query params
- `transaction-browsing`: Validate query params (page, page_size, dates)
- `combo-box`: Fix JSON injection in hx-vals, escape LIKE wildcards
- `account-management`: Fix XSS in edit endpoints, add null checks

## Impact

- **Files**: `main.py`, `ingest.py`, `db.py`, `models.py`, `_combo_results.html`, `_txn_table_body.html`, `inbox.html`, and 6+ new template partials for edit widgets
- **Behavior**: Some edge cases that previously crashed will now return 404 or use safe defaults. Dedup behavior changes (tighter key) could affect re-imports of existing data.
- **Dependencies**: None added
