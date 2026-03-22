## Context

`main.py` is ~1530 lines with all route handlers, helper functions, and constants. After architecture-cleanup lands (enums, `utils.py`, unified pagination), the remaining work is purely organizational: moving route handlers into focused modules using FastAPI's `APIRouter`.

## Goals / Non-Goals

**Goals:**
- Split routes into cohesive modules by feature area
- Establish a `routes/` package with clear conventions
- Provide shared web-layer utilities via `routes/_utils.py`
- Reduce `main.py` to an app shell (~50 lines)

**Non-Goals:**
- Changing any user-facing behavior or URLs
- Refactoring route handler logic
- Adding new endpoints or templates
- Changing the database schema

## Decisions

### 1. Module organization

**Decision**: Create `src/financial_pipeline/routes/` with these modules:

```
routes/
  __init__.py       # empty
  _utils.py         # shared web-layer concerns
  dashboard.py      # /dashboard, /dashboard/content
  inbox.py          # /inbox, /inbox/commit-summary, /inbox/commit
  settings.py       # /settings/*, /accounts/*, /categories/*
  transactions.py   # /transactions, /transactions/bulk, /transactions/{txn_id}/*
  upload.py         # /upload GET + POST
  widgets.py        # /api/combo/{entity}
```

**Rationale**: Each module maps to a page or feature area. `widgets.py` holds shared HTMX partial endpoints (currently just combo search) that aren't tied to a specific page.

### 2. Transaction endpoints stay together

**Decision**: All `/transactions/*` endpoints live in `routes/transactions.py`, including:
- `GET /transactions` (transactions page)
- `PATCH /transactions/bulk` (bulk update)
- `PATCH /transactions/{txn_id}` (single update)
- `GET /transactions/{txn_id}/edit-*` (inline edit partials)

**Rationale**: These endpoints share a URL namespace and will grow together as the transactions page gains features. Even though they're currently invoked from inbox templates, the URL coupling is the right organizational boundary.

### 3. `routes/_utils.py` for web-layer shared concerns

**Decision**: Create `routes/_utils.py` containing:
- `templates` -- the `Jinja2Templates` instance
- `TEMPLATES_DIR` -- path constant for template directory
- `shared_context()` -- async function returning base template context (accounts, categories, active page)

The underscore prefix signals this is internal to the routes package, not a router module.

**Rationale**: Every route module needs the templates instance and `shared_context()`. Putting them in a central location within `routes/` avoids circular imports and keeps `main.py` clean. Pure utilities (`safe_int`, etc.) stay in the top-level `utils.py` from architecture-cleanup.

### 4. Router registration pattern

**Decision**: Each route module creates its own `APIRouter()` at module level. `main.py` imports and includes them:

```python
from financial_pipeline.routes.dashboard import router as dashboard_router
# ...
app.include_router(dashboard_router)
```

No URL prefixes on `include_router()` -- each route module defines its full paths in the decorators, keeping URLs visible where they're defined.

**Rationale**: Full paths in decorators makes it easy to grep for a URL and find its handler. Prefix-based mounting splits the URL across two locations, making it harder to trace.

### 5. Helper function placement

**Decision**:
- **Module-specific helpers** move with their route module (e.g., `_dashboard_query()`, `_render_categories_tab()` stay with `dashboard.py`)
- **Shared web helpers** go in `routes/_utils.py` (e.g., `shared_context()`)
- **Pure utilities** imported from top-level `utils.py` (e.g., `safe_int()`, `compute_date_range()`)

**Rationale**: Functions live at the narrowest scope that covers their callers. No function should be in a module that doesn't use it.

## Risks / Trade-offs

- **Import complexity increases**: Route modules import from `routes._utils`, `utils`, `models`, `db`, `charts`, `ingest`. More files means more import statements.
  -> Mitigation: This is the standard cost of modularization. Each file is self-contained and imports are explicit.

- **Template references unchanged**: Templates use URL paths (`hx-get="/transactions/..."`) that span module boundaries (inbox templates reference transaction endpoints).
  -> Mitigation: URLs don't change, so templates work without modification. This is normal for HTMX apps.

- **Merge conflicts with parallel changes**: If other changes modify `main.py` concurrently, the split will conflict.
  -> Mitigation: Land architecture-cleanup first, then apply route-split before starting new feature work.
