## Context

Currently, the data pages (categories, imports, external accounts, importers) each have their own template file with duplicated table markup and styling. As the application grows and more data pages are added, this template duplication increases maintenance burden and makes it harder to ensure consistent behavior and styling.

## Goals / Non-Goals

**Goals:**
- Create a single, reusable `_data_table.html` component that consolidates all data table rendering
- Support declarative column definitions that specify rendering behavior (text, editable, link, badge, date, null-safe)
- Eliminate template duplication across categories, imports, external accounts, and importers pages
- Make it easy to add new cell rendering types without modifying the base template
- Make it simple to add new data pages using the same component

**Non-Goals:**
- Add new user-facing features or capabilities
- Change database schema or models
- Support complex multi-row interactions (sorting, grouping, etc.)
- Implement pagination or filtering at the component level (these remain page-level concerns)

## Decisions

### 1. Column Definition Schema (Text, Link, Editable, Badge, Date, Null-Safe)

**Decision**: Each column is defined as a dictionary with `key`, `label`, `type`, and type-specific properties. The template uses a Jinja2 macro `render_cell(row, col)` with conditional branches for each type.

**Rationale**: 
- Declarative approach keeps rendering logic in one place (the macro) rather than scattered across templates
- Type system is self-documenting and extensible
- Routes can trivially build column definitions without string manipulation

**Alternatives considered**:
- Separate templates per cell type (`_cell_text.html`, `_cell_link.html`, etc.) — more modular but verbose and slower to render
- Route-level HTML generation — loses template ownership and makes styling harder to maintain

### 2. No Header in Component

**Decision**: The `_data_table.html` component renders only the table (thead + tbody), not the section header or empty-state message.

**Rationale**:
- Each data page has its own semantics for section titles and empty state messages
- This keeps the component focused and reusable
- Routes handle passing `title` and `empty_message` as context variables, rendered by the data page partial

**Alternatives considered**:
- Include title/empty-state in the component — requires more parameters and makes component less flexible

### 3. Extensible via Type Branches

**Decision**: The `render_cell` macro checks `col.type` and renders accordingly. New cell types are added as new `elif` branches.

**Rationale**:
- Low friction to add new types (one new branch in the macro)
- All rendering logic is in one macro, easy to review and maintain
- Future types (status_badge, actions, number_formatted, raw_html) follow the same pattern

**Alternatives considered**:
- Separate template files for each cell type — more files to maintain, slower
- Using separate partials and `{% include %}` — adds indirection and template lookup overhead

### 4. Row ID Support

**Decision**: Component accepts optional `row_id_key` parameter. If provided, rows are wrapped in `<tr id="{{ row_id_key }}-{{ row[row_id_key] }}">` for HTMX targeting.

**Rationale**:
- Needed for inline editing (e.g., categories) where HTMX replaces a row by ID
- Optional to keep component simple for static tables (imports)
- Naming convention is predictable (`id-123`, `category-456`)

**Alternatives considered**:
- Always require row IDs — forces unnecessary IDs on static tables
- Pass the full ID template as a parameter — more verbose

### 5. Column Key-Based Cell Access

**Decision**: Cells are populated via `row[col.key]`, assuming rows are dictionaries or objects with attribute/key access.

**Rationale**:
- Works with SQLAlchemy objects (attribute access), Dicts (key access), and tuples/NamedTuples
- Jinja2 handles all these transparently
- Simple and doesn't require row transformation

**Alternatives considered**:
- Require rows to be dictionaries only — too restrictive, breaks with SQLAlchemy ORM
- Pass pre-rendered cells instead of raw data — loses flexibility and makes future type additions hard

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| Column schema becomes complex as more types are added | Document each type clearly with examples; keep new types focused and orthogonal |
| Routes must construct column definitions (more context boilerplate) | This is acceptable; it's explicit and clear. Routes declare their table schema |
| If type logic grows, the macro becomes large | Refactor into separate macros if any one type becomes complex (e.g., `render_editable_cell`, `render_link_cell`) |
| Future changes to one table might accidentally affect others | All tables use the same component, so changes are centralized. Test coverage on the macro is crucial |

## Migration Plan

1. Create `_data_table.html` with full `render_cell` macro supporting all 6 types
2. Create column definition context builders (helper functions) in routes for each page (optional but recommended)
3. Update each route handler to build column definitions instead of passing raw objects
4. Replace partial includes in templates with `{% include "_data_table.html" %}`
5. Remove old template files: `_data_categories.html`, `_data_imports.html`, `_data_external_accounts.html`, `_data_importers.html`
6. Rollback strategy: Not applicable for internal refactoring; if issues arise, revert commits

## Open Questions

- Should we create helper functions in routes (e.g., `_build_category_columns()`) to keep context building DRY, or keep it inline in route handlers?
