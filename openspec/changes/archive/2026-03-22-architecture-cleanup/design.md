## Context

`main.py` is ~1470 lines containing route handlers, helper functions, and constants. The codebase uses magic strings for status/kind, has dead code, and has two near-identical pagination templates. The test suite from the prior change provides a safety net for this cleanup.

## Goals / Non-Goals

**Goals:**
- Eliminate magic strings with enums
- Remove all dead code
- Extract pure utility functions into `utils.py`
- Reduce template duplication (unified pagination)

**Non-Goals:**
- Splitting routes into modules (separate `route-split` change)
- Changing any user-facing behavior
- Refactoring OOB swap patterns (deferred to TODO.md)
- Changing the database schema

## Decisions

### 1. StrEnum for status and account kind

**Decision**: Add enums to `models.py`:

```python
class TransactionStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"

class AccountKind(StrEnum):
    CHECKING = "checking"
    SAVINGS = "savings"
    CREDIT_CARD = "credit_card"
    EXTERNAL = "external"
```

Use `StrEnum` so values serialize to strings naturally with SQLAlchemy/SQLite. The `kind` field on Account stays as `String` in the DB (not a SQL enum) since users can already type any kind, but the sentinel value `"external"` becomes `AccountKind.EXTERNAL`.

**Rationale**: `StrEnum` is stdlib (3.11+), zero dependencies, and values work as strings everywhere. We don't need to constrain all kind values to the enum (users can type custom kinds), just the special sentinel.

### 2. Utils module for pure functions

**Decision**: Create `src/financial_pipeline/utils.py` and move pure, independently testable functions there:
- `compute_date_range()` (renamed from `_compute_date_range`, made public)
- `_safe_int()`, `_safe_date()`, `_escape_like()` (from security fixes change)

**Not moved** (too coupled to the route layer, will move naturally during route-split):
- `shared_context()` — needs async session
- `_transactions_to_df()` — builds DataFrames for routes
- `SORT_COLUMNS` — route-specific constant

**Rationale**: Only extract functions that are pure and independently useful. Don't shuffle route-coupled code into a utils file just to shrink main.py — that's the route-split's job.

### 3. Unified pagination template

**Decision**: Replace `_pagination.html` and `_inbox_pagination.html` with a single `_pagination.html` that uses Jinja2 template variables. The calling template sets variables before including:

```jinja2
{# In parent template: #}
{% set pagination_url = "/inbox" %}
{% set pagination_target = "#inbox-table" %}
{% set pagination_include = "#filter-bar" %}
{% include "_pagination.html" %}
```

The unified template uses `{{ pagination_url }}`, `{{ pagination_target }}`, `{{ pagination_include }}`.

**Rationale**: The two templates differ only in three values (`hx-get` URL, `hx-target`, `hx-include`). Variable passing is simpler than Jinja2 macro syntax and requires no changes to how partials are included.

### 4. Dead code removal

**Decision**: Delete:
- `db.py:get_session()` — never used
- `__init__.py:hello()` — scaffolding
- `charts.py:compute_stats()` `net_total` — redundant with `net`

**Rationale**: Dead code confuses readers and suggests patterns that aren't actually used.

## Risks / Trade-offs

- **StrEnum for kind is partial**: Only `"external"` is semantically important. Other kinds are user-defined. The enum doesn't constrain allowed values, it just provides constants.
  -> Mitigation: Document that AccountKind is for sentinel values, not exhaustive validation. The `kind` field stays a free-form string in the DB.

- **Moving functions changes import paths**: Tests that import `_compute_date_range` from `main` will need updating.
  -> Mitigation: The test suite change hasn't landed yet, so no existing tests to break. New tests will import from `utils`.
