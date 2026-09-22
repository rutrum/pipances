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
| 4 — Range clipboard | ✅ Done | `84d6205` |
| 5 — Modal + splits | ✅ Done | `9db0fe4` |
| 6 — Retrain + styling | ✅ Done | `a357f5a` |
| 7 — Hardening | ✅ Done | `cd580dd` |

`d5f8896` = "Add Tabulator inbox page with inline editing (phases 0-2)".
`1ad3621` = "Add approve and commit flow to Tabulator inbox (phase 3)".
`84d6205` = "Add range clipboard paste to Tabulator inbox (phase 4)".
`9db0fe4` = "Add edit modal and splits to Tabulator inbox (phase 5)".
`a357f5a` = "Add retrain and inbox styling to Tabulator inbox (phase 6)".
`cd580dd` = "Prune redundant UI tests and repair the suite (phase 7)".
`df4ce23` = "Bump flake inputs (blueprint, nixpkgs, uv2nix)" (unrelated chore).
Nothing is pushed; the branch is 23 commits ahead of `origin/ui-redesign`.
Phase 7 is committed as `cd580dd`.

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
  PATCH /api/inbox/transactions/batch       <- range paste (all-or-nothing)
  GET   /inbox-tabulator/transactions/{id}/edit-modal  <- new modal HTML
  GET   /api/inbox/commit-summary           <- commit dialog data
  POST  /api/inbox/commit                   <- commit marked rows
  POST  /api/inbox/retrain                  <- retrain, returns updated count
