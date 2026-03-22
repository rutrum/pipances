## 1. Enums and Constants

- [x] 1.1 Add `TransactionStatus(StrEnum)` with `PENDING = "pending"` and `APPROVED = "approved"` to `models.py`
- [x] 1.2 Add `AccountKind(StrEnum)` with `CHECKING`, `SAVINGS`, `CREDIT_CARD`, `EXTERNAL` to `models.py`
- [x] 1.3 Replace all `"pending"` and `"approved"` string literals with `TransactionStatus.PENDING` / `.APPROVED` across `main.py`, `ingest.py`, `seed.py`
- [x] 1.4 Replace all `"external"` string literals with `AccountKind.EXTERNAL` across `main.py`, `ingest.py`, `seed.py`

## 2. Dead Code Removal

- [x] 2.1 Delete `get_session()` from `db.py`
- [x] 2.2 Replace `hello()` in `__init__.py` with empty file or just a version string
- [x] 2.3 Remove redundant `net_total` from `compute_stats()` in `charts.py` (keep only `net`)
- [x] 2.4 Update any templates or code referencing `net_total` to use `net`

## 3. Extract Utils Module

- [x] 3.1 Create `src/financial_pipeline/utils.py`
- [x] 3.2 Move `_compute_date_range()` to `utils.py` and make it public (`compute_date_range`)
- [x] 3.3 Move `_safe_int()`, `_safe_date()`, `_escape_like()` to `utils.py`
- [x] 3.4 Update all call sites in `main.py` to import from `utils`

## 4. Unify Pagination Templates

- [x] 4.1 Parameterize `_pagination.html` to use `{{ pagination_url }}`, `{{ pagination_target }}`, `{{ pagination_include }}` instead of hardcoded values
- [x] 4.2 Update inbox template to set pagination variables before `{% include "_pagination.html" %}`
- [x] 4.3 Update transactions template to set pagination variables before `{% include "_pagination.html" %}`
- [x] 4.4 Delete `_inbox_pagination.html`
- [x] 4.5 Update any Python code that renders inbox pagination to use the unified template name

## 5. Verification

- [x] 5.1 Run `just test` and verify all tests still pass
- [x] 5.2 Run `just check` and verify linting passes
- [x] 5.3 Run `just fmt` to fix any formatting issues
- [x] 5.4 Run `just seed && just serve` and spot-check that all pages render correctly
