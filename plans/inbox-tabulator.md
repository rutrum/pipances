# Inbox Tabulator — Implementation Plan & Handoff

A second, Tabulator-based inbox that lives alongside the existing HTMX inbox.
It is intended to **eventually replace** the original, so it is deliberately
self-contained: no shared modal template, no shared row template, no
abstraction layer between the two inboxes. Only genuinely neutral helpers
(query functions, `set_txn_*`, categories/external resolution) are reused.

## Status

Branch: `ui-redesign`. Work is committed; nothing is pushed.

| Phase | State | Commit |
|---|---|---|
| 0 — Scaffolding | ✅ Done | `d5f8896` |
| 1 — Read-only table | ✅ Done | `d5f8896` |
| 2 — Inline editing + clear | ✅ Done | `d5f8896` |
| 3 — Approve + commit | ✅ Done | `1ad3621` |
| 4 — Range clipboard | ⬜ Not started | — |
| 5 — Modal + splits | ⬜ Not started | — |
| 6 — Retrain + styling | ⬜ Not started | — |
| 7 — Hardening | ⬜ Not started | — |

`d5f8896` = "Add Tabulator inbox page with inline editing (phases 0-2)".
`1ad3621` = "Add approve and commit flow to Tabulator inbox (phase 3)".

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
| 1 | One new navbar entry, route `/inbox-tabulator`, label "Inbox Tabulator", `active_page="inbox_tabulator"`. |
| 2 | Range paste uses a custom `clipboardPasteAction` (built-in `"range"` parser kept), plus a batch PATCH. |
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
| 14 | Deferred: the 36 pre-existing UI-test failures are out of scope for this feature. |

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

Implemented:

```
Browser (inbox-tabulator.js)
  POST  /api/inbox/table                    <- remote sort/pagination
  PATCH /api/inbox/transactions/{id}        <- inline edit / approve toggle
  GET   /api/inbox/commit-summary           <- commit dialog data
  POST  /api/inbox/commit                   <- commit marked rows
```

Planned:

```
  PATCH /api/inbox/transactions/batch       <- range paste (all-or-nothing)
  POST  /api/inbox/retrain                  <- retrain, returns updated count
  GET   /inbox-tabulator/transactions/{id}/edit-modal  <- new modal HTML
```

The existing `/inbox`, `/inbox/commit`, `/inbox/retrain`, `/transactions/*`
routes and templates are left exactly as they are.

## Files

Created:

- `src/pipances/routes/inbox_tabulator.py` — page route (modal route TODO).
- `src/pipances/templates/pages/inbox_tabulator.jinja2` — page, toolbar, commit dialog.
- `static/js/pages/inbox-tabulator.js` — table, editors, approve, commit.
- `tests/test_inbox_tabulator_api.py` — 30 unit/API tests.

Planned:

- `src/pipances/templates/inbox/_inbox_tabulator_modal.jinja2` — new modal.
- `static/js/pages/inbox-tabulator-modal.js` — modal wiring.
- `tests/ui/test_inbox_tabulator.py` — browser tests for the new page.

Modified:

- `src/pipances/routes/api/inbox.py` — new JSON endpoints.
- `src/pipances/routes/api/schemas.py` — request/response models.
- `src/pipances/routes/api/queries.py` — inbox row serializer fields.
- `src/pipances/db/transactions.py` — `marked_txn_count`, `CommitSummary`,
  `commit_summary`, `commit_marked_transactions`.
- `src/pipances/routes/inbox.py` — old HTML routes now call the shared helpers.
- `src/pipances/settings.py` — page size + options.
- `src/pipances/main.py` — router registration.
- `src/pipances/templates/shared/_navbar.jinja2` — nav entry.
- `static/css/tabulator-daisy.css` — `.txn-approved` row style.
- `tests/ui/conftest.py` — fixture fix (see gotchas).

## Data shape

`transaction_to_dict` (used by the new table endpoint) was extended with:

- `category_id`, `external_id` — emitted but not used by the editors (see gotchas).
- `can_approve` — `bool(description and external_id)`; drives the approve gate.
- `split_count` — number of splits when loaded (`fetch_page(splits=True)`).

The nested `category` / `external_account` / `internal_account` /
`ml_confidence` objects are still emitted and used by the formatters.

## Endpoint contract

### `POST /api/inbox/table` (done)

Body: `TabulatorRequest`. Response: `{last_page, last_row, data: [...]}`.
`fetch_page(statuses=(PENDING,), sorters=..., page=..., page_size=..., splits=True)`.
Filters are accepted but unused for now.