```

The existing `/inbox`, `/inbox/commit`, `/inbox/retrain`, `/transactions/*`
routes and templates are left exactly as they are.

## Files

Created:

- `src/pipances/retrain.py` — shared `retrain_pending_suggestions` helper.
- `src/pipances/routes/inbox_tabulator.py` — page route + modal route.
- `src/pipances/templates/pages/inbox_tabulator.jinja2` — page, toolbar, commit dialog.
- `src/pipances/templates/inbox/_inbox_tabulator_modal.jinja2` — new modal.
- `static/js/pages/inbox-tabulator.js` — table, editors, approve, commit, range paste.
- `static/js/pages/inbox-tabulator-modal.js` — modal wiring.
- `tests/test_inbox_tabulator_api.py` — 42 unit/API tests.
- `tests/ui/test_inbox_tabulator.py` — 5 browser tests (paste + modal +
  dropdown stacking + dropdown clipping).

Modified:

- `src/pipances/routes/api/inbox.py` — new JSON endpoints.
- `src/pipances/routes/api/schemas.py` — request/response models.
- `src/pipances/routes/api/queries.py` — inbox row serializer fields.
- `src/pipances/db/transactions.py` — `marked_txn_count`, `CommitSummary`,
  `commit_summary`, `commit_marked_transactions`, `distinct_descriptions`.
- `src/pipances/routes/inbox.py` — old HTML routes now call the shared helpers.
- `src/pipances/routes/transactions.py` — old modal route uses
  `distinct_descriptions` (data-only refactor).
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

### `PATCH /api/inbox/transactions/batch` (done, Phase 4)

Body: `{updates: [{id, description?, category_id?, external_id?}]}`.
All-or-nothing: every update is applied to one session and a single
`commit()` runs at the end, so an unknown `id` raises 422 and the whole batch
(including categories/externals already flushed by `get_or_create_*`) rolls
back. Only the three editable fields are accepted; Pydantic ignores extras such
as `marked_for_approval` or `date`. Duplicate ids collapse to the last update.
Returns `{data: [row, ...]}` in first-seen order.

**Route ordering matters:** `PATCH /inbox/transactions/batch` must be declared
*before* `PATCH /inbox/transactions/{txn_id}`. FastAPI/Starlette matches the
`{txn_id}` route for the literal `batch` string and then fails int validation
with 422, so the batch route would be unreachable if declared after.

### `GET /api/inbox/commit-summary` (done)

`{count, new_categories: [...], new_externals: [...]}` via
`db.transactions.commit_summary`.

### `POST /api/inbox/commit` (done)

`{committed, remaining}` via `db.transactions.commit_marked_transactions`,
which also prunes orphaned external accounts.

### `POST /api/inbox/retrain` (done, Phase 6)

Trains on approved rows, updates pending suggestions, returns
`{updated_count}` (individual field suggestions refreshed; a transaction can
contribute up to three). Zero when there is nothing to train on or change. The
HTMX route and this endpoint both call
`pipances.retrain.retrain_pending_suggestions`, which returns a
`RetrainResult(updated_count, pending_count, approved_count)` and commits the
session itself.

### `GET /inbox-tabulator/transactions/{id}/edit-modal` (done, Phase 5)

Returns the new modal partial. Loads the row (`splits=True`), all external
accounts, all categories (as ORM objects and as `[{id, name}]` for the splits
section) and the distinct descriptions via the new shared
`db.transactions.distinct_descriptions` helper (the old
`/transactions/{id}/edit-modal` route now uses the same helper). 404 for an
unknown id.

## Modal (done, Phase 5)

The modal is fully independent of the old HTMX modal:

- `inbox/_inbox_tabulator_modal.jinja2` renders a `<dialog>` with the read-only
  context (date, amount, account, raw description), three scalar comboboxes,
  the reused `{% include "shared/_splits_section.jinja2" %}`, and a single
  Approve/Unapprove button (`data-modal-approve`).
- The scalar selects carry `class="ts-json-select"` (deliberately **not**
  `ts-select`) and are initialized by `inbox-tabulator-modal.js`. Each change
  PATCHes `/api/inbox/transactions/{id}` and refreshes the Tabulator row.
- `inbox-tabulator.js` adds the `Edit` button to the actions formatter (hidden
  for marked rows) and opens the modal through
  `window.PipancesInboxModal.open(id)`.
- On close the modal refetches `GET /api/transactions/{id}` and updates the row
  so `split_count` and the split badge stay in sync, then destroys the Tom
  Select instances and empties `#edit-modal-container`.
- The Approve button label/state is updated in place after scalar edits based
  on the returned `can_approve` / `marked_for_approval`.
- Every Tom Select dropdown inside the modal is portaled into the `<dialog>`
  and positioned `fixed` so `.modal-box`'s `overflow-y: auto` cannot clip it
  (see gotcha 16). This covers both the scalar `ts-json-select` comboboxes and
  the splits `ts-select` comboboxes, including after splits HTMX swaps.

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

Phase 4 added: `clipboard: true`, `clipboardCopyRowRange: "range"`,
`clipboardPasteParser: "range"`, `clipboardPasteAction: rangePasteAction`,
`clipboardCopyStyled: false`,
`clipboardCopyConfig: {columnHeaders: false, rowHeaders: false}`.

Columns: Date, Account, Amount, Raw Description, Description, Category,
External, Actions.

- Description/Category/External formatters show the value (or muted fallback)
  plus an ML confidence dot.
- Category formatter appends an `N splits` badge when `split_count > 0`.
- Actions formatter renders `Approve` / `Approved` / disabled `Approve`.

`rowFormatter` toggles a `txn-approved` class from `marked_for_approval`.

## Range paste (done, Phase 4)

1. The built-in `"range"` parser produces row objects keyed by the visible
   fields under the selected range.
2. `rangePasteAction` (in `inbox-tabulator.js`) replicates the range/row
   targeting logic (active rows, start/end bounds, modulo cycling), then:
   - filters to the allowlist `description`, `category.name`,
     `external_account.name` (ignores date/amount/raw/internal/`_actions` even
     if the range covers them);
   - converts each flat field path into a **nested** object before calling
     `row.updateData(...)` (see gotcha 10), inside `blockRedraw`/`restoreRedraw`;
   - collects `{id, field: value}` updates mapped to the body field names
     (`category.name` -> `category_id`, etc.);
   - sends one `PATCH /api/inbox/transactions/batch`;
   - on success reconciles rows from the response with `refreshRow`;
   - on any failure reloads the table (`setData()`) and shows an error toast.
   - if the pasted range contains no editable columns, it toasts a warning and
     does nothing (no request).
3. Values copied from the table are display strings (e.g. category name); the
   endpoint resolves id-or-name, so round-trips work unchanged.

Inline edits and clear-cells need no special casing: they fire `cellEdited`,
which reuses `PipancesEditors.saveCell` against the single-row endpoint.

Note: the parser maps by column position, so the allowlist must be enforced in
the action even though `_actions` has `clipboard: false`.

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

10. **Nested fields need a nested update object.** Tabulator's `row.updateData`
    diffs through `column.getFieldValue()` (which reads dot paths from the row
    object). Passing the flat key `"category.name"` updates a junk flat
    property, not the nested category. `rangePasteAction` therefore builds a
    nested object (`{category: {name: ...}}`) before applying locally; the
    server response then restores the full `{id, name}` object via
    `refreshRow`. The batch request body still uses the flat mapping in
    `EDITABLE_FIELDS`.

11. **`table.addRange` is asynchronous.** The range constructor sets its bounds
    in a `setTimeout`. Anything testing range paste programmatically (including
    the UI test's synthetic fallback) must wait a tick after `addRange` before
    dispatching the paste event, or the parser sees the default one-cell range
    at the top-left cell.

12. **Fetch-injected HTML is not processed by HTMX or Alpine.** The modal is
    loaded with `fetch` (not `hx-get`), so `inbox-tabulator-modal.js` must call
    `htmx.process(container)` and `Alpine.initTree(container)` after injecting,
    and `initTomSelects(container)` for the reused splits section. HTMX then
    handles the splits section's own `hx-*` requests via its normal
    `htmx:afterSwap` handler.

13. **Modal scalar selects are `ts-json-select`, not `ts-select`.** The global
    `initTomSelects` bootstrap in `base.jinja2` fires HTMX PATCHes expecting an
    HTML swap; the modal needs JSON PATCH + row refresh instead, so it has its
    own initializer. Do not rename the class back.

14. **Tom Select dropdowns must stay inside the `<dialog>`.** A native modal
    `<dialog>` (shown with `showModal()`) lives in the browser's top layer,
    which paints above *all* normal DOM regardless of `z-index`. Setting
    `dropdownParent: "body"` therefore renders the dropdown behind the modal
    and makes it unclickable. Leave `dropdownParent` unset so the dropdown is a
    child of the `.ts-wrapper` (inside the dialog); if it is ever moved, the
    dropdown must be appended inside the dialog. UI regression guard:
    `test_modal_combobox_dropdown_renders_above_dialog` asserts the option is
    the topmost element via `document.elementFromPoint`.

15. **The modal's Approve button is stateful.** It is rendered once (possibly
    disabled) and is turned on/off in place after each scalar edit from the
    `can_approve` / `marked_for_approval` fields of the PATCH response. Tom
    Select instances are still destroyed before the container is emptied on
    close as good hygiene.

16. **Tom Select dropdowns are clipped by `.modal-box`.** `.modal-box` is an
    `overflow-y: auto` scroll container, and TomSelect positions its dropdown
    with `position: absolute` inside the wrapper. For the lower fields (and on
    short viewports) the option list is cut off and unreachable. Fix (in
    `inbox-tabulator-modal.js`): `portalDropdown()` moves the dropdown into the
    top-layer `<dialog>`, switches it to `position: fixed`, sizes it from the
    control's `getBoundingClientRect()`, flips it above the control when it
    would overflow the viewport, and repositions it via `dropdown_open`,
    `type`, modal-box scroll, window resize and a `ResizeObserver` (the option
    list is laid out asynchronously, so the first measurement is too small).
    `portalTomSelects()` re-portals after the splits section's HTMX swaps via
    an `htmx:afterSwap` listener. UI regression guard:
    `test_modal_combobox_dropdown_escapes_scroll_container`.

17. **Retrain commits the caller's session.** `retrain_pending_suggestions`
    applies the predictions and calls `await session.commit()` itself (matching
    `commit_marked_transactions`), so the session is left clean on return. The
    legacy route re-queries the pending rows afterwards rather than rendering
    the objects it mutated, because `expire_on_commit=True` would otherwise
    force async lazy loads during template rendering.

18. **`updated_count` counts fields, not rows.** Each pending transaction can
    add up to three (description, category, external). This matches the legacy
    toast wording ("updated N suggestions") and the API contract; do not change
    it to a row count without updating both callers and the tests.

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

### Phase 4 — Range clipboard ✅

Done. Batch endpoint (all-or-nothing, route declared before `{txn_id}`), custom
`rangePasteAction`, allowlist filtering, nested local apply, reconcile/reload.
Unit tests in `test_inbox_tabulator_api.py` (batch success, creation, clear,
rollback, allowlist, dedupe, empty) and a browser test
`tests/ui/test_inbox_tabulator.py` (real clipboard with a synthetic fallback).

Note: built-in `clipboardCopyRowRange` is `"range"`, `clipboardCopyStyled` is
false, and copy config suppresses headers/row headers.

### Phase 5 — Modal + splits ✅

Done. New `inbox/_inbox_tabulator_modal.jinja2` + modal route, JSON-PATCH scalar
comboboxes (`ts-json-select`), reused splits section, live Approve-button state,
`Edit` button in the actions formatter, and row refetch on close so
`split_count` and category refresh. `distinct_descriptions` extracted into
`db/transactions.py` and shared with the old modal route.

Unit tests: modal render, current scalar values selected, 404, script include,
old modal route. Browser tests: scalar edit persists, adding a split refreshes
the badge.

Acceptance met: modal opens from Edit, scalar edits reflect in the table, splits
add/edit/delete work (verified manually + browser test), old modal untouched.

### Phase 6 — Retrain + styling ✅

Done. `pipances/retrain.py` holds the shared `retrain_pending_suggestions`
helper; `routes/inbox.py::retrain_inbox` delegates to it and re-queries the
pending rows for rendering. `POST /api/inbox/retrain` returns
`{updated_count}`. The toolbar `#retrain-btn` is disabled with a
`loading loading-spinner` while running, toasts the count, and calls
`table.replaceData()` so the clipboard/sort/page state survives the refresh.
`tabulator-daisy.css` now maps range-selection chrome (`tabulator-range*`)
onto `primary`, deepens `.txn-approved` (22% success + 4px left bar), and adds
`.txn-actions-cell` for compact action cells. No `/data` selectors were
touched, and the `/data/accounts` page was screenshot-checked.

Unit tests: no pending, no training data, a deterministic prediction run that
asserts `updated_count == 3` plus refreshed row fields, and a guard that the
legacy HTML route still reports the shared count. Browser test:
`test_retrain_reports_count_and_refreshes_table` stubs the endpoint and asserts
the count toast plus a follow-up `POST /api/inbox/table`.

Acceptance met: retrain reports an updated count and refreshes suggestions;
approved rows are unmistakable; no visual regressions to `/data` tables.

### Phase 7 — Hardening ✅

**Goal:** ship-quality confidence with no behavioral change to the Tabulator
inbox: green lint/unit/build, a *triaged* UI suite, and a recorded manual pass.

#### 7.1 Verification (baseline already captured)

Branch `ui-redesign` @ `3a1dc58`. Working tree dirty only for `flake.lock`
(blueprint bump, unrelated to this feature — decide whether to keep it separate).

| Check | Command | Result |
|---|---|---|
| Lint/format | `just lint` | ✅ all 14 prek hooks pass |
| Unit/API | `just test` | ✅ 212 passed in 6.03s |
| Nix package | `nix build .#pipances` | ✅ builds; `pipances-static` store contains `inbox-tabulator.js`, `inbox-tabulator-modal.js`, `tabulator-daisy.css` |
| Feature UI tests | `nix develop -c uv run pytest tests/ui/test_inbox_tabulator.py` | ✅ 6 passed (not in the failure list of the full run) |
| Full UI suite | `nix develop -c just test-ui` | ⚠️ 36 failed / 50 passed / 735s |

The Nix task from the old bullet list is therefore **done**: `nix/packages/pipances.nix:71`
copies `static/js/pages/.` wholesale and the built store path confirms both new
scripts are present. 7.1 only needs to be re-run and recorded at the end.

#### 7.2 UI suite — prune first, then fix

The 36 failures are **not** inbox-Tabulator regressions (the six
`test_inbox_tabulator.py` tests pass). They live in tests written for the
hand-rolled tables and the third-party wrappers. Guiding rule: **do not test
behaviour that Tabulator or Tom Select provides out of the box — keep only tests
that exercise our own wiring/config.** That means deleting redundant tests
rather than repairing their stale locators.

**Delete outright (redundant or stale):**

| File / test | Tests | Why |
|---|---|---|
| `tests/ui/test_combobox_popover.py` | 5 | Pure Tom Select behaviour (type→dropdown, arrow keys, enter/click select, create-new). Third-party library, not our code. |
| `tests/ui/test_inbox_modal_edit.py` | 14 | Stale: helper `fill_combo()` targets `.combo-box`, removed when Tom Select landed; module docstring lists BUG-A/BUG-B that are fixed. Superseded by `test_inbox_transaction_modal_edit.py` (current `.ts-wrapper` selectors) and `test_inbox_tabulator.py`. |
| `test_oob_regressions.py::test_inbox_thead_oob_swap_updates_sort_arrow` | 1 | Guards the hand-rolled `#inbox-thead` OOB swap that Tabulator makes unnecessary. |
| `test_table_sorting.py` (12 of 15) | 12 | All 5 `test_explore_*`, all 5 `test_inbox_*` sort tests, `test_data_transactions_sort_toggles_direction`, `test_html_pages_have_working_sort`. They assert Tabulator/macro arrow text and hand-rolled toggling — out-of-box or retired. |

**Keep and repair — `test_table_sorting.py` becomes `test_transactions_table.py`
with 3 Tabulator wiring tests:**

- `test_data_transactions_table_renders` — smoke: grid mounts with the expected
  columns. Fix `#transactions-table .tabulator` → `#transactions-table.tabulator`
  (Tabulator puts the class **on** the container, so the descendant selector
  matches nothing — confirmed `element(s) not found`).
- `test_data_transactions_default_sort_is_date_descending` — our `initialSort`
  config matches the API default. Already green.
- `test_data_transactions_date_preset_reloads_table` — our date-preset wiring
  (`btn-active`, grid stays mounted). Fix the same `.tabulator` selector.

Sort/arrow *toggling* and persistence-across-pagination are Tabulator
guarantees; the server side is covered by `tests/test_tabulator_table.py`. No UI
test needed for either.

**Keep and repair (our logic, green apart from locators/viewport):**

- `test_commit_flow.py::test_confirm_pagination_*` (2) — pagination reset/total
  after a commit is our logic. `_pagination.jinja2` renders `<button>`, so fix
  `#inbox-pagination span:has-text('Page …')` → `#inbox-pagination
  button:has-text('Page …')`.
- `test_inbox_transaction_modal_edit.py` (3 of 14 failing) — old-modal wiring on
  current selectors.
- `test_transaction_splits.py` (3) — shared splits section.

Both viewport failures share one cause; see 7.3.

#### 7.3 Old-modal viewport root cause (6 failures after 7.2)

The click targets the *nth* `.ts-wrapper` input, but `test_combobox_popover.py`'s
`get_ts_input()` scrolls only the **first** `.ts-wrapper` into view, so
Playwright reports `element is outside of the viewport` for the Category field.
`test_inbox_modal_edit.py` additionally targets a removed `.combo-box` selector.
Confirm before fixing:
1. Reproduce one remaining failure at `origin/ui-redesign` (pre-feature base) to
   prove it is pre-existing, not caused by phases 3–6.
2. Fix the shared helper to scroll the *target* wrapper into view (or set a
   taller viewport). If it still fails, inspect the old `.modal-box` scroll
   container for a real layout regression and record the exact cause.

#### 7.4 Decision needed

Confirm the prune list in 7.2. After it, the suite loses **32 tests** (5 + 14 +
1 + 12, of which 28 were failing) and the remaining **8 failures** are repaired
(2 `test_commit_flow`, 3 `test_inbox_transaction_modal_edit`, 3
`test_transaction_splits`). If you would rather keep any of the deleted files
(e.g. the old-modal field-persistence tests until `/inbox` is retired), say so
and I will repair instead of delete.

#### 7.5 Manual browser pass

Throwaway DB + uvicorn on :8097 (commands in the Handoff notes), driven with
`nix develop -c agent-browser`, screenshots to `/tmp/agent-browser`:
load page → remote sort → pagination → inline description/category/external
edit → clear-cells → range copy/paste → approve one row + highlight → commit
(dialog + badge + count) → retrain (spinner + count toast) → open modal → scalar
edit → add/edit/delete a split → close modal (badge refreshes) → confirm no
console errors. Then spot-check `/data/transactions`, `/data/accounts`,
`/data/categories` for CSS regressions from `tabulator-daisy.css`.

#### 7.6 Wrap-up

- Re-run `just lint`, `just test`, the feature UI tests, and `nix build`.
- Mark Phase 7 ✅ in the status table, replace “Highest-value next work” with a
  post-hardening note, and record the final UI-suite numbers + cluster outcome.
- Commit the phase (user pushes; nothing is committed by the agent unless
  asked). Keep the `flake.lock` bump in its own commit or drop it.

#### 7.7 Acceptance criteria

- `just lint` and `just test` green; `nix build .#pipances` succeeds with both
  new scripts in the static store.
- `tests/ui/test_inbox_tabulator.py` green; every remaining `tests/ui` failure
  is either fixed or listed with a confirmed non-feature cause.
- Manual pass completes with no console errors and no `/data` visual
  regressions.
- Plan doc reflects reality (counts, commit hashes, final decision).

#### 7.8 Outcome (executed)

**Suite pruning (7.2–7.4) — done.** 32 tests deleted, the remaining failures
repaired:

- Deleted `tests/ui/test_combobox_popover.py` (5) and
  `tests/ui/test_inbox_modal_edit.py` (14 — stale `.combo-box` selectors plus a
  docstring of already-fixed bugs), `test_oob_regressions.py`'s thead-OOB test
  (1), and 12 of the 15 tests in `test_table_sorting.py`.
- `test_table_sorting.py` → `tests/ui/test_transactions_table.py` with 3
  Tabulator wiring tests.
- `tests/ui/helpers.py`: `inbox_page_label` `span` → `button` (same fix in the
  two `test_commit_flow.py` pagination tests).
- `test_inbox_transaction_modal_edit.py`: dropped the wrong-premise
  `test_edit_description_and_blur_persists` (Tom Select does not keep typed text
  on blur without selecting) and the copy-pasted garbage in `test_clear_category`;
  replaced the broken x-button test with a real close assertion.
- `test_transaction_splits.py`: the delete control is `button[hx-delete]`
  (renders `✕`, not `x`); split category is driven through
  `tomselect.setValue()` because the native `<select>` is hidden; wait for
  Alpine after each HTMX swap.
- Removed the now-unused `full_txn` and `txn_with_existing_split` fixtures from
  `tests/ui/conftest.py` and fixed its stale `reset_db` docstring.

The "old-modal viewport" cluster from 7.2 was a misdiagnosis: after deleting the
two stale files only 6 failures remained, and they had other causes (wrong test
premise, copy-paste garbage, stale Tom Select selectors, Alpine timing). **No
application code changed in this phase** — only tests and docs.

**Final gates:**

- `just lint` — ✅ clean (14 hooks).
- `just test` — ✅ 212 passed.
- `nix develop -c just test-ui` — ✅ **53 passed, 0 failed** in 57.5s.
- `nix build .#pipances` — ✅ builds; `inbox-tabulator.js`,
  `inbox-tabulator-modal.js`, and `tabulator-daisy.css` all present in the
  `pipances-static` store.

**Manual pass** (`nix develop -c agent-browser`, throwaway seed on :8097; no
console errors): load → inline description edit (persisted across reload) →
modal scalar edits (external + category persisted to the row) → Approve (green
`txn-approved` highlight, Commit count 1) → Commit dialog → confirm (badge
20→19, toast, table reload) → Retrain (toast "updated 54 suggestions", ML dots)
→ modal split add (row badge "1 split" after close) → `/data/transactions` +
`/data/accounts` spot-check. Range paste is covered by
`tests/ui/test_inbox_tabulator.py`.

Minor observation left as-is: at a 1280px viewport the inbox's Actions column
sits at the right edge and needs the table's horizontal scroll. Functional and
consistent with `layout: "fitColumns"`; not a blocker for replacing `/inbox`.

## Handoff notes for the next agent

### Where things stand

The page is fully usable for the core loop: view → inline edit → range paste →
modal edit → splits → approve → commit → retrain. It is unauthenticated
single-user, same as the rest of the app. Phases 0–7 are committed
(`d5f8896` … `cd580dd`); nothing is pushed.

### Recent modal fixes

The edit modal's Tom Select comboboxes had two separate bugs that needed two
separate fixes:

1. `dropdownParent: "body"` put the dropdown outside the `<dialog>` top layer,
   so it rendered behind the modal and was unclickable (fixed, gotcha 14).
2. `.modal-box { overflow-y: auto }` clipped the absolutely-positioned
   dropdown for lower fields / short viewports, so typed results never showed
   (fixed by portaling to the dialog with `position: fixed`, gotcha 16).

Both are guarded by `tests/ui/test_inbox_tabulator.py`
(`..._renders_above_dialog` and `..._escapes_scroll_container`).

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

- `just test`: 212 passing (unchanged by phase 7).
- `tests/ui/` after phase 7's prune: **53 passing, 0 failing** in ~58s (was 50
  passing / 36 failing). 32 redundant tests were removed; see Phase 7.8.
- UI tests now cover only our own wiring: 3 Tabulator table tests
  (`test_transactions_table.py`), the 6 inbox-Tabulator tests, commit flow, row
  approve, old-modal wiring (`test_inbox_transaction_modal_edit.py`), and the
  splits stories. Out-of-the-box Tabulator/Tom Select behaviour is deliberately
  not tested.
- `tests/ui/test_inbox_tabulator.py` covers range paste, the modal dropdowns
  and retrain. Run it with
  `nix develop -c uv run pytest tests/ui/test_inbox_tabulator.py -v`
  (the session fixture seeds a throwaway DB and starts uvicorn on :8099).
- Phase 3 fixed the `conftest.py` fixtures (`approvable_txn`,
  `approvable_txn_with_new_category`, `bulk_pending_txns`) to attach an external
  account; phase 7 removed the now-unused `full_txn` and
  `txn_with_existing_split`.

### Highest-value next work

The feature is complete and hardened. What remains is a product decision, not a
code task:

1. Decide when `/inbox-tabulator` replaces `/inbox`; at that point the old
   modal, its routes, `test_inbox_transaction_modal_edit.py`,
   `test_inbox_row_approve.py`, and the old inbox templates can be deleted and
   the navbar entry renamed.
2. Only after that, revisit the deferred items in "Out of scope".

Do not re-add `clipboardPasteAction` plumbing, a second modal bootstrap, or a
second retrain code path — phases 4-6 are complete. Any follow-up styling keeps
daisyUI tokens inside `tabulator-daisy.css` and leaves `/data` selectors alone.

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
- **Modal split badge refresh:** the table row's `split_count` only refreshes
  when the modal closes (it refetches `GET /api/transactions/{id}`). The splits
  section itself updates immediately inside the modal.
- **Modal lifecycle:** `#edit-modal-container` is emptied on close and its Tom
  Select instances are destroyed first, because their dropdowns are portaled
  into the dialog (and, originally, to avoid orphaned body dropdowns).
- **Modal dropdown positioning:** never set `dropdownParent: "body"` for a
  combobox inside the native modal `<dialog>` (top-layer occlusion), and never
  leave the dropdown inside `.modal-box` (overflow clipping). Use
  `portalDropdown()` in `inbox-tabulator-modal.js`.

## Out of scope

- Filters/header filters, checkboxes, selection toolbar.
- Editing date, amount, internal account.
- Persisting the old inbox's stacked-value presentation.
- Any change to the existing `/inbox` page or the old modal (until it is
  retired; see "Highest-value next work").
