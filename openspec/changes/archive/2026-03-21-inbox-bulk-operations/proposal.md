## Why

After the inbox layout rework, each transaction is reviewed individually. When uploading a large batch (50+ transactions), many share the same category or external account. Users need a way to apply edits to multiple transactions at once, and to filter the inbox to focus on a specific subset. This change adds selection, bulk editing, bulk approval, and filtering to the inbox.

## What Changes

- **Selection checkboxes**: Each row gets a checkbox on the left for multi-selection. A select-all checkbox in the header toggles all visible (filtered) rows.
- **Bulk toolbar**: When one or more rows are selected, a toolbar appears above the table with fields for category, external account, and description. An "Apply" action sends only non-empty fields to the selected transactions (empty fields are no-ops, preventing accidental data wipes). A "Bulk Approve" button approves all selected transactions that meet the approval criteria.
- **Filter bar**: A persistent filter bar above the table with date range (two date inputs), internal account dropdown, and import batch dropdown. Each filter triggers an HTMX request to re-render the table body with filtered results. Filters persist across commits. A "Clear" button resets all filters.

## Capabilities

### New Capabilities
- `inbox-filtering`: Filter bar for narrowing visible inbox transactions by date range, internal account, and import batch
- `inbox-bulk-operations`: Selection checkboxes, bulk toolbar for editing and approving multiple transactions at once

### Modified Capabilities
- `inbox-review`: Rows gain a selection checkbox (separate from the approve button introduced in `inbox-layout-rework`)

## Impact

- **Templates**: `inbox.html` gains filter bar and bulk toolbar sections. `_inbox_row.html` gains a selection checkbox column.
- **Backend**: `inbox_page` endpoint gains query parameter filtering. A new `PATCH /transactions/bulk` endpoint applies partial updates to multiple transactions. A new endpoint or logic for bulk approval.
- **Frontend JS**: Minimal JS for select-all toggle behavior (check/uncheck all visible checkboxes). Bulk toolbar visibility toggle based on selection count.
- **Depends on**: `inbox-layout-rework` must be completed first (this builds on the two-tier row layout and approve button).
