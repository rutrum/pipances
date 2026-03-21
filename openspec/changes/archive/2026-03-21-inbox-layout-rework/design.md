## Context

The inbox page (`/inbox`) currently renders pending transactions in a flat 8-column table. Each row has: approve checkbox, date, amount, raw description, description, category, external, internal. Clicking description/category/external triggers inline editing via HTMX. The combobox component (`_combo_edit.html`) uses `position: absolute` inside an `overflow-x-auto` wrapper, causing dropdown clipping. The approve checkbox and commit button have no confirmation step.

Key files:
- `templates/inbox.html` — page layout and table structure
- `templates/_inbox_row.html` — single row partial (returned by PATCH)
- `templates/_combo_edit.html` — combobox editing widget
- `main.py` — `inbox_page`, `update_transaction`, `commit_inbox` endpoints

## Goals / Non-Goals

**Goals:**
- Restructure inbox rows into a two-tier layout that separates editable fields from read-only context
- Replace the approval checkbox with a three-state button
- Eliminate column width jitter when toggling between view and edit modes
- Fix combobox dropdown clipping
- Add a commit confirmation dialog with summary of new entities
- Improve empty inbox messaging

**Non-Goals:**
- Selection checkboxes and bulk operations (Change 2: `inbox-bulk-operations`)
- Filtering and sorting (Change 2)
- Changing the combobox component's core behavior (search, keyboard nav, create-new)
- Changing the Transaction data model

## Decisions

### Two-tier row structure

Each `<tr>` renders two visual lines using a single table row with internal layout.

**Approach:** Use a CSS grid or flex layout inside `<td>` cells that span the row content. The top tier contains date, amount, and the three editable fields. The bottom tier (smaller, muted text) shows internal account and raw description.

**Structure:**
```
<tr>
  <td colspan="full-width">
    <div class="grid grid-cols-[auto_auto_1fr_1fr_1fr_auto]">
      <!-- Top tier: date, amount, description, category, external, approve btn -->
    </div>
    <div class="text-xs text-base-content/50 pl-[offset]">
      <!-- Bottom tier: internal account + raw description -->
    </div>
  </td>
</tr>
```

**Alternative considered:** Keeping a flat `<table>` with separate `<td>` elements and hiding raw description / internal into subtitle spans within individual cells. Rejected because it doesn't reduce column count and still causes width instability.

**Alternative considered:** Ditching `<table>` entirely for a card/list layout. Rejected because table semantics still make sense for tabular transaction data, and DaisyUI's table styling gives us zebra striping and density for free.

### Column width stability

**Approach:** Apply a consistent `min-width` class to both the display `<span>` and the `<input>` for each editable cell. Use the same width utility (e.g. `min-w-40` for description, `min-w-32` for category/external) on both states. The HTMX swap replaces inner content but the outer container with the fixed width remains stable.

**Implementation:** Wrap each editable field in a container `<div>` with the `min-width` set, so the swap target is the inner content, not the sized container.

```html
<div class="min-w-40">
  <span hx-get="..." hx-target="this" hx-swap="innerHTML">
    {{ txn.description or "click to edit" }}
  </span>
</div>
```

When editing, the `<span>` is replaced with an `<input class="w-full">` that fills the same container.

### Approve button states

**Three states driven by data:**

| State | Condition | Rendering |
|-------|-----------|-----------|
| Disabled | `description` is null | `btn-ghost btn-disabled` with muted text |
| Ready | Has description set | `btn-outline btn-sm` "Approve" |
| Approved | `marked_for_approval = true` | `btn-success btn-sm` "Approved" |

Note: External account is not part of the approval gate because the ingest process always sets external from the raw description (e.g. "AMZN MKTP US*1A2B3C" becomes an external account). It always has a value — the user may edit it but it's never empty. Category is optional. Description is the only field that starts null and must be filled by the user.

The button triggers `hx-patch="/transactions/{id}"` with `{"marked_for_approval": "toggle"}`, same as the current checkbox. The row partial (`_inbox_row.html`) evaluates the state on each render.

**Decision:** State evaluation happens in the template, not the backend. The template checks `txn.description` and `txn.marked_for_approval` to determine which button variant to render. This keeps the backend simple.

### Combobox clipping fix

**Problem:** `_combo_edit.html` renders the dropdown with `position: absolute` inside a `div.overflow-x-auto` on `inbox.html`, causing the dropdown to be clipped at the table boundary.

**Approach:** Remove `overflow-x-auto` from the table wrapper on the inbox page. The two-tier layout with fewer effective columns should eliminate the need for horizontal scrolling. If the table still needs horizontal scroll on very small screens, use `overflow-x-auto overflow-y-visible` or move the dropdown to use `position: fixed` with JS-calculated coordinates.

**Preferred path:** Simply removing `overflow-x-auto` since the new layout is narrower. Test on reasonable viewport widths (>=768px). The app is a self-hosted desktop tool, not a mobile app.

### Commit confirmation dialog

**Approach:** Use a DaisyUI modal (`<dialog>` element). When the user clicks "Commit":

1. An HTMX GET request fetches `/inbox/commit-summary` which returns the modal content
2. The modal content includes: count of approved transactions, list of category names that don't yet exist in the `categories` table as committed-transaction references, list of external account names that are new (created during inbox editing but not yet referenced by any approved transaction)
3. The modal has Cancel and Confirm buttons. Confirm triggers the existing `POST /inbox/commit`

**New endpoint:** `GET /inbox/commit-summary` — queries marked transactions, identifies new categories and external accounts, returns a modal partial.

**What counts as "new":** A category or external account is "new" if it was created during inbox editing and is only referenced by pending transactions (no approved transactions reference it yet). This is the accurate definition — these entities technically exist in the DB already but have never been part of a committed batch.

### Empty inbox state

Replace the current "No pending transactions" `alert-info` with a friendlier message: "All cleaned up!" with a subtle illustration or icon, plus the existing link to upload.

## Risks / Trade-offs

- **Two-tier rows increase vertical space per transaction** — Each row is taller. For large inboxes (100+ transactions) this means more scrolling. Mitigation: the increased information density per row (fewer columns, context as sublabel) offsets this. Filtering (Change 2) will also reduce visible row count.

- **Removing overflow-x-auto may cause layout issues on narrow viewports** — Mitigation: the inbox is a desktop-first self-hosted tool. Test at 1024px+ widths. If issues arise, add a responsive breakpoint.

- **Commit summary query adds a round-trip** — User clicks Commit, waits for summary, then confirms. Mitigation: the query is simple (count marked transactions, check category/account references) and should be <100ms on any reasonable dataset.

- **Template-driven button state could get out of sync** — If the user edits description but the row doesn't re-render, the approve button state is stale. Mitigation: every PATCH already returns the full re-rendered row partial, so the button state updates on every edit.
