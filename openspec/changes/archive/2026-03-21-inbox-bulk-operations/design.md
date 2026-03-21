## Context

This change builds on `inbox-layout-rework`, which restructures inbox rows into a two-tier layout with an approve button (replacing the old approval checkbox). After that change lands, each row has: a data area (date, amount, editable description/category/external on top; internal account and raw description on bottom) and an approve button on the right. There is no selection mechanism and no filtering.

This change adds selection checkboxes, a bulk editing toolbar, and a filter bar. It depends on the layout from `inbox-layout-rework` being in place.

Key files (post-layout-rework):
- `templates/inbox.html` — page layout, table structure
- `templates/_inbox_row.html` — single row partial
- `main.py` — `inbox_page`, `update_transaction` endpoints

## Goals / Non-Goals

**Goals:**
- Enable multi-selection of inbox transactions via checkboxes
- Provide bulk editing of category, external account, and description across selected rows
- Provide bulk approval of selected rows
- Enable filtering the inbox by date range, internal account, and import batch
- Filters persist across commits and re-renders

**Non-Goals:**
- Sorting controls (default sort by date is sufficient)
- Saved/named filter presets
- Bulk delete or bulk reject
- Full-text search across descriptions

## Decisions

### Selection mechanism

**Approach:** Add a checkbox `<input type="checkbox">` as the leftmost element in each row. This is purely client-side state — no database persistence. A "select all" checkbox in the header toggles all currently visible (filtered) rows.

**Implementation:** Each checkbox has a shared CSS class (e.g. `select-txn`) and carries `data-txn-id`. A small inline `<script>` in `inbox.html` handles:
- Select-all toggle: sets all visible `.select-txn` checkboxes to match the header checkbox
- Selection count: updates the bulk toolbar visibility and count display
- Event delegation on the `<tbody>` for checkbox change events

**Alternative considered:** HTMX-driven selection (each checkbox triggers a server request). Rejected — selection is ephemeral UI state, no reason to round-trip to the server.

### Bulk toolbar

**Approach:** A `<div>` above the table, always visible. When no rows are selected, all inputs and buttons are disabled and the count shows "0 selected". When rows are selected, controls become enabled. Contains:
- Selection count display ("3 selected")
- Category combobox (reuses `_combo_edit.html` pattern but targets the bulk endpoint)
- External account combobox (same)
- Description text input
- "Apply" button
- "Approve Selected" button

**Partial apply semantics:** The Apply button collects values from the three fields. Only non-empty fields are sent in the request body. The server endpoint skips any field not present in the payload. This prevents accidental data wipes — if you only set category, description and external are untouched.

**Bulk toolbar comboboxes:** These are simpler than the inline row comboboxes. They don't need to target a specific transaction row — they just need to let the user pick/create a category or external account. The selected value is held in the input until "Apply" is clicked. No immediate server-side effect until Apply.

**Alternative considered:** Reusing the exact same `_combo_edit.html` with HTMX for the toolbar comboboxes. Rejected because the toolbar comboboxes have different semantics (they don't immediately patch a transaction — they stage a value for bulk apply). A simpler variant that just does search-and-select without immediate PATCH is cleaner.

### Bulk edit endpoint

**New endpoint:** `PATCH /transactions/bulk`

**Request body:** JSON or form data with:
```
{
  "ids": [1, 2, 3],
  "description": "Amazon Purchase",   // optional
  "category": "Shopping",             // optional
  "external": "Amazon"                // optional
}
```

Only fields present in the payload are applied. The endpoint loops through the IDs and applies the same logic as the existing single-transaction PATCH (resolve-or-create for category/external).

**Response:** Returns the full set of updated row partials so HTMX can swap them in place. Uses OOB swaps (`hx-swap-oob="outerHTML:#txn-1"`) to update each affected row.

**Alternative considered:** Sending individual PATCH requests per transaction from JS. Rejected — N round-trips for N selected rows is wasteful and causes visual flicker as rows update one by one.

### Bulk approve

**"Approve Selected" button in the toolbar.** Sends `PATCH /transactions/bulk` with `{"ids": [...], "marked_for_approval": true}`. Only transactions that meet the approval criteria (has description + non-default external) are actually marked — the rest are silently skipped. The response re-renders all affected rows so button states update.

**Alternative considered:** A separate endpoint for bulk approve. Rejected — the bulk PATCH endpoint can handle approval as just another field.

### Filter bar

**Approach:** A horizontal bar above the table (and above the bulk toolbar) with:
- Date range: two `<input type="date">` fields (from/to)
- Internal account: `<select>` dropdown populated with all internal accounts
- Import batch: `<select>` dropdown populated with recent imports (showing institution + date)
- Clear button: resets all filters

**HTMX-driven filtering:** Each filter input triggers `hx-get="/inbox"` with query parameters, targeting the `<tbody>`. The `inbox_page` endpoint reads query params (`date_from`, `date_to`, `internal_id`, `import_id`) and adds `.where()` clauses to the query.

**Filter values included in other requests:** The filter bar inputs use `hx-include` so that when other HTMX requests fire (like commit), the filter state is preserved. After a commit re-renders the tbody, the filters stay applied.

**Implementation detail:** Use `hx-trigger="change"` on the selects and `hx-trigger="change"` on the date inputs. All filter inputs share a common `hx-get="/inbox/rows"` target that returns just the `<tbody>` content.

**New endpoint:** `GET /inbox/rows` — returns only the filtered `<tbody>` content (the row partials), not the full page. The full `GET /inbox` continues to return the complete page. This separation keeps the filter bar stable while the table content updates.

**Alternative considered:** Client-side filtering with JS show/hide. Rejected — server-side filtering is simpler, consistent with the HTMX approach, and handles large datasets without loading everything into the DOM.

### Select-all interacts with filters

The "select all" checkbox in the header selects only the currently visible (filtered) rows. If you filter to "Chase" transactions and hit select-all, only Chase rows are selected. This is the intuitive behavior.

**Implementation:** The select-all handler queries `.select-txn` checkboxes within the current `<tbody>`, which only contains filtered rows (server-side filtering means non-matching rows aren't in the DOM).

## Risks / Trade-offs

- **Bulk toolbar combobox is a new variant** — It looks like the inline combobox but behaves differently (stages a value vs. immediately patching). Risk of user confusion. Mitigation: the toolbar is visually separated from the table, and the "Apply" button makes the two-step flow clear.

- **OOB swaps for bulk updates could be complex** — Returning N OOB-swapped row partials in one response. Mitigation: HTMX handles multiple OOB swaps well. The response is just concatenated row HTML with `hx-swap-oob` attributes. Test with 20+ selected rows.

- **Filter state could get lost on full page navigation** — If user navigates away and back, filters reset. Mitigation: acceptable for now. Filters are lightweight to re-apply. Could add URL query params later if needed.

- **Bulk approve silently skips incomplete rows** — If you select 10 rows and 3 are incomplete, only 7 get approved with no error. Mitigation: the response re-renders all rows, so the user sees which ones didn't change. Could add a toast ("7 of 10 approved, 3 skipped — missing required fields") for clarity.
