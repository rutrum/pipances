# Tabulator Consolidation — Plan

Finish the Tabulator migration started in `plans/inbox-tabulator.md`. That plan
landed the inbox and the `/data/*` tables. This plan covers the three remaining
hand-rolled tables, the in-place replacement of the old inbox, and the removal
of every piece of the custom table stack.

## Goal

1. `/inbox` serves the Tabulator inbox. The old HTMX inbox and the temporary
   `/inbox-tabulator` path both disappear; there is no redirect and no
   backwards compatibility. The navbar has one Inbox entry.
2. The Explore transaction list is a Tabulator remote table (read-only) that
   uses Tabulator's own header filters, exactly like `/data/transactions`.
   Page-level date presets navigate the page so the server-rendered
   stats/charts stay in sync. No HTMX.
3. The CSV import preview is a Tabulator table.
4. Delete `shared/_transaction_table.jinja2`, `shared/_table_macros.jinja2`,
   `shared/_txn_row.jinja2`, `shared/_pagination.jinja2`,
   `shared/_edit_input.jinja2`, the old inbox templates/routes, and the dead
   HTML row/edit routes and JSON endpoints that only they used.

## Current state

Already on Tabulator (leave alone beyond cleanup): `/data/accounts`,
`/data/categories`, `/data/external-accounts`, `/data/importers`,
`/data/imports`, `/data/transactions`, `/inbox-tabulator`.

Still hand-rolled:

| Surface | Table | Mechanism |
|---|---|---|
| `/inbox` (old) | pending txns | Jinja rows + `shared/_pagination.jinja2` + `_table_macros` sort headers + bulk toolbar |
| `/explore` | read-only txns | `shared/_transaction_table.jinja2` (sort/filter headers, pagination) inside `explore/_explore_content.jinja2`, HTMX-swapped |
| `/import` CSV preview | parsed rows | `import/_import_preview.jinja2` `<table>` with duplicate line-through |

`/data/transactions` already uses the exact column set Explore needs
(Date, Amount, Description, Category, External, Internal) via
`static/js/pages/transactions-table.js` and `POST /api/transactions/table`.

## Locked decisions

| # | Decision |
|---|---|
| 1 | `/inbox` is the only inbox URL. No redirect for `/inbox-tabulator`; delete it. Rename the Tabulator inbox artifacts in place (drop the `-tabulator` suffix). |
| 2 | One navbar entry, label "Inbox", `active_page="inbox"`. |
| 3 | Explore keeps server-rendered stats/charts and uses **full-page navigation** when the date preset / custom range changes. No HTMX. |
| 4 | Explore's column filtering is purely Tabulator header filters (Description, Category, External, Internal), the same as `/data/transactions`. No bespoke dropdowns. Query params seed the header filters. |
| 5 | `POST /api/transactions/table` is extended with optional `internal` / `external` / `category` name filters (see note under Phase 2). |
| 6 | Transfers are included everywhere. Remove `exclude_transfers=True` from Explore's stats/charts query. |
| 7 | Import preview data is serialized server-side into a `<script type="application/json">` block; `import-preview-table.js` builds a client-mode Tabulator from it. Duplicate rows keep `line-through opacity-50` via `rowFormatter`. |

### Decision 6 consequence

`exclude_transfers=True` currently joins `external` and requires
`Account.kind == "external"`, which drops internal↔internal transfer pairs
(seeded transfer rows reuse the same internal account as `external_id`). Showing
everything means:

- Explore's stats and charts will include transfers, so income/expense totals
  will grow and may show paired in/out amounts. This is intended.
- Remove the flag from `routes/explore.py`. `routes/api/explore.py` is deleted
  outright.
- `apply_filters(..., exclude_transfers=...)` and `fetch_page(...,
  exclude_transfers=...)` then have no callers. Remove the option (and its
  `AccountKind` import if now unused) as part of Phase 4 cleanup.

## Phase 1 — In-place inbox replacement

### Routes

The old `routes/inbox.py` and the new `routes/inbox_tabulator.py` both go away;
one new `routes/inbox.py` remains.

- Rename `routes/inbox_tabulator.py` → `routes/inbox.py`, replacing the old
  module. Delete the old `routes/inbox.py` in the same change (never keep both
  files).
- `GET /inbox-tabulator` → `GET /inbox` (`inbox_page`).
- `GET /inbox-tabulator/transactions/{txn_id}/edit-modal` →
  `GET /inbox/transactions/{txn_id}/edit-modal`.
