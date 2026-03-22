## Context

The project has zero tests and no testing infrastructure. The tech stack is FastAPI + SQLAlchemy async + SQLite + Polars. Tests need to handle async code, database isolation, and HTMX-specific response patterns (OOB swaps, HX-Request header).

A code review (PR_REVIEW.md) identified several known bugs. Tests should target the *correct* behavior and use `@pytest.mark.xfail` where the current code has a known bug that will be fixed in a subsequent change. This way, the xfails flip to passes after the fix lands, confirming it worked.

## Goals / Non-Goals

**Goals:**
- Establish testing infrastructure (fixtures, conftest)
- Cover core business logic with unit tests (ingest, date range)
- Cover route handlers with integration tests (validation failures, null IDs, commit workflow, upload errors)
- Make `just test` the standard way to run tests
- Focus test density where bugs are most likely and most costly: data ingestion, currency math, input validation, and the commit workflow

**Non-Goals:**
- 100% code coverage (focus on high-value areas)
- End-to-end browser tests (agent-browser covers this manually)
- Performance/load testing
- Testing chart rendering or ML prediction (these wrap Altair/scikit-learn -- testing library behavior, not ours)
- CI/CD pipeline (deferred to TODO.md)

## Decisions

### 1. Test database: in-memory SQLite per test

**Decision**: Each test gets a fresh in-memory SQLite database via a pytest fixture that creates tables and yields a session. No file-based DB, no shared state between tests.

**Rationale**: Fast, isolated, no cleanup needed. The async engine is created with `sqlite+aiosqlite:///:memory:`.

**Alternative considered**: Temp file DB. Rejected because in-memory is faster and simpler for unit/integration tests.

### 2. Override the session via monkey-patch

**Decision**: The test fixtures monkey-patch `db.async_session` with a test session maker bound to the in-memory engine. This is necessary because the codebase uses `async_session()` directly everywhere (not FastAPI dependency injection).

**Rationale**: The cleanest approach given the current architecture. The architecture-cleanup change may introduce proper DI later, at which point tests can use `app.dependency_overrides`.

### 3. httpx.AsyncClient for route testing

**Decision**: Use `httpx.AsyncClient` with FastAPI's `ASGITransport` for testing route handlers. This allows testing async endpoints without running a server.

**Rationale**: This is the standard FastAPI testing approach. It handles ASGI lifecycle, allows setting custom headers (like `HX-Request: true`), and doesn't require a running server.

### 4. Test file organization and content

**Decision**: Place tests in `tests/` at project root. One test file per logical area. The guiding principle: **test the things that handle money, user input, and data boundaries -- don't test obvious CRUD or library wrappers**.

Below is each test module with its specific test methods and why each exists.

---

#### `tests/conftest.py` -- Shared Fixtures

```
Fixtures:
  engine          -- Creates in-memory async SQLite engine, runs create_tables(), tears down after test
  session         -- Yields an AsyncSession bound to the test engine
  patch_db        -- Monkey-patches db.async_session to use test engine (auto-used)
  client          -- httpx.AsyncClient wrapping the FastAPI app
  seed_accounts   -- Creates Checking + Savings + Credit Card internal accounts, returns dict[name -> Account]
  seed_categories -- Creates a few categories (Groceries, Dining, etc.), returns dict[name -> Category]
  seed_import     -- Creates an Import record, returns it
```

Why: Every integration test needs a client and database. Seed fixtures avoid repeating account/category creation in every test file. Keeping them composable (not one giant "seed everything" fixture) lets unit tests use only what they need.

---

#### `tests/test_ingest.py` -- Ingestion & Dedup Logic

This is the highest-priority test module. Currency math errors and dedup bugs silently corrupt financial data.

```
test_amount_conversion_rounds_correctly
    Ingest a row with amount=19.99, verify amount_cents=1999.
    xfail: current code uses int(amount*100) which truncates. (PR_REVIEW 2.1)

test_amount_conversion_negative
    Ingest amount=-45.67, verify amount_cents=-4567.

test_amount_conversion_exact
    Ingest amount=10.00, verify amount_cents=1000 (no rounding issue).

test_same_file_duplicates_both_inserted
    Ingest a DataFrame with two identical rows. Both should be inserted
    (same-file dupes are real transactions like two coffee purchases).

test_cross_import_duplicates_skipped
    Ingest a DataFrame, then ingest the same DataFrame again.
    Second import should insert 0 new rows.

test_cross_import_partial_overlap
    First import: 3 rows. Second import: 2 of the same + 1 new.
    Should insert only the 1 new row.

test_cross_account_not_deduplicated
    Ingest same (date, amount, description) for "Checking", then for "Savings".
    Both should be inserted -- different accounts are different transactions.
    xfail: current dedup key doesn't include internal account. (PR_REVIEW 2.2)

test_all_duplicates_creates_phantom_import
    Ingest a DataFrame, then re-ingest the same DataFrame.
    Verify an Import record is created even though 0 rows were inserted.
    This documents the current behavior (PR_REVIEW 2.5) -- a future fix
    could change this to not create the phantom record.

test_missing_internal_account_raises
    Ingest with internal_account="NonExistent". Should raise ValueError.
```

