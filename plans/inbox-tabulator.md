# Inbox Tabulator — Implementation Plan

A second, Tabulator-based inbox that lives alongside the existing HTMX inbox.
It is intended to **eventually replace** the original, so it is deliberately
self-contained: no shared modal template, no shared row template, no
abstraction layer between the two inboxes. Only genuinely neutral helpers
(query functions, `set_txn_*`, categories/external resolution) are reused.

## Goals

- Tabulator at the core, remote sort/pagination, matching the `/data/*` pattern.
- Inline spreadsheet-style editing of `description`, category, and external account.
- Range selection + clipboard: copy/highlight multiple cells, paste one value
  across many rows.
- Approve per row with an obvious highlight; Commit at the top is paramount.
- A new modal for the three scalar fields **and** category splits.
- Retrain button.
- No row checkboxes, no selection toolbar, no filters (for now).

## Locked decisions

| # | Decision |
|---|---|
| 1 | One new navbar entry with its own route. Proposed: `/inbox-tabulator`, label "Inbox Tabulator" (rename freely). |
| 2 | Range paste uses a custom `clipboardPasteAction` (built-in range parser kept), plus a batch PATCH. |
| 3 | Inline editing **and** the modal. Splits stay in the modal. |
| 4 | New modal template for the new page. Old modal untouched. |
| 5 | Commit summary/commit are JSON endpoints. |
| 6 | Raw description is its own column. |
| 7 | Mouse-only approve (no keyboard shortcut). |
| 8 | `selectableRangeClearCells` enabled, clear value `""`. |
| 9 | Batch endpoint is all-or-nothing. |
| 10 | Remote pagination/sort (consistent with `/data`). |
| 11 | Retrain included. |
| 12 | New table constants go in `Settings()` and are passed to JS via data attributes. |
| 13 | UI tests use real clipboard permissions with an API-level fallback. |

## Key technical finding driving the design

The bundled Tabulator 6.5.0 ships range clipboard as a module extension
(`SelectRangeModule.moduleExtensions`): `clipboardPasteParser: "range"`,
`clipboardPasteAction: "range"`, `clipboardCopyRowRange: "range"`. The range
parser already supports "paste one value across a multi-row range" by cycling
the pasted row object with modulo.

However, the built-in range paste action calls `row.updateData(...)`, which
uses `cell.setValueProcessData` and therefore **does not fire `cellEdited`**.
So the built-in paste never reaches the server. Inline editors and
`selectableRangeClearCells` do go through `cell.setValue` and **do** fire
`cellEdited`.

Consequence: `cellEdited` is the persistence path for inline edits and clear;
range paste needs its own custom action that applies changes locally and sends
one batch PATCH.

## Architecture

```
Browser (inbox-tabulator.js)
  POST /api/inbox/table                     <- remote sort/pagination
  PATCH /api/inbox/transactions/{id}        <- inline cell edit / approve toggle
  PATCH /api/inbox/transactions/batch       <- range paste (all-or-nothing)
  GET  /api/inbox/commit-summary            <- commit dialog data
  POST /api/inbox/commit                    <- commit marked rows
  POST /api/inbox/retrain                   <- retrain, returns updated count
  GET  /inbox-tabulator/transactions/{id}/edit-modal  <- new modal HTML
```

The existing `/inbox`, `/inbox/commit`, `/inbox/retrain`, `/transactions/*`
routes and templates are left exactly as they are.

## Files

New:

- `src/pipances/routes/inbox_tabulator.py` — page + modal HTML routes.
- `src/pipances/templates/pages/inbox_tabulator.jinja2` — page, toolbar, dialog markup.
- `src/pipances/templates/inbox/_inbox_tabulator_modal.jinja2` — new modal.
- `static/js/pages/inbox-tabulator.js` — table.
- `static/js/pages/inbox-tabulator-modal.js` — modal wiring.
- `tests/test_inbox_tabulator_api.py` — unit/API tests.
- `tests/ui/test_inbox_tabulator.py` — UI tests.

Modified:

- `src/pipances/routes/api/inbox.py` — new JSON endpoints.
- `src/pipances/routes/api/schemas.py` — request/response models.
- `src/pipances/routes/api/queries.py` — inbox row serializer fields.
- `src/pipances/db/transactions.py` — shared commit / retrain / summary helpers.
- `src/pipances/settings.py` — page size + options.
- `src/pipances/main.py` — register the new router.
- `src/pipances/templates/shared/_navbar.jinja2` — new entry.
- `static/css/tabulator-daisy.css` — approved row + range accents.

## Data shape

Extend `transaction_to_dict` (used by the new table endpoint) with flat fields
so Tabulator editors can bind to ids:

- `category_id`, `external_id` — currently only nested objects are emitted.
- `can_approve` — `bool(description and external_id)`.
- `split_count` — number of splits when loaded (`fetch_page(splits=True)`).

Keep the existing nested `category` / `external_account` / `internal_account` /
`ml_confidence` objects for formatters.

## Proposed endpoints (contract)

### `POST /api/inbox/table`