- `shared_context("inbox_tabulator")` → `shared_context("inbox")`.
- No redirect route for `/inbox-tabulator`.
- Port the upload toast: read `toast`, `imported`, `duplicates`, `date_min`,
  `date_max`, `account` from the query string and pass `import_summary` through,
  mirroring the old `inbox_page`. `import_page.py` already redirects to
  `/inbox?...` and needs no change.

Routes deleted with the old module: `GET /inbox/commit-summary`,
`POST /inbox/commit`, `POST /inbox/retrain` (HTML). The Tabulator inbox uses
`/api/inbox/commit-summary`, `/api/inbox/commit`, `/api/inbox/retrain`.

### Renames (drop the `-tabulator` suffix)

- `src/pipances/routes/inbox_tabulator.py` → delete (merged into `routes/inbox.py`)
- `src/pipances/templates/pages/inbox_tabulator.jinja2` → `pages/inbox.jinja2`
  (old `pages/inbox.jinja2` deleted)
- `src/pipances/templates/inbox/_inbox_tabulator_modal.jinja2` →
  `inbox/_inbox_modal.jinja2`
- `static/js/pages/inbox-tabulator.js` → `static/js/pages/inbox.js`
- `static/js/pages/inbox-tabulator-modal.js` →
  `static/js/pages/inbox-modal.js`
- `tests/test_inbox_tabulator_api.py` → `tests/test_inbox_api.py`
- `tests/ui/test_inbox_tabulator.py` → `tests/ui/test_inbox.py`
- Container ids: `#inbox-tabulator-root` → `#inbox-root`,
  `#inbox-tabulator` → `#inbox-table`
- `static_version` calls and `<script src>` tags updated to the new filenames.

Keep the `window.PipancesInbox*` globals (`PipancesInbox`, `PipancesInboxTable`,
`PipancesInboxModal`) — they are already inbox-named.

### Navbar

`shared/_navbar.jinja2`: remove the `/inbox-tabulator` entry. Keep a single
`/inbox` entry (icon `inbox`, label "Inbox", `active_page == 'inbox'`) with the
`#inbox-badge` span that `inbox.js` updates.

### Templates

`pages/inbox.jinja2` (the renamed Tabulator page) gets the `initial_toast`
block ported from the old page. `inbox/_inbox_row.jinja2`,
`inbox/_inbox_thead.jinja2`, `inbox/_commit_summary.jinja2` are deleted.

### Python route pruning

- `routes/transactions.py`: delete `bulk_update_transactions`,
  `update_transaction`, `edit_modal`, `transaction_row`. Keep the split CRUD
  routes (`create_split`, `update_split`, `delete_split`) and
  `_render_splits_section`; the new inbox modal's splits section depends on
  them.
- `routes/data.py`: delete `create_account`, `update_account`,
  `edit_account_name`, `edit_account_type`, `edit_account_balance`,
  `edit_account_balance_date`, `update_category`, `edit_category_name`. Keep
  every `…_page`/redirect handler.
- `main.py`: drop the old `inbox_router` registration; register the new
  `routes/inbox.py` router.

### base.jinja2

- Drop the `htmx:oobAfterSwap` listener (no template emits OOB swaps after this
  plan).
- Drop the `data-ts-target` default (`'#txn-' + txnId`) in `initTomSelects`; the
  splits section always sets an explicit target.
- Keep `initTomSelects`, and the lucide/Alpine re-init on `htmx:afterSwap` —
  the splits section and the import page still use HTMX swaps.

### Tests

- `tests/test_inbox_api.py`: `/inbox-tabulator` → `/inbox`,
  `/inbox-tabulator/transactions/...` → `/inbox/transactions/...`; drop the
  "old modal route still renders" test.
- `tests/ui/test_inbox.py`: `goto("/inbox-tabulator")` → `goto("/inbox")`;
  `#inbox-tabulator` → `#inbox-table`.
- Delete old-inbox UI tests: `test_inbox_row_approve.py`,
  `test_inbox_transaction_modal_edit.py`, `test_oob_regressions.py`,
  `test_commit_flow.py`.
- `tests/ui/helpers.py`: delete the old-inbox locators (`approve_btn`,
  `approved_btn`, `inbox_page_label`, `badge_count`, `open_commit_dialog`,
  `confirm_commit`, `cancel_commit`, `do_approve`) or rewrite the ones still
  needed by `test_transaction_splits.py`.
