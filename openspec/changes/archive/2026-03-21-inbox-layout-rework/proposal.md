## Why

The inbox is the primary workspace where users review and approve transactions. The current flat 8-column table layout wastes horizontal space, has visual instability when toggling between view/edit modes, and lacks a commit confirmation step. This rework improves information density, editing ergonomics, and commit safety.

## What Changes

- **Two-tier row layout**: Each transaction row becomes two lines. Top line shows date, amount, and the three editable fields (description, category, external). Bottom line (muted) shows internal account and raw description as read-only context.
- **Approve button replaces checkbox**: The approval checkbox becomes a button with three visual states: disabled (missing required fields), ready (clickable), and approved (green/success). A transaction requires description to be set before it can be approved (external account always has a value from import; category is optional).
- **Column width stability**: Editable cells use matching `min-width` on both display spans and edit inputs so toggling between view/edit modes doesn't shift the table layout.
- **Combobox clipping fix**: The combo box dropdown is no longer clipped by the table's `overflow-x-auto` wrapper.
- **Commit confirmation dialog**: Clicking "Commit" shows a confirmation dialog summarizing the number of transactions to be committed and listing any new categories and external accounts that will be persisted.
- **Empty inbox state**: When all transactions are committed, show a friendly "All cleaned up!" message with a link to upload.

## Capabilities

### New Capabilities
- `commit-confirmation`: Confirmation dialog shown before committing approved transactions, summarizing counts and new entities to be created

### Modified Capabilities
- `inbox-review`: Two-tier row layout, approve button (replaces checkbox with three-state logic), column width stability, empty state messaging
- `combo-box`: Fix dropdown clipping when rendered inside overflow-constrained containers

## Impact

- **Templates**: `inbox.html` and `_inbox_row.html` are substantially rewritten. `_combo_edit.html` needs a clipping fix.
- **Backend**: The PATCH endpoint's approval toggle logic changes to support the button interaction. The commit endpoint needs to query for new (unpersisted-until-commit) categories and external accounts to build the confirmation summary.
- **CSS**: New styles for two-tier rows, approve button states, and confirmation dialog.
- **No schema changes**: The `Transaction` model is unchanged. The `marked_for_approval` field continues to work as-is.
