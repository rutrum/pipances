## Why

Inbox transaction editing is currently scattered across three inline click-to-edit fields (description, category, external), requiring separate interactions for each field. This spreadsheet-like approach makes it hard to maintain as a cohesive form and difficult to see the full record context. A dedicated modal with a proper form will improve UX, reduce complexity, and provide a foundation for adding more fields (like ML confidence data) in the future.

## What Changes

- Replace inline click-to-edit spans in inbox table with a single **Edit** button per row
- Clicking Edit opens a modal containing a form with:
  - Description (text input, persists on blur)
  - External account (select dropdown, persists on change)
  - Category (select dropdown, persists on change)
  - Approve button (intentional user action, separate from field edits)
- Changes persist immediately as fields are edited (no "Apply" button for individual records)
- Closing the modal refreshes the row in the table
- Simplify row template to display-only; move edit logic into dedicated modal template

## Capabilities

### New Capabilities
<!-- None - this change modifies existing editing behavior -->

### Modified Capabilities
- `inbox-review`: Transition from inline click-to-edit fields to modal-based form for editing transaction description, external account, and category

## Impact

**Templates:**
- `_inbox_row.html`: Replace three clickable spans with single Edit button
- `pages/inbox.html`: Add modal container
- New: `_transaction_edit_modal.html` (modal form template)

**Routes:**
- `routes/inbox.py`: Add GET `/transactions/{id}/edit-modal` endpoint (returns modal HTML)
- `routes/transactions.py`: Modify PATCH `/transactions/{id}` to support field-by-field updates from modal

**Complexity reduction:**
- Remove three inline edit endpoints: `/transactions/{id}/edit-description-combo`, `/edit-external`, `/edit-category`
- Consolidate edit form logic into single modal template
