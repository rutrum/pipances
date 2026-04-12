## Why

The transaction table appears in two different pages (Explore and Data/Transactions) with nearly identical structure: same columns, same sort/filter logic, same row template. However, the template code is duplicated across `_explore_table.html` and `_data_transactions.html`. Additionally, the sort header macro is defined three times (Explore, Data, and hand-coded in Inbox), making the codebase harder to maintain and inconsistent to extend.

This consolidation reduces duplication, lowers maintenance burden, and makes it easier to add table features consistently across all views.

## What Changes

- Extract sort and filter header macros into a shared `_table_macros.html`
- Create a unified `_transaction_table.html` partial used by both Explore and Data/Transactions
- Consolidate date range pickers into `_transaction_date_range.html` (shared by both pages)
- Remove duplicate template definitions from `_explore_table.html` and `_data_transactions.html`
- Update `_explore_table.html`, `_data_transactions.html`, and `_inbox_thead.html` to use the shared macros
- Update routes to pass consistent context variables to the shared partials

**Not changed**: User-facing behavior, sorting/filtering logic, or transaction display. This is purely a code organization improvement.

## Capabilities

### New Capabilities

None. This is a refactoring with no new user-facing functionality.

### Modified Capabilities

None. The requirements and behavior of Explore and Data/Transactions pages remain unchanged. This is an implementation detail reorganization.

## Impact

**Affected code**:
- Templates: `_explore_table.html`, `_data_transactions.html`, `_inbox_thead.html`, `_explore_date_range.html`
- Routes: `routes/explore.py`, `routes/data.py` (minor context adjustments)
- No API or database changes

**Benefits**:
- Easier to maintain table features (sort indicators, filters, pagination)
- Faster to add new filter types or column types
- Consistent behavior across all transaction table views
- Lower test burden (fewer variations to test)
- Clear separation of concerns (date picker, table, macros)
