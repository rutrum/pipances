## 0. UI Test Scaffolding (write first, must fail before implementing)

- [ ] 0.1 Create `tests/ui/test_inbox_transaction_modal_edit.py` with Playwright tests for all scenarios
  - Test: Edit button opens modal
  - Test: Modal displays transaction context (date, amount, raw description)
  - Test: Edit description and blur persists change
  - Test: Clear description field and blur persists empty value
  - Test: Change external account dropdown persists change
  - Test: Clear external account dropdown
  - Test: Change category dropdown persists change
  - Test: Clear category dropdown
  - Test: Close modal via X button and row refreshes
  - Test: Close modal via Escape key and row refreshes
  - Test: Approve button in modal marks transaction approved
  - Test: Approve button disabled when description is empty
  - Test: Field validation error displays inline and modal stays open
  - Test: Row displays fields as read-only (no inline edit spans)
- [ ] 0.2 Run `just test-ui` and confirm all new tests FAIL

## 1. Backend Endpoint: Edit Modal

- [ ] 1.1 Add `GET /transactions/{id}/edit-modal` endpoint to `routes/transactions.py`
  - Returns DaisyUI modal HTML with form containing:
    - Read-only context: date, amount, raw_description
    - Editable fields: 
      - description (text input)
      - external_id (simple select dropdown with all external accounts)
      - category_id (simple select dropdown with all categories)
    - Approve button
    - Close button (X)
  - Load transaction with relationships (internal, external, category)
  - Load all available external accounts and categories for populating selects

- [ ] 1.2 Create `_transaction_edit_modal.html` template
  - DaisyUI `<dialog>` component with form containing:
    - Read-only context section (date, amount, raw_description)
    - Form field for description: `<input type="text">` with `hx-trigger="blur"` for HTMX PATCH
    - Form field for external account: Embed `_combo_edit.html` with field_name="external_id" and txn_id
    - Form field for category: Embed `_combo_edit.html` with field_name="category_id" and txn_id
    - Error divs with response-targets for 422 handling on each field
    - Approve button (enabled/disabled based on description not empty)
    - Close button (X)

## 2. Frontend Template: Inbox Row

- [ ] 2.1 Update `_inbox_row.html` to replace inline edit spans with Edit button
  - Remove clickable `<span>` elements with `hx-get="/edit-description-combo"`, `hx-get="/edit-external"`, `hx-get="/edit-category"`
  - Add single Edit button: `hx-get="/transactions/{id}/edit-modal"` → `hx-target="#edit-modal-container"`
  - Display description, external, category fields as read-only text (no click handlers)

- [ ] 2.2 Update `pages/inbox.html` to add modal container
  - Add `<div id="edit-modal-container"></div>` before closing body tag
  - Add inline JavaScript to handle dialog lifecycle:
    - After HTMX swap completes, call `dialog.showModal()`
    - On dialog close event, fire GET to refresh row

## 3. JavaScript: Modal Lifecycle & Combo-Box Integration

- [ ] 3.1 Add JavaScript in `_transaction_edit_modal.html` to handle:
  - Auto-show dialog: `document.querySelector('dialog').showModal()` after HTMX renders
  - Close button: `onclick="this.closest('dialog').close()"`
  - Escape key handling: Prevent dialog from closing if combo-box dropdown is visible
    - Check if any `.combo-box` has open results: `document.querySelector('.combo-box #combo-results-* [data-combo-item]')`
    - If combo-box dropdown is visible, let Escape close the dropdown (via existing combo behavior)
    - If no dropdown visible, allow Escape to close modal (native behavior)
  - On dialog close event (`close` event listener): 
    - Fire silent HTMX GET `/transactions/{id}/row` to refresh row in table
    - This GET returns `<tr>` HTML with OOB swap attribute
    - Modal container clears itself

- [ ] 3.2 Create `GET /transactions/{id}/row` endpoint in `routes/transactions.py` if not exists
  - Returns single transaction row HTML (`<tr>` element)
  - Used for refreshing row after modal closes
  - Includes OOB swap attribute so HTMX updates the row in place
  - Loads transaction with relationships (internal, external, category)

## 4. Backend Field Updates: PATCH Handling

- [ ] 4.1 Ensure `PATCH /transactions/{id}` endpoint handles individual field updates from modal
  - Each field (description, external_id, category_id) can be PATCH'd independently
  - Return updated form HTML (re-rendered modal template) on success for error feedback display
  - Return 422 with error message on validation failure
  - Error message targets the appropriate error div in modal via response-targets extension (`hx-target-422`)

- [ ] 4.2 Add validation: description required for approval
  - When user clicks Approve button in modal
  - Check if description is empty/null; if so, return error with 422 status
  - Error message targets error div in modal via response-targets

- [ ] 4.3 Clear ML confidence when user edits a field
  - When PATCH updates description → set `ml_confidence_description` to `None`
  - When PATCH updates external_id → set `ml_confidence_external` to `None`
  - When PATCH updates category_id → set `ml_confidence_category` to `None`

## 5. Cleanup: Remove Old Inline Edit Endpoints and Templates

- [ ] 5.1 Remove `/transactions/{id}/edit-description-combo` endpoint from `routes/transactions.py`
- [ ] 5.2 Remove `/transactions/{id}/edit-external` endpoint from `routes/transactions.py`
- [ ] 5.3 Remove `/transactions/{id}/edit-category` endpoint from `routes/transactions.py`
- [ ] 5.4 Remove inline edit entry points (the click-to-edit logic) but KEEP combo templates:
  - KEEP: `src/pipances/templates/shared/_combo_edit.html` (now used by modal)
  - KEEP: `src/pipances/templates/shared/_combo_results.html` (now used by modal)

## 6. Verification

- [ ] 6.1 Run `just test-ui` and confirm all tests from step 0 now PASS
- [ ] 6.2 Run `just test` to confirm no unit test regressions
- [ ] 6.3 Manual smoke test in browser:
  - Open inbox
  - Click Edit on a transaction
  - Verify modal opens with form pre-filled with current values
  - Edit each field (description, external, category)
  - Verify changes persist immediately (modal form updates)
  - Close modal via X button and verify row refreshes with new values
  - Open Edit again and make different changes
  - Close modal via Escape key and verify row refreshes
  - Verify Approve button works from modal
  - Verify Approve button is disabled when description is empty
  - Verify old inline edit spans are gone from table rows
