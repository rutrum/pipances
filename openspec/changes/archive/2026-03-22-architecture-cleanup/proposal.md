## Why

`main.py` has magic strings for transaction status and account kind, dead code (`get_session()`, `__init__.py` boilerplate), duplicate pagination templates, and pure utility functions mixed in with route handlers. These structural issues make the code harder to maintain and more error-prone. With a test suite in place (from the prior change), this cleanup can proceed safely.

## What Changes

- Create `StrEnum` types for transaction status (`"pending"`, `"approved"`) and account kind (`"checking"`, `"savings"`, `"credit_card"`, `"external"`)
- Replace all magic strings with the enum values
- Remove dead code: `get_session()` in `db.py`, `hello()` in `__init__.py`
- Extract pure utility functions (`_compute_date_range`, `_safe_int`, `_safe_date`, `_escape_like`) into `utils.py`
- Unify `_pagination.html` and `_inbox_pagination.html` into a single parameterized template using Jinja2 variable passing

## Out of Scope

- **Route split** — deferred to a separate `route-split` change (depends on this one landing first)
- **OOB swap refactoring** — deferred to TODO.md; the proper fix is template-level `oob=True` parameters, not a wrapper function

## Capabilities

### New Capabilities

(none — this is a refactor, no new user-facing behavior)

### Modified Capabilities

(none — behavior is unchanged, only internal structure changes)

## Impact

- **Files**: `models.py` gains enums, `db.py` loses dead code, `__init__.py` cleaned up, new `utils.py`, 2 pagination templates merged into 1
- **Dependencies**: None added or removed
- **Breaking**: None (internal-only changes)
- **Risk**: Low. Enums and utils extraction are mechanical. Test suite validates correctness.