- `tests/ui/test_transaction_splits.py`: retarget from the old modal to the
  inbox Tabulator modal (open via the row's `Edit` button); if
  `test_inbox.py`'s split test already covers the story, delete the duplicate.
- `tests/test_routes.py`: delete `test_inbox_get_200` and the invalid-param
  tests, the `/transactions/9.../edit-*` tests, the `/inbox/commit` workflow
  tests, and both `test_inbox_*_thead_oob` tests. Add/keep `GET /inbox` → 200
  and an assertion that `/inbox-tabulator` is now 404.
- Delete data-route tests that only exercise the removed HTML handlers:
  `test_edit_account_*`, `test_update_account_nonexistent`,
  the `POST /data/accounts` form tests, `test_edit_category_name_nonexistent`.
  The JSON equivalents in `tests/test_table_editing.py` stay.
- Add a test that `GET /inbox?toast=upload_success&imported=3&...` renders the
  success toast.

## Phase 2 — Explore table

### Endpoint

`routes/api/transactions.py`:

- Extend `TabulatorRequest` (or a subclass) with optional `internal`,
  `external`, `category` string fields.
- Map them in `transactions_table` onto
  `fetch_page(internal_filter=…, external_filter=…, category_filter=…)`.
- Do **not** set `exclude_transfers` (decision 6).

`routes/api/explore.py` is deleted (currently unreachable/`nowhere`; its
`_transactions_to_df` + chart code duplicates `routes/explore.py`).

Endpoint-extension note: with decision 4 (header filters only), Explore's own
table requests are already filtered by Tabulator's `filter` payload, so Explore
does not need to send these params. The extension is still added (decision 5)
and covered by API tests; it gives a documented server-side way to filter the
table without going through header filters, and keeps the option open if the
seed mechanism changes. If you would rather not carry an unused capability,
this is the one thing to cut.

### Route

Rewrite `routes/explore.py::explore_page`:

- Parse `preset`/`date_from`/`date_to` (existing `compute_date_range`) and
  `internal`/`external`/`category`.
- Fetch **all** matching transactions to build stats + charts, with
  `exclude_transfers` removed.
- Drop the second `fetch_page` page query (`total_count`, `total_pages`), the
  `endpoint`/`target` table context, the HTMX branch, and the OOB
  date-range/filter fragments.
- Pass the filter values and date-preset ranges to the template for the
  initial `initialHeaderFilter` seed.

Keep `_transactions_to_df`, `compute_stats`, and the three chart builders.

### Template

`pages/explore.jinja2`:

- Vega scripts + the three `vegaEmbed` calls (moved out of the old
  `explore/_explore_content.jinja2`).
- Stats row, chart cards, and the "No transactions match the current filters"
  alert (moved out of `_explore_content.jinja2`).
- Date presets + custom range, modelled on `data/_data_transactions.jinja2`,
  but as links / `window.location` navigation (decision 3). Preset ranges come
  from `compute_date_range` in the route, same as Data. Include a "Clear
  filters" link that drops the name params.
- `<div id="transactions-table-root" data-endpoint="/api/transactions/table"
  data-date-from=… data-date-to=… data-initial-filter='{"category.name": …,
  "external_account.name": …, "internal_account.name": …}'>` and
  `<div id="transactions-table">`.
- Include the table script with `static_version`.
- Deleted: `explore/_explore_content.jinja2`, `explore/_explore_table.jinja2`,
  `explore/_explore_date_range.jinja2`.

### JS

The Explore columns are identical to `/data/transactions`, so share the table
definition:

- Extract the table/column config from `transactions-table.js` into a small
  factory, e.g. `window.PipancesTables.transactions(container, options)` with
  `options = { ajaxURL, ajaxParams, initialHeaderFilter }`.
- `transactions-table.js` (Data) keeps its in-place date-preset wiring and
  calls the factory with `ajaxParams: () => ({date_from, date_to})`.
- New `explore-table.js` reads `data-*` from the root, calls the factory with
  `ajaxParams: () => ({date_from, date_to})` and
  `initialHeaderFilter: [{field, value}, …]` built from `data-initial-filter`.
  It does **not** wire date presets — those navigate.
- Header filters: Description search, Category, External, Internal — brought
  over unchanged from the Data column config.

### Tests

- `tests/test_routes.py`: replace `test_explore_htmx_returns_partial` with a
  test that the full page renders the chart scripts, the Tabulator container,
  and the expected `initialHeaderFilter` payload; keep `test_explore_get_200`
  and `test_explore_invalid_page`.
- Add API tests for `internal`/`external`/`category` on
  `POST /api/transactions/table`, including combination with
  `date_from`/`date_to`.
- Add a test that transfers are present in the Explore stats (seed a transfer
  pair, assert it is counted) to lock in decision 6.
- Add a UI test (`tests/ui/test_explore_table.py`): grid mounts, a preset click
  navigates (URL gains `preset=`) and updates the table, and
  `/explore?internal=…` seeds the header filter and filters the table.
- `tests/test_date_range.py` unaffected; verify no test asserts
  `exclude_transfers`.

## Phase 3 — Import preview table

### Route

Both `import_preview` and `import_preview_dedup` build a JSON-serializable
payload:

```python
preview_rows = [
    {
        "date": str(row["date"]),
        "amount_cents": row["amount_cents"],
        "description": row["description"],
        "duplicate": bool(duplicate_flags[i]) if duplicate_flags else False,
    }
    for i, row in enumerate(rows)
]
```

Pass `preview_rows` to `import/_import_preview.jinja2`. Keep `new_count`,
`dupe_count`, the status line, the importer/account selects, and the existing
HTMX wiring (the dedup re-render is the one HTMX surface this plan does not
touch; converting it to `fetch` + `table.setData()` is a possible follow-up,
see Out of scope).

### Template

Replace the `<table>` with:

```html
<script type="application/json" id="import-preview-data">{{ preview_rows | tojson }}</script>
<div id="import-preview-table"></div>
<script src="/static/js/pages/import-preview-table.js?v={{ static_version('js', 'pages', 'import-preview-table.js') }}"></script>
```

Dates are stringified in the route, so `tojson` only sees plain values. The
script tag must stay inside the swapped fragment so it re-runs on each dedup
re-render.

### JS

`static/js/pages/import-preview-table.js`:

- Parse `#import-preview-data`; bail if the container or JSON is missing.
- `new Tabulator(container, { data, layout: "fitColumns", height: "24rem",
  placeholder: "No rows", columns: [Date, Amount (money formatter),
  Description], rowFormatter: line-through/opacity for`duplicate`})`.
- Local mode only (client sort/filter). Optionally add a `Duplicate` badge
  column for clarity.

### Tests

- `tests/test_import.py` / `tests/test_routes.py`: assert
  `#import-preview-table` and `import-preview-table.js` appear in the preview
  response, and that `import-preview-data` parses to the expected row count and
  duplicate flags.
- Optional UI test: upload a fixture CSV, assert rows render and duplicates get
  the strike-through class.

## Phase 4 — Sweep and dead-code removal

After Phases 1–3:

1. Delete every remaining file from the custom table inventory:
   `pages/inbox.jinja2` (old), `inbox/_inbox_row.jinja2`,
   `inbox/_inbox_thead.jinja2`, `inbox/_commit_summary.jinja2`,
   `shared/_transaction_table.jinja2`, `shared/_table_macros.jinja2`,
   `shared/_txn_row.jinja2`, `shared/_pagination.jinja2`,
   `shared/_edit_input.jinja2`, `shared/_transaction_edit_modal.jinja2`,
   `shared/_modal_approve_btn.jinja2`, `shared/_toast.jinja2`,
   `shared/_badge.jinja2`, `data/_account_row.jinja2`,
   `data/_category_row.jinja2`.
   Keep `inbox/_inbox_modal.jinja2` and `shared/_splits_section.jinja2`.
2. Delete the dead JSON endpoints and their schemas/serializers:
   `GET /api/inbox` (`list_inbox_transactions`), `GET /api/transactions`
   (`list_transactions`), `GET /api/descriptions` (`search_descriptions`),
   `GET /api/imports` (`list_imports`), and `routes/api/explore.py`. Drop
   `txn_page_to_dict`, and `PaginatedTransactions`/`PaginationInfo`/
   `ExploreResponse`/`ExploreStats`/`ExploreCharts` once unreferenced.
3. Remove the now-unused `exclude_transfers` option from `apply_filters` and
   `fetch_page`, plus the `AccountKind` import if nothing else uses it.
4. `base.jinja2` cleanup (Phase 1) re-verified.
5. `rg` for dangling references: `_transaction_table`, `_table_macros`,
   `_txn_row`, `_pagination`, `_edit_input`, `_inbox_row`, `_inbox_thead`,
   `_commit_summary`, `_account_row`, `_category_row`, `_explore_content`,
   `_explore_date_range`, `inbox-pagination`, `inbox-thead`, `inbox-table`,
   `inbox-tabulator`, `commit-dialog-container`, `#transaction-edit-modal`,
   `bulk-toolbar`. (`inbox-table` is now the new container id, so check
   context.)
6. Run `just deadcode` and drive the report to zero:
   - no orphan templates
   - no unused/dead macros
   - no `Dangling #id selectors`
   - no `URLs with no matching route`
   - no `Routes never requested from templates or JS`
   The residual `N value(s) left dynamic` line is informational.
7. `uv run vulture` should report nothing new.

## Phase 5 — Verification

```bash
just lint
just test
nix develop -c just test-ui
nix build .#pipances
just deadcode
```

Manual pass with `nix develop -c agent-browser` against a throwaway seed,
screenshots to `/tmp/agent-browser`:

- `/inbox` loads the Tabulator inbox; `/inbox-tabulator` is 404; the navbar
  shows one "Inbox" entry with a live badge.
- Hit `/inbox?toast=upload_success&imported=3&duplicates=1&date_min=2026-01-01&date_max=2026-01-03&account=Checking`
  and confirm the success toast.
- Inbox regression: inline edit, range paste, modal edit, splits, approve,
  commit, retrain, badge updates.
- `/explore`: charts + stats render; presets navigate and update charts and
  table; `?internal=…` / `?category=…` / `?external=…` seed the header filters
  and filter the table; header filter clearing works; table sort/pagination
  work; transfers appear in the stats.
- `/import` CSV preview: importer badges, account select triggers dedup
  re-render, Tabulator shows new/duplicate styling, "Add to Inbox" redirects to
  `/inbox` with the toast.
- Spot-check `/data/*` for regressions.
- No console errors on any page.

## Risks and gotchas

- **No redirect means old links 404.** `/inbox-tabulator` bookmarks and any
  external link die. Accepted by decision 1 (the tab never reached a user).
- **Single `routes/inbox.py`.** The rename must be one atomic change: delete
  the old module and create the new one together, or FastAPI will register two
  `/inbox` GET handlers.
- **Route ordering.** `/inbox/transactions/{txn_id}/edit-modal` (HTML) and the
  `/api/inbox/transactions/batch` PATCH are different prefixes, so no shadowing;
  but keep `/api/inbox/transactions/batch` declared before
  `/api/inbox/transactions/{txn_id}` as today.
- **Transfers in charts.** Including transfer pairs will double-count
  in/out in the income/expense stats. Intended (decision 6), but the numbers
  will visibly change; call it out in the commit message.
- **Header-filter seeding.** `initialHeaderFilter` is a table-level option
  (`[{field, value}]`); the field must match the column `field`
  (`category.name`, `external_account.name`, `internal_account.name`). Setting
  the field name and the column field differently silently no-ops.
- **No HTMX re-init of the Explore table.** The whole reason presets navigate.
  Never innerHTML-swap the Tabulator container; destroy the instance first if a
  swap is ever added.
- **`tojson` and dates.** Import preview rows contain `datetime.date`; stringify
  in the route, never rely on the JSON encoder for `date`.
- **Script execution in swapped fragments.** HTMX executes `<script>` in swapped
  content, which re-inits the preview table on dedup. Do not hoist the script
  into the outer page or it goes stale after the first account change.
- **`_splits_section.jinja2` depends on the split routes.** Keep
  `transactions.py`'s split CRUD and `_render_splits_section`; only the
  row/modal/bulk routes are dead.
- **`initTomSelects` is still needed** for the splits section's `ts-select`
  comboboxes inside the inbox modal. Do not delete it with the old modal.
- **Test fixtures.** `tests/ui/conftest.py` seeds once per session and several
  fixtures restore rows. Retargeting `test_transaction_splits.py` to the new
  modal must preserve those cleanup paths.
- **`active_page` rename.** Changing `shared_context("inbox_tabulator")` to
  `"inbox"` also changes the navbar comparison; a mismatch silently drops the
  active highlight, so verify visually.
- **Dead endpoint params.** Decision 5's endpoint extension may end up unused by
  the UI (see the note in Phase 2). If it does, either add a caller or drop it;
  do not leave an untested parameter.

## Out of scope

- Converting the import page's HTMX flow (tab switch, dedup, commit) to
  `fetch`. The preview table migration keeps that wiring; a follow-up could
  make `/import/preview/dedup` return JSON and call `table.setData()`.
- Inbox date/internal/import filters (the old page had them; the Tabulator
  inbox does not). Add as header filters later if wanted.
- Client-side chart re-rendering.
- Any change to ML/approval/commit/retrain semantics.
