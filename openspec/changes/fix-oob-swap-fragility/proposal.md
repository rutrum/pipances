## Why

The codebase uses HTMX out-of-band (OOB) swaps in three fragile patterns: string replacement on ID attributes, hand-constructed HTML strings, and CSS class string matching. All use post-render manipulation, causing silent failures when templates change. This violates HTMX's design philosophy (OOB attributes should be in the response markup itself) and makes refactoring risky and hard to maintain.

## What Changes

- Eliminate all string-based OOB injection (`str.replace()` on IDs, classes, or HTML fragments)
- Move OOB logic into templates with conditional attribute rendering (`{% if oob %}hx-swap-oob="..."{% endif %}`)
- Create reusable templates for hand-constructed fragments (toast, badge, etc.)
- Update all routes that generate OOB responses to pass `oob=True` parameter instead of post-processing
- Maintain 100% functional equivalence — no behavior changes, only implementation improvements

## Capabilities

### New Capabilities
- `oob-template-pattern`: Template-based OOB swap pattern using conditional rendering. Enables safe, maintainable OOB responses aligned with HTMX design principles.

### Modified Capabilities
- `html-rendering`: Response rendering now supports `oob` parameter to conditionally include `hx-swap-oob` attributes in templates.

## Impact

- **Routes affected**: `inbox.py`, `transactions.py`, `explore.py` (removes ~10 lines of string manipulation)
- **Templates affected**: `_pagination.html`, `_transaction_row.html`, `_explore_date_range.html`, plus new templates `_toast.html`, `_badge.html`
- **Database**: None
- **Dependencies**: None (uses existing Jinja2 conditional rendering)
- **Breaking changes**: None (refactor only, behavior unchanged)
