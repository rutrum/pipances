## 1. Test Infrastructure

- [x] 1.1 Add `pytest`, `httpx`, `pytest-asyncio` to the `dev` dependency group in `pyproject.toml`
- [x] 1.2 Run `uv sync` to install the new dev dependencies
- [x] 1.3 Add `just test` recipe: `uv run pytest tests/ -v`
- [x] 1.4 Update `just check` recipe to also run `uv run pytest tests/`
- [x] 1.5 Create `tests/__init__.py` (empty)
- [x] 1.6 Create `tests/conftest.py` with fixtures: `engine`, `session`, `patch_db`, `client`, `seed_accounts`, `seed_categories`, `seed_import` (see design.md for details)
- [x] 1.7 Add CI/CD to TODO.md as a deferred item

## 2. Unit Tests: Ingest

- [x] 2.1 Create `tests/test_ingest.py` with all 9 test methods from design.md (amount conversion x3, dedup x4, phantom import, missing account)

## 3. Unit Tests: Date Range

- [x] 3.1 Create `tests/test_date_range.py` with all 9 test methods from design.md (each preset, boundary cases, custom, fallthrough)

## 4. Integration Tests: Routes

- [x] 4.1 Create `tests/test_routes.py` with all route test methods from design.md: inbox (5 tests + 3 commit workflow), transactions (2), upload (4), settings accounts (9), settings categories (5), dashboard (2), combo search (2)

## 5. Database Tests

- [x] 5.1 Create `tests/test_db.py` with both test methods from design.md (idempotency, migration adds columns)

## 6. Verification

- [x] 6.1 Run `just test` — 41 passed, 15 failed (real bugs, no xfail markers)
- [x] 6.2 Run `just check` — lint/format pass, tests fail with 15 known bugs