Why each test: The first three nail down currency precision (the #1 data corruption risk). The dedup tests cover the three key scenarios from the count-based dedup algorithm. The cross-account test catches the known scoping bug. The phantom import test documents a data cleanliness issue. The last test covers basic error handling.

---

#### `tests/test_date_range.py` -- Date Range Computation

This is a pure function with tricky edge cases around month boundaries.

```
test_preset_all
    Returns (None, None).

test_preset_ytd
    Returns (Jan 1 of current year, today).

test_preset_last_month
    Freeze to 2026-03-15. Returns (2026-02-01, 2026-02-28).

test_preset_last_month_january
    Freeze to 2026-01-10. Returns (2025-12-01, 2025-12-31).

test_preset_last_3_months
    Freeze to 2026-03-15. Returns (2025-12-01, 2026-03-15).

test_preset_last_year
    Freeze to 2026-03-15. Returns (2025-01-01, 2025-12-31).

test_preset_custom_valid
    preset="custom", date_from="2026-01-01", date_to="2026-02-28".
    Returns those exact dates.

test_preset_custom_missing_dates
    preset="custom" with no date_from/date_to. Should fall through to YTD default.

test_unrecognized_preset
    preset="bogus". Should fall through to YTD default.
```

Why: Each preset is a distinct code path. The January boundary test catches off-by-one in month subtraction. The custom fallthrough tests verify graceful degradation.

---

#### `tests/test_routes.py` -- Route Handler Integration Tests

One file for all route tests. Grouped by area within the file. Focus: input validation, error handling, status codes, and critical workflows. NOT testing template rendering correctness.

```
# --- Inbox ---
test_inbox_get_200
    GET /inbox returns 200.

test_inbox_invalid_page_param
    GET /inbox?page=abc returns 200 (not 500).
    xfail: current code has bare int() conversion. (PR_REVIEW 4.1)

test_inbox_negative_page_size
    GET /inbox?page_size=-1 returns 200.
    xfail: current code has no page_size validation. (PR_REVIEW 4.2)

test_inbox_invalid_date_filter
    GET /inbox?date_from=not-a-date returns 200 (ignores bad date).
    xfail: current code has bare date.fromisoformat(). (PR_REVIEW 4.3)

test_inbox_invalid_internal_id_filter
    GET /inbox?internal_id=abc returns 200 (not 500).
    xfail: current code has bare int() on internal_id. (PR_REVIEW 4.1)

test_edit_description_nonexistent_txn
    GET /transactions/99999/edit-description returns 404.
    xfail: current code crashes with AttributeError. (PR_REVIEW 4.4)

test_edit_external_nonexistent_txn
    GET /transactions/99999/edit-external returns 404.
    xfail: current code crashes. (PR_REVIEW 4.4)

test_edit_category_nonexistent_txn
    GET /transactions/99999/edit-category returns 404.
    xfail: current code crashes. (PR_REVIEW 4.4)

# --- Inbox: Commit Workflow ---
test_commit_no_marked_transactions
    POST /inbox/commit with no marked transactions returns HTML with warning.

test_commit_marked_transactions_approved
    Seed pending transactions, mark some for approval via PATCH, then POST /inbox/commit.
    Verify the marked transactions change status to "approved".

test_commit_unmarked_transactions_remain_pending
    Seed pending transactions, mark only some, commit.
    Verify unmarked transactions remain "pending".

# --- Transactions ---
test_transactions_get_200
    GET /transactions returns 200.

test_transactions_invalid_page
    GET /transactions?page=abc returns 200.
    xfail: same bare int() issue. (PR_REVIEW 4.1)

# --- Upload ---
test_upload_page_get_200
    GET /upload returns 200.

test_upload_missing_file
    POST /upload with importer+account but no file. Should return 422 (not 500).
    xfail: current code crashes on file.read() when file is None. (PR_REVIEW 4.6)

test_upload_unknown_importer
    POST /upload with importer="nonexistent". Should return 422 with error message.

test_upload_error_does_not_leak_internals
    POST /upload with a file that causes a parse error. Verify the error response
    does not contain Python traceback or internal exception class names.
    xfail: current code renders raw exception as HTML. (PR_REVIEW 4.5)

# --- Settings: Accounts ---
test_settings_accounts_get_200
    GET /settings/accounts returns 200.

test_create_account_valid
    POST /settings/accounts with name+kind returns 200 and creates the account.

test_create_account_missing_name
    POST /settings/accounts with no name returns 422.

test_create_account_external_kind_rejected
    POST /settings/accounts with kind="external" returns 422.

test_create_account_duplicate_name
    Create an account, then POST with the same name. Returns 422.

test_edit_account_name_nonexistent
    GET /accounts/99999/edit-name returns 404.
    xfail: current code crashes. (PR_REVIEW 4.4)

test_edit_account_type_nonexistent
    GET /accounts/99999/edit-type returns 404.
    xfail: current code crashes. (PR_REVIEW 4.4)

test_edit_account_balance_nonexistent
    GET /accounts/99999/edit-balance returns 404.
    xfail: current code crashes. (PR_REVIEW 4.4)

test_edit_account_balance_date_nonexistent
    GET /accounts/99999/edit-balance-date returns 404.
    xfail: current code crashes. (PR_REVIEW 4.4)

test_update_account_nonexistent
    PATCH /accounts/99999 returns 404.

# --- Settings: Categories ---
test_settings_categories_get_200
    GET /settings/categories returns 200.

test_create_category_valid
    POST /settings/categories with name returns 200.

test_create_category_empty_name
    POST /settings/categories with empty name returns 422.

test_delete_category
    Create category, DELETE it, verify 200 and gone.

test_edit_category_name_nonexistent
    GET /categories/99999/edit-name returns 404.
    xfail: current code crashes. (PR_REVIEW 4.4)

# --- Dashboard ---
test_dashboard_get_200
    GET /dashboard returns 200.

test_dashboard_redirect_from_root
    GET / returns redirect to /dashboard.

# --- Combo Search ---
test_combo_search_with_percent
    GET /api/combo/categories?q=%25 returns 200 (doesn't match everything).
    xfail: current code doesn't escape LIKE wildcards. (PR_REVIEW 1.3)

test_combo_search_with_underscore
    GET /api/combo/categories?q=_ returns 200 (doesn't match all single chars).
    xfail: current code doesn't escape LIKE wildcards. (PR_REVIEW 1.3)
```

Why this scope: Every test catches either (a) a known bug from PR_REVIEW (xfail), (b) a validation gap that causes 500s, or (c) a critical workflow (commit). The combo search tests cover the LIKE injection. The upload tests cover missing field and error leakage. The commit tests cover the most important state transition in the app. All edit-* endpoints for accounts are tested (4 of them), not just edit-name.

---

#### `tests/test_db.py` -- Migration Idempotency

```
test_create_tables_idempotent
    Call create_tables() twice. Second call should not error.

test_migration_adds_missing_columns
    Create tables with a schema missing the newer columns (starting_balance_cents, etc.),
    then call create_tables(). Verify the columns exist afterward.
```

Why: The hand-rolled migration in db.py is fragile. These tests catch regressions when new ALTER TABLE statements are added.

---

## Risks / Trade-offs

- **Monkey-patching `db.async_session`**: Slightly fragile since it depends on module-level state. If the codebase later moves to proper dependency injection, the test approach can be simplified.
  -> Mitigation: Document the pattern in conftest.py. The architecture-cleanup change could introduce proper DI later.

- **Tests for current behavior may codify bugs**: Some current behavior is wrong (e.g., float truncation). Tests are written for the *correct* behavior and marked with `@pytest.mark.xfail` for known bugs that will be fixed in the security change.
  -> Mitigation: Use xfail markers with clear comments linking to PR_REVIEW.md findings.

- **Freezing dates in date range tests**: `_compute_date_range` calls `date.today()` internally. Tests need to either freeze time (e.g., `freezegun`) or accept that YTD results change over time.
  -> Decision: Use `unittest.mock.patch` to mock `date.today()` rather than adding a `freezegun` dependency. Keep it simple.
