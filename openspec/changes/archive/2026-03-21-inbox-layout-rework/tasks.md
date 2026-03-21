## 1. Two-tier row layout

- [x] 1.1 Rewrite `_inbox_row.html` to use two-tier structure: top tier (date, amount, description, category, external, approve button), bottom tier (internal account, raw description in muted text)
- [x] 1.2 Update `inbox.html` table structure — remove the 8-column `<thead>`, adapt to new row layout (fewer semantic columns or single-column with internal grid)
- [x] 1.3 Remove `overflow-x-auto` from the inbox table wrapper (fixes combobox clipping, new layout is narrower)

## 2. Column width stability

- [x] 2.1 Wrap each editable field (description, category, external) in a container with a fixed `min-width` class so the HTMX swap target is the inner content, not the sized container
- [x] 2.2 Ensure edit inputs use `w-full` within the fixed-width container so they fill the same space as the display span

## 3. Approve button

- [x] 3.1 Replace the approval checkbox in `_inbox_row.html` with a button element that renders three states: disabled (`btn-ghost btn-disabled` when description is null), ready (`btn-outline` "Approve"), approved (`btn-success` "Approved")
- [x] 3.2 Wire the approve button to `hx-patch="/transactions/{id}"` with `{"marked_for_approval": "toggle"}` — same PATCH endpoint, new UI element
- [x] 3.3 Verify the row re-renders correctly on approve/unapprove (button state updates, row styling changes)

## 4. Commit confirmation dialog

- [x] 4.1 Create `GET /inbox/commit-summary` endpoint that queries marked transactions, identifies new categories (only referenced by pending transactions) and new external accounts (same criteria), returns a modal partial
- [x] 4.2 Create `_commit_summary.html` modal template using DaisyUI `<dialog>` — shows transaction count, lists new categories and new external accounts, has Cancel and Confirm buttons
- [x] 4.3 Wire the "Commit" button to fetch the summary modal via HTMX GET, then display it. Confirm button triggers the existing `POST /inbox/commit`
- [x] 4.4 Handle the "no approved transactions" case — show warning toast instead of the modal (preserve current behavior)

## 5. Empty inbox state

- [x] 5.1 Update the empty inbox message in `inbox.html` to show a friendly "All cleaned up!" message with a link to upload

## 6. Testing and polish

- [x] 6.1 Browser-test the full flow: upload CSV, review inbox with new layout, edit description/category/external, approve, commit with confirmation dialog
- [x] 6.2 Verify combobox dropdown is no longer clipped at table boundary
- [x] 6.3 Verify column widths remain stable when toggling between view and edit modes
- [x] 6.4 Run `just fmt` and `just lint`