### `PATCH /api/inbox/transactions/{id}` (done)

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
  returns 422 otherwise. Validation runs after any field updates in the same
  request, so `{description, external_id, marked_for_approval: true}` works.
- Returns the same inbox row dict the table endpoint uses.

### `PATCH /api/inbox/transactions/batch` (planned, Phase 4)

Body: `{updates: [{id, description?, category_id?, external_id?}]}`.
All-or-nothing in one transaction: any invalid row rolls the whole request back
and returns 422. On success returns the updated rows. Deliberately excludes
`marked_for_approval` and any non-editable field.

### `GET /api/inbox/commit-summary` (done)

`{count, new_categories: [...], new_externals: [...]}` via
`db.transactions.commit_summary`.

### `POST /api/inbox/commit` (done)

`{committed, remaining}` via `db.transactions.commit_marked_transactions`,
which also prunes orphaned external accounts.

### `POST /api/inbox/retrain` (planned, Phase 6)

Trains on approved rows, updates pending suggestions, returns
`{updated_count}`. Logic still lives in the old `routes/inbox.py::retrain_inbox`
and should be extracted into a shared helper.

### `GET /inbox-tabulator/transactions/{id}/edit-modal` (planned, Phase 5)

Returns the new modal partial. Reuses the existing category/external/description
loading helper (data only, not markup).

## Table configuration (as built)

```
height: "70vh"
layout: "fitColumns"
index: "id"
selectableRows: false
ajaxURL: "/api/inbox/table", ajaxConfig: "POST", ajaxContentType: "json"
pagination: true, paginationMode: "remote"
paginationSize: settings.inbox_default_page_size
paginationSizeSelector: settings.inbox_page_size_options
paginationCounter: "rows"
sortMode: "remote"
initialSort: [{column: "date", dir: "asc"}]
editTriggerEvent: "dblclick"
selectableRange: 1
selectableRangeColumns: false
selectableRangeRows: false
selectableRangeClearCells: true
selectableRangeClearCellsValue: ""
```

Phase 4 adds: `clipboard: true`, `clipboardCopyRowRange: "range"`,
`clipboardPasteParser: "range"`, `clipboardPasteAction: <custom>`,
`clipboardCopyStyled: false`,
`clipboardCopyConfig: {columnHeaders: false, rowHeaders: false}`.

Columns: Date, Account, Amount, Raw Description, Description, Category,
External, Actions.

- Description/Category/External formatters show the value (or muted fallback)
  plus an ML confidence dot.
- Category formatter appends an `N splits` badge when `split_count > 0`.
- Actions formatter renders `Approve` / `Approved` / disabled `Approve`.

`rowFormatter` toggles a `txn-approved` class from `marked_for_approval`.

## Range paste (planned, Phase 4)

1. The built-in `"range"` parser produces row objects keyed by the visible
   fields under the selected range.
2. The custom action replicates the range/row targeting logic (active rows,
   start/end bounds, modulo cycling), then:
   - filters to the allowlist `description`, `category_id`, `external_id`
     (ignores date/amount/raw/internal/`_actions` even if the range covers them);
   - applies `row.updateData(...)` inside `blockRedraw`/`restoreRedraw`;
   - collects `{id, field: value}` updates;
   - sends one `PATCH /api/inbox/transactions/batch`;
   - on success reconciles rows from the response;
   - on any failure reloads the table (`setData()`) and shows an error toast.
3. Values copied from the table are display strings (e.g. category name); the
   endpoint resolves id-or-name, so round-trips work unchanged.

Inline edits and clear-cells need no special casing: they fire `cellEdited`,
which reuses `PipancesEditors.saveCell` against the single-row endpoint.

Note: the parser maps by column position, so the allowlist must be enforced in
the action even though `_actions` has `clipboard: false`.

## Modal (planned, Phase 5)

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
- Add an `Edit` button to the actions formatter that loads the modal into
  `#edit-modal-container` (already present in the page template).

## Approved + commit UX (as built)

- Clicking Approve optimistically flips `marked_for_approval` locally,
  re-runs `row.reformat()` for the immediate highlight, updates the marked
  count, then PATCHes; on failure it reverts and toasts.
- `Commit` sits in the top toolbar and shows the marked count (server-rendered
  initial value via `data-marked-count`, adjusted on toggles, reset to 0 after
  commit).
- Clicking Commit fetches the JSON summary and populates the inline
  `<dialog id="commit-dialog">`; Confirm POSTs `/api/inbox/commit`, then closes,
  toasts, updates `#inbox-badge`, and `table.setData()`.

## Settings additions

```python
inbox_default_page_size: int = 25
inbox_page_size_options: list[int] = [25, 50, 100]
```

