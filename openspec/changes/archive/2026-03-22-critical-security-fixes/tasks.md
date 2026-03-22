## 1. Input Validation Helpers

- [x] 1.1 Add `_safe_int(value, default, min_val=None, max_val=None)` helper to `main.py` that wraps `int()` in try/except and clamps to range
- [x] 1.2 Add `_safe_date(value)` helper to `main.py` that wraps `date.fromisoformat()` in try/except, returns None on failure
- [x] 1.3 Replace all bare `int(params.get(...))` calls in inbox_page and transactions_page with `_safe_int`, clamping page_size to 1-100
- [x] 1.4 Replace all bare `date.fromisoformat()` calls on user input in inbox_page, transactions_page, create_account, and update_account with `_safe_date`

## 2. Fix Currency Conversion

- [x] 2.1 Change `ingest.py:102` from `int(row["amount"] * 100)` to `int(round(row["amount"] * 100))`

## 3. Fix Dedup Key Scope

- [x] 3.1 Add `internal_account` to the dedup key in `ingest.py`: change key from `(date, amount_cents, description)` to `(date, amount_cents, description, internal_account)`
- [x] 3.2 Update the database count query to also filter by `Transaction.internal_id == internal.id`

## 4. XSS Fixes: Move f-string HTML to Templates

- [x] 4.1 Create `_edit_input.html` template partial for the text/number/date edit inputs (parameterized by field name, value, type, endpoint, target)
- [x] 4.2 Refactor `edit_account_name`, `edit_account_type`, `edit_account_balance`, `edit_account_balance_date` to use the new template partial instead of f-strings
- [x] 4.3 Refactor `edit_category_name` to use the new template partial
- [x] 4.4 Refactor `edit_description` to use the new template partial
- [x] 4.5 Fix the upload error handler (`main.py:401-405`) to HTML-escape the exception message using `html.escape(str(e))`

## 5. XSS Fixes: Template Escaping

- [x] 5.1 Fix `inbox.html` toast script: change bare `{{ value }}` to `{{ value|tojson }}` for all values interpolated into JavaScript
- [x] 5.2 Fix `_combo_results.html` hx-vals: build the dict properly and render with `|tojson` filter
- [x] 5.3 Fix `_txn_table_body.html` filter header hx-vals: render filter values safely with `|tojson` or pre-escaped dicts

## 6. Null Checks on Edit Endpoints

- [x] 6.1 Add null check (return 404 if None) after `session.get()` in `edit_account_name`, `edit_account_type`, `edit_account_balance`, `edit_account_balance_date`
- [x] 6.2 Add null check after `session.get()` in `edit_category_name`
- [x] 6.3 Add null check after `session.get()` in `edit_description`
- [x] 6.4 Add null check after `session.get()` in `edit_external`
- [x] 6.5 Add null check after `session.get()` in `edit_category`

## 7. SQL LIKE Wildcard Escaping

- [x] 7.1 Add a `_escape_like(q)` helper that escapes `%`, `_`, and `\` in the search query
- [x] 7.2 Apply `_escape_like()` in `combo_search` before the `ilike()` calls

## 8. Database Hardening

- [x] 8.1 Add SQLAlchemy engine event listener in `db.py` to execute `PRAGMA foreign_keys = ON` on every new connection
- [x] 8.2 Add `server_default` to `Transaction.status` (value `"pending"`) and `Transaction.marked_for_approval` (value `"0"`) in `models.py`

## 9. Verification

- [x] 9.1 Run `just check` — lint passes, all 56 tests pass
- [x] 9.2 Run `just seed && just serve` and manually verify edit endpoints work with the new templates
