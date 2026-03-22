## Why

The project has zero tests - no unit tests, no integration tests, no end-to-end tests. There is no pytest dependency, no test recipe in the justfile, and no CI pipeline. Every change is a risk because there's nothing to catch regressions. The upcoming security fixes and architecture refactor (splitting a 1445-line god module) especially need a safety net. Tests should go first so the fixes and refactor can be validated against them.

## What Changes

- Add pytest, httpx (for async FastAPI testing), and pytest-asyncio as dev dependencies
- Add a `just test` recipe to the justfile
- Add a `conftest.py` with fixtures for an in-memory test database, test client, and seeded data
- Write unit tests for core business logic: `ingest.py` (dedup, amount conversion), `_compute_date_range()` (boundary conditions), `charts.py` (empty/single-row DataFrames), `predict.py` (empty training data, single sample)
- Write integration tests for route handlers: status codes, validation failures, HTMX vs non-HTMX responses, null ID handling
- Write tests for `db.py` migration idempotency
- Add a `just check` update to include test execution

## Capabilities

### New Capabilities

(none - tests are infrastructure, not user-facing capabilities)

### Modified Capabilities

(none - tests don't change behavior, they verify it)

## Impact

- **Files**: New `tests/` directory with `conftest.py` and test modules, `justfile` updates
- **Dependencies**: `pytest`, `httpx`, `pytest-asyncio` added to dev dependency group
- **No production code changes** - this is purely additive