Passed to the template and onto `#inbox-tabulator-root` as data attributes.

## As-built notes, deviations and gotchas

These are the important things to know before touching the code again.

1. **Actions cell does not auto-refresh.** `row.update(data)` only re-renders
   cells whose column `field` changed. `marked_for_approval`, `can_approve`,
   and `split_count` are not column fields, so the Actions/other formatters
   go stale. **Always call `row.reformat()` after a `row.update` that should
   change a formatter.** This was a real bug for the Approve gate after an
   inline edit; `refreshRow(row, data)` and the `saveCell(...).then(...)`
   wrapper already do this.

2. **Editors bind to names, not ids.** Category/External columns are
   `field: "category.name"` / `"external_account.name"`, and the Tom Select
   options use `{value: name, text: name}`. This keeps nested `row.update`
   working and lets the server resolve id-or-name. The serializer still emits
   `category_id` / `external_id` but nothing reads them yet.

3. **Clear-cells touches read-only cells.** The range module clears every cell
   in the range. Non-editable columns are protected by a guarded restore
   (`restoreReadonlyCell`) that sets the value back to `getOldValue()`; the
   `restoringReadonly` flag prevents an oscillation loop. Keep this in place.

4. **`row.updateData` does not fire `cellEdited`.** Do not try to persist range
   paste via `cellEdited`; use the custom paste action.

5. **`JSON.stringify` drops `undefined`.** Clear-cells uses `""` and the
   endpoint normalizes `""` to `None`. Do not switch the clear value to
   `undefined`/`null` without updating `saveCell`.

6. **`table-editors.js` is shared with `/data/*`.** Prefer not to change its
   contract; the inbox relies on `saveCell`, `tomSelect`, `showToast`.

7. **Tabulator range constraints.** Do not add `frozen` columns, row selection,
   or `selectableRangeColumns/Rows` without re-reading Tabulator's warnings;
   the range module conflicts with them. `selectableRows: false` is required.

8. **`selectableRange` was enabled in Phase 2**, not Phase 4, because
   `selectableRangeClearCells` needs it. Phase 4 only adds clipboard config.

9. **Testing Tom Select with agent-browser.** Clicking the dropdown option via
   a ref/synthetic event is flaky. `document.querySelector('.tabulator-cell.tabulator-editing select').tomselect.setValue('Netflix')`
   triggers the same `change` path and works reliably. Real Playwright clicks
   have worked for categories.

## Phases

### Phase 0 — Scaffolding ✅

Done. Route, navbar entry, settings, empty page.

### Phase 1 — Read-only table ✅

Done. `POST /api/inbox/table`, serializer fields, columns/formatters,
`rowFormatter`.

### Phase 2 — Inline editing + clear ✅

Done. Single-row PATCH, `input` / `tomSelect` editors, `cellEdited` →
`saveCell` → `row.reformat()`, clear-cells with read-only restore.

### Phase 3 — Approve + commit ✅

Done. Actions cell + optimistic toggle, JSON summary/commit, shared commit
helpers, commit dialog, badge + marked count.

### Phase 4 — Range clipboard ⬜

- Add `PATCH /api/inbox/transactions/batch` (all-or-nothing).
- Add `clipboard` config and a custom `clipboardPasteAction`. Keep
  `clipboardPasteParser: "range"`.
- Allowlist filtering, `blockRedraw`, reconcile/reload behavior.
- Unit tests: batch success, rollback, allowlist, empty clears.
- UI test: clipboard permissions + paste single value across a range; fall back
  to an API-level assertion if the browser path is flaky.

Acceptance: selecting a multi-row range and pasting one value updates and
persists every row; pasting a rectangle fills by cycling; failures revert.

### Phase 5 — Modal + splits ⬜

- New modal partial and `GET /inbox-tabulator/transactions/{id}/edit-modal`.
- `inbox-tabulator-modal.js` wiring scalar fields to JSON PATCH and row refresh.
- Reuse `_splits_section.jinja2`; on close refresh the row so `split_count`
  and the splits badge update.
- Add the `Edit` button to the actions formatter.

Acceptance: modal opens from Edit, scalar edits reflect in the table, splits
add/edit/delete still work, old modal untouched.

### Phase 6 — Retrain + styling ⬜

- Extract retrain logic into a shared helper; add `POST /api/inbox/retrain`
  JSON + toolbar button (disabled while running).
- `tabulator-daisy.css`: range selection accents, compact action cells; refine
  `.txn-approved` if needed.
- daisyUI classes for buttons/badges; consult the daisyUI skill.

