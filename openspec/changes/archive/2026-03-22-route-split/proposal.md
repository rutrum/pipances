## Why

`main.py` is ~1530 lines containing all 30+ route handlers. As the project grows (drill-down pages, manual transactions, external account management, importer config), this file will only get larger. Splitting routes into focused modules improves navigability for both humans and agents editing code -- smaller files mean more targeted reads and fewer accidental side effects.

This is scoped to the route split only. Enums, dead code removal, utils extraction, and pagination unification are handled in the architecture-cleanup change (prerequisite).

## What Changes

- Split route handlers from `main.py` into modules using FastAPI `APIRouter`:
  - `routes/dashboard.py` -- `/dashboard`, `/dashboard/content`, tab renderers
  - `routes/inbox.py` -- `/inbox`, `/inbox/commit-summary`, `/inbox/commit`
  - `routes/settings.py` -- `/settings/*`, `/accounts/*`, `/categories/*`
  - `routes/transactions.py` -- `/transactions`, `/transactions/bulk` PATCH, `/transactions/{txn_id}` PATCH, edit-field endpoints
  - `routes/upload.py` -- `/upload` GET + POST
  - `routes/widgets.py` -- `/api/combo/{entity}` (shared combobox search)
- `main.py` becomes the app shell: app creation, lifespan, static files, router mounting, index redirect
- Create `routes/_utils.py` for web-layer shared concerns: `Jinja2Templates` instance, `shared_context()`, template path constants
- Private helper functions that serve a single route module move with that module
- Pure utility functions (`_safe_int`, `_safe_date`, etc.) are imported from the top-level `utils.py` (created by architecture-cleanup)

## Capabilities

### New Capabilities

(none -- this is a structural refactor, no new user-facing behavior)

### Modified Capabilities

(none -- behavior is unchanged, only internal file organization changes)

## Impact

- **Files**: `main.py` shrinks from ~1530 to ~50 lines; 6 new route modules + 1 `_utils.py` created in `routes/` package
- **Dependencies**: None added or removed
- **Breaking**: Module import paths change internally (no external consumers)
- **Risk**: Must preserve all route behavior exactly. Test suite validates this.
- **Prerequisite**: Architecture-cleanup change must land first (enums, utils, pagination) so the split operates on cleaner code