Body: `TabulatorRequest`. Response: `{last_page, last_row, data: [...]}`.
`fetch_page(statuses=(PENDING,), sorters=..., page=..., page_size=..., splits=True)`.
Filters are accepted but unused for now, matching the repo pattern.

### `PATCH /api/inbox/transactions/{id}`

Body (`InboxRowUpdate`), only provided fields applied:

- `description: str | None`
- `category_id: int | str | None` (id or name; name is create-or-get)
- `external_id: int | str | None`
- `marked_for_approval: bool | None`

Rules:

- `""` is treated as `None` (supports clear-cells).
- Field writes go through `set_txn_description` / `set_txn_category` /
  `set_txn_external`, which clear the ML confidence.
- Setting `marked_for_approval: true` validates description + external and
  returns 422 otherwise.
- Returns the same inbox row dict the table endpoint uses.

### `PATCH /api/inbox/transactions/batch`

Body: `{updates: [{id, description?, category_id?, external_id?}]}`.
All-or-nothing in one transaction: any invalid row rolls the whole request back
and returns 422. On success returns the updated rows. Deliberately excludes
`marked_for_approval` and any non-editable field.

### `GET /api/inbox/commit-summary`

`{count, new_categories: [...], new_externals: [...]}`. Logic extracted from the
existing `commit_summary` route into a shared function.

### `POST /api/inbox/commit`

Commits marked pending rows, prunes orphan external accounts, returns
`{committed, remaining}`.

### `POST /api/inbox/retrain`

Trains on approved rows, updates pending suggestions, returns
`{updated_count}`. Logic extracted from the existing `retrain_inbox` route.

### `GET /inbox-tabulator/transactions/{id}/edit-modal`

Returns the new modal partial. Reuses the existing category/external/description
loading helper (data only, not markup).

## Table configuration

```
height: "70vh"
layout: "fitColumns"
index: "id"
ajaxURL: "/api/inbox/table", ajaxConfig: "POST", ajaxContentType: "json"
pagination: true, paginationMode: "remote"
paginationSize: settings.inbox_default_page_size
paginationSizeSelector: settings.inbox_page_size_options
paginationCounter: "rows"
sortMode: "remote"
initialSort: [{column: "date", dir: "asc"}]
selectableRange: true
selectableRangeColumns: false
selectableRangeRows: false
selectableRangeClearCells: true
selectableRangeClearCellsValue: ""
clipboard: true
clipboardCopyRowRange: "range"
clipboardPasteParser: "range"
clipboardPasteAction: <custom function>
clipboardCopyStyled: false
clipboardCopyConfig: {columnHeaders: false, rowHeaders: false}
editTriggerEvent: "dblclick"
```

Columns: Date, Account, Amount, Raw Description, Description, Category,
External, Status/Actions.

- Description formatter: value or muted "no description", plus ML confidence dot.
- Category formatter: nested name or muted "no category", ML dot, and an
  `N splits` badge when `split_count > 0`.
- External formatter: nested name or muted "no external account", ML dot.
- Actions formatter: `Approve` / `Approved` button (disabled unless
  `can_approve` or already marked) and an `Edit` button that opens the modal.

`rowFormatter` toggles a `txn-approved` class from `marked_for_approval`.

## Range paste (custom action)

1. The built-in `"range"` parser produces row objects keyed by the visible
   fields under the selected range.
2. Our action replicates the range/row targeting logic (active rows, start/end
   bounds, modulo cycling), then:
   - filters to the allowlist `description`, `category_id`, `external_id`
     (ignores date/amount/raw/internal even if the range covers them);
   - applies `row.updateData(...)` inside `blockRedraw`/`restoreRedraw`;
   - collects `{id, field: value}` updates;
   - sends one `PATCH /api/inbox/transactions/batch`;
   - on success reconciles rows from the response;
   - on any failure reloads the table (`setData()`) and shows an error toast.
3. Values copied from the table are display strings (e.g. category name); the
   endpoint resolves id-or-name, so round-trips work unchanged.

Inline edits and clear-cells need no special casing: they fire `cellEdited`,
which reuses `PipancesEditors.saveCell` against the single-row endpoint.

## Modal

New partial, independent of the old inbox modal:

- `<dialog>` with the read-only context (date, amount, account, raw description).
- Description / category / external as Tom Select controls wired by
  `inbox-tabulator-modal.js` to JSON PATCH, then `table.updateRow(id, response)`.
- `{% include "shared/_splits_section.jinja2" %}` reused as-is: it is
  self-contained (Alpine + Tom Select + HTMX against the existing splits
  endpoints) and does not couple to the old table.
- Approve/unapprove button uses the JSON endpoint, updates the row, closes.
- On close, refetch the row (`GET /api/transactions/{id}`) and
  `table.updateRow(id, data)` so `split_count` and categories refresh.

## Approved + commit UX

- Clicking Approve optimistically flips `marked_for_approval` locally,
  re-runs the row formatter for the immediate highlight, updates the marked
  count, then PATCHes; on failure it reverts and toasts.
- `Commit` sits in the top toolbar and shows the marked count (server-rendered
  initial value, adjusted on toggles, refreshed after commit/retrain).