Acceptance: retrain reports updated count and refreshes suggestions; approved
rows are unmistakable; no visual regressions to `/data` tables.

### Phase 7 — Hardening ⬜

- `just lint` clean.
- Full unit suite; triage UI suite (see below).
- Manual browser pass via `nix develop -c agent-browser`.
- Verify Nix build copies the new JS (`static/js/pages` is copied wholesale).
- Optionally fix the pre-existing UI-test failures (deferred decision).

## Handoff notes for the next agent

### Where things stand

The page is fully usable for the core loop: view → inline edit → approve →
commit. It is unauthenticated single-user, same as the rest of the app.
Nothing is pushed; `ui-redesign` is 11 commits ahead of `origin/ui-redesign`.

### Commands

```bash
just lint          # prek, all files (run this, not individual linters)
just test          # unit/API tests, ignores tests/ui
nix develop -c just test-ui   # browser tests (needs chromium from the devshell)
just serve-hot     # dev server on :8098 using .env + ./pipances.db
```

Manual testing against a throwaway seed (do not mutate the dev DB):

```bash
rm -f /tmp/pipances.db
PIPANCES_DB_PATH=/tmp/pipances.db PIPANCES_STATIC_DIR=./static \
  PIPANCES_IMPORTERS_DIR=./importers PIPANCES_TEMP_DIR=/tmp/pipances_imports \
  uv run python scripts/seed.py
PIPANCES_DB_PATH=/tmp/pipances.db PIPANCES_STATIC_DIR=./static \
  PIPANCES_IMPORTERS_DIR=./importers PIPANCES_TEMP_DIR=/tmp/pipances_imports \
  uv run uvicorn pipances.main:app --port 8097
nix develop -c agent-browser open http://localhost:8097/inbox-tabulator
```

### Test status to be aware of

- `just test`: 195 passing.
- `just test-ui`: 44 passing, 36 failing. **All 36 failures are pre-existing on
  this branch** and unrelated to the inbox Tabulator work (verified by running
  representative failures at the base commit). They are:
  - `test_table_sorting` (11): stale locators from the `/data` migration.
  - `test_combobox_popover` / `test_inbox_modal_edit` /
    `test_inbox_transaction_modal_edit` / `test_transaction_splits` (22): the
    old modal's Tom Select input is "outside of the viewport" at the test
    viewport size.
  - `test_oob_regressions` (1) and 2 `test_commit_flow` pagination tests:
    locators expect a `<span>` but `_pagination.jinja2` renders a `<button>`.
- Phase 3 did fix one real cluster: `tests/ui/conftest.py` fixtures
  `approvable_txn`, `approvable_txn_with_new_category`, and `bulk_pending_txns`
  previously set only `description`, but both inboxes require description +
  external to enable Approve, so `do_approve` always timed out. They now attach
  an external that is already referenced by an approved transaction.
  `test_commit_flow.py` went from 1/13 to 11/13 passing.
- There is no `tests/ui/test_inbox_tabulator.py` yet; Phase 4–6 should add one
  once the surface is stable.

### Highest-value next work

Phase 4 (range clipboard) is the differentiating feature and the reason the
custom paste action exists. Phase 5 (modal) is the other chunk needed before
this can replace `/inbox`. Phase 6 is polish plus retrain.

## Edge cases / risks

- **Remote pagination scope:** ranges and paste only span the loaded page. Accepted.
- **`cellEdited` vs `row.updateData`:** server reconciliation must use
  `row.update` (+ `row.reformat()`), which does not re-fire `cellEdited`; no
  persistence loop.
- **Undefined vs empty:** `JSON.stringify({field: undefined})` drops the key, so
  clear-cells uses `""`, which the endpoint normalizes to `None`.
- **Range + editing conflicts:** `editTriggerEvent: "dblclick"` avoids
  entering edit on selection; do not use frozen columns or row selection.
- **Optimistic approve:** must revert cleanly on 422 (missing description or
  external) and keep the marked count correct.
- **Batch failure:** reload from server rather than trying to reconcile partial
  local state.
- **Column allowlist:** the range parser maps by position, so non-editable
  columns must be explicitly filtered out, not just left un-editable.
- **Marked count is best-effort across pages:** it is server-rendered on load
  and adjusted locally for toggles on the loaded page. The commit dialog's
  summary remains authoritative.

## Out of scope

- Filters/header filters, checkboxes, selection toolbar.
- Editing date, amount, internal account.
- Persisting the old inbox's stacked-value presentation.
- Any change to the existing `/inbox` page or the old modal.
- Fixing the 36 pre-existing UI-test failures (deferred decision).
