## Why

The data pages (categories, import history, external accounts, importers) each have separate table templates with duplicated markup and styling. As new data pages are added, this duplication grows. A single, extensible generic table component eliminates repetition and makes it easier to maintain consistent styling and behavior across all data views.

## What Changes

- Create `_data_table.html` — a reusable table template that accepts column definitions
- Replace `_data_categories.html`, `_data_imports.html`, `_data_external_accounts.html`, and `_data_importers.html` with calls to the generic component
- Update route handlers to construct column definitions instead of rendering separate templates
- Support multiple cell rendering types (text, editable, link, badge, date, null-safe) via a declarative column schema

## Capabilities

### New Capabilities

None — this is a refactoring. User-facing behavior remains unchanged.

### Modified Capabilities

None — no requirement changes. This consolidates implementation details only.

## Impact

- **Templates**: Consolidates 4 separate data table templates into 1 generic component
- **Routes** (`src/pipances/routes/data.py`): Updates context building for categories, imports, external_accounts, and importers pages
- **Internal**: No API or database changes; internal implementation only