- Clicking Commit fetches the JSON summary and populates the dialog; Confirm
  POSTs `/api/inbox/commit`, then closes, toasts, updates `#inbox-badge`, and
  `table.setData()`.

## Settings additions

```python
inbox_default_page_size: int = 25
inbox_page_size_options: list[int] = [25, 50, 100]
```

Passed to the template and onto `#inbox-tabulator-root` as data attributes.

## Phases

### Phase 0 — Scaffolding

- Add settings fields.
- Add `routes/inbox_tabulator.py` with `GET /inbox-tabulator` rendering an empty
  page (extend `base.jinja2`), registered in `main.py`.
- Add navbar entry and `active_page="inbox_tabulator"`.

Acceptance: route renders, nav item highlights, old inbox unaffected.

### Phase 1 — Read-only table

- Add `POST /api/inbox/table` + serializer fields (`category_id`,
  `external_id`, `can_approve`, `split_count`).
- Build `inbox-tabulator.js` with columns, remote sort/pagination, formatters,
  `rowFormatter` (marked state visible even before approve is wired).
- Page markup: toolbar, root data attributes, containers.

Acceptance: table loads pending rows, sorts and paginates; unit tests for the
envelope, pending-only status, sort, pagination, and new fields.

### Phase 2 — Inline editing + clear

- Add single-row `PATCH /api/inbox/transactions/{id}`.
- Wire description `input`, category/external `tomSelect` (options fetched from
  `/api/categories` and `/api/external-accounts`, `create: true`), `cellEdited`
  to `saveCell`.
- Enable `selectableRangeClearCells` with `""` clear value.
- Unit tests: each field, clear, name-or-id resolution, ML confidence reset,
  approve validation.

Acceptance: edits and clears persist across reload; invalid values revert + toast.

### Phase 3 — Approve + commit

- Actions cell with approve formatter + `cellClick` optimistic toggle.
- `GET /api/inbox/commit-summary`, `POST /api/inbox/commit` (JSON), dialog
  markup, badge update, marked count.
- Extract commit/summary logic into shared helpers and keep the old HTML routes
  calling them.
- Unit tests: summary counts, new-entity warnings, commit flips status, orphan
  pruning, `remaining`; approve toggle + 422.

Acceptance: approve highlights immediately and survives reload; commit dialog →
confirm removes rows, decrements badge, toasts.

### Phase 4 — Range clipboard

- Custom `clipboardPasteAction` + `PATCH /api/inbox/transactions/batch`.
- Allowlist filtering, blockRedraw, reconcile/reload behavior.
- Unit tests: batch success, all-or-nothing rollback, allowlist.
- UI test: clipboard permissions + paste single value across a range; fall back
  to an API-level assertion if the browser path proves flaky.

Acceptance: selecting a multi-row range and pasting one value updates and
persists every row; pasting a rectangle fills by cycling; failures revert.

### Phase 5 — Modal + splits

- New modal partial and `GET /inbox-tabulator/transactions/{id}/edit-modal`.
- `inbox-tabulator-modal.js` wiring scalar fields to JSON PATCH and row refresh.
- Reuse `_splits_section.jinja2`; on close refresh the row so `split_count`
  and the splits badge update.

Acceptance: modal opens from Edit, scalar edits reflect in the table, splits
add/edit/delete still work, old modal untouched.

### Phase 6 — Retrain + styling

- `POST /api/inbox/retrain` JSON + toolbar button (disabled while running).
- `tabulator-daisy.css`: `.txn-approved` row style (specificity must beat
  `.tabulator-row-even`), range selection accents, compact action cells.
- daisyUI classes for buttons/badges; consult the daisyUI skill.

Acceptance: retrain reports updated count and refreshes suggestions; approved
rows are unmistakable; no visual regressions to `/data` tables.

### Phase 7 — Hardening

- `just lint` clean.
- Full unit + UI suite.
- Manual browser pass via `nix develop -c agent-browser`.
- Verify Nix build copies the new JS (`static/js/pages` is copied wholesale).

## Edge cases / risks

- **Remote pagination scope:** ranges and paste only span the loaded page. Accepted.
- **`cellEdited` vs `row.updateData`:** server reconciliation must use
  `row.update`, which does not re-fire `cellEdited`; no persistence loop.
- **Undefined vs empty:** `JSON.stringify({field: undefined})` drops the key, so
  clear-cells uses `""`, which the endpoint normalizes to `None`.
- **Range + editing conflicts:** `editTriggerEvent: "dblclick"` avoids
  entering edit on selection; do not use frozen columns or row selection
  (Tabulator warns about both with `selectableRange`).
- **Optimistic approve:** must revert cleanly on 422 (missing description or
  external) and keep the marked count correct.
- **Batch failure:** reload from server rather than trying to reconcile partial
  local state.
- **Column allowlist:** the range parser maps by position, so non-editable
  columns must be explicitly filtered out, not just left un-editable.

## Out of scope

- Filters/header filters, checkboxes, selection toolbar.
- Editing date, amount, internal account.
- Persisting the old inbox's stacked-value presentation.
- Any change to the existing `/inbox` page or the old modal.
