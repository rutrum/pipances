## Why

The inbox dropdowns have several usability issues: internal accounts don't appear in the external account dropdown (users need to map transactions to internal accounts during import, but the dropdown only shows external accounts), the search results are capped at 5 items (often too few), approved transactions remain editable when they should be locked, description fields lack dropdown autocomplete that exists for category/external, and the overall keyboard navigation is buggy.

## What Changes

- **Add internal accounts to external account dropdown**: The import preview and manual import pages show internal accounts alongside external accounts in the account selection dropdown, with a visual separator between the two groups.
- **Increase dropdown search limit**: Raise the hardcoded `.limit(5)` to `.limit(50)` in the combo search API.
- **Lock approved transactions**: Transactions marked as approved have text fields (description, category, external) become read-only, but the approval button can still toggle to un-approve. Tab order cycles through: description → category → external → next row description.
- **Description dropdown**: Add click-to-edit autocomplete for description field using the same combo pattern as category/external.
- **Fix blur/revert race condition**: Prevent the blur timeout from firing when clicking dropdown items by using `mousedown` prevention more reliably.

## Capabilities

### New Capabilities
- `inbox-dropdown-improvement`: Comprehensive improvements to inbox dropdowns including search limits, read-only states, and new description autocomplete

### Modified Capabilities
- None (this is a pure UX/improvement change, no spec-level requirements change)

## Impact

- **Routes modified**: `widgets.py` (combo search), `transactions.py` (edit endpoints), `import_page.py` (account dropdowns)
- **Templates modified**: `_inbox_row.html`, `_combo_edit.html`, `_combo_results.html`, `_import_preview.html`, `_import_manual.html`, new `_edit_combo.html` for description
- **No database changes** required
- **No new dependencies** introduced
