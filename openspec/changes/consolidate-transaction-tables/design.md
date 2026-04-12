## Context

Currently, the Explore and Data/Transactions pages both render transaction tables with identical structure (same columns, sort/filter logic, row template), but the template code is duplicated:

- `_explore_table.html` defines `sort_header()` and `filter_header()` macros
- `_data_transactions.html` defines identical but separate `sort_header()` and `filter_header()` macros
- `_inbox_thead.html` hand-codes headers without using a macro (causing the same repetition there)
- Both pages include their own date range pickers and filter containers

This duplication makes it harder to:
- Add new features (e.g., column width controls, new filter types) — changes needed in multiple places
- Fix bugs consistently — easy to miss one copy
- Understand the codebase — unclear which version is authoritative

The Inbox table is intentionally excluded from this consolidation because it has a fundamentally different row structure (`_inbox_row.html` with editing, checkboxes, and bulk toolbar vs `_txn_row.html` read-only).

## Goals / Non-Goals

**Goals:**
- Extract sort and filter header macros into a single reusable `_table_macros.html`
- Create a unified `_transaction_table.html` partial that encapsulates the common table structure, headers, pagination, and no-data state
- Create a shared `_transaction_date_range.html` partial for date filtering
- Update `_explore_table.html` and `_data_transactions.html` to use these shared partials
- Update `_inbox_thead.html` to use the macros
- Reduce template code duplication while maintaining identical user-facing behavior
- Make it easier to add consistent features to all transaction tables in the future

**Non-Goals:**
- Do not change sorting/filtering behavior or order of results
- Do not refactor Inbox table structure (it's fundamentally different)
- Do not add new user-facing features
- Do not change database schema or APIs
- Do not modify route logic beyond passing consistent context variables

## Decisions

### 1. Create `_table_macros.html` with parameterized macros

**Decision**: Extract `sort_header()` and `filter_header()` macros to a shared file.

**Rationale**: These macros are identical except for endpoint/target/include values, which should be parameters. This is the DRY principle applied directly.

**Macro signature**:
```jinja
sort_header(column, label, endpoint, target, include_selector, width_class='')
filter_header(column, label, accounts, current_filter, endpoint, target, include_selector)
```

**Alternatives considered**:
- Inline the sort logic into each template → rejected, breaks DRY
- Use a JS library for client-side sorting → rejected, breaks HTMX server-side model
- Create a custom HTMX plugin → overengineering for this scope

### 2. Create unified `_transaction_table.html`

**Decision**: Create a single transaction table partial that replaces the table logic in both `_explore_table.html` and `_data_transactions.html`.

**What it includes**:
- Filter state container (`<div id="{{ filters_container_id }}">`)
- Conditional no-data alert
- Table structure with:
  - Header row using `sort_header()` and `filter_header()` macros (via import)
  - Category filter (hardcoded, not a macro — it has special "Uncategorized" handling)
  - Transaction rows (`_txn_row.html`)
- Pagination (via `_pagination.html`)

**Context parameters** (passed from route):
- `endpoint`: e.g., `/explore` or `/data/transactions`
- `target`: e.g., `#explore-content` or `#data-content`
- `include_selector`: e.g., `#explore-filters, #explore-pagination-page-size`
- `filters_container_id`: e.g., `explore-filters` or `data-txn-filters`
- `pagination_id`: e.g., `explore-pagination` or `data-transactions-pagination`
- Plus all filter/sort/transaction data

**Alternatives considered**:
- Create conditional template with `if view == 'explore'` → rejected, violates separation of concerns
- Keep separate templates but use a macro for the table body → rejected, still have duplication
- Use a JS component to build tables → rejected, breaks HTMX model

### 3. Create separate `_transaction_date_range.html`

**Decision**: Date presets (All, YTD, 30d, etc.) are a separate concern from the table itself. Extract into `_transaction_date_range.html`.

**Rationale**: Explore already has `_explore_date_range.html`; Data/Transactions has the same UI duplicated inside `_data_transactions.html`. Separating concerns makes it clearer and easier to reuse.

**Design**: Date range partial accepts `endpoint`, `target`, `include_selector` parameters plus current `preset`, `date_from`, `date_to`.

**Alternatives considered**:
- Keep date range as part of `_transaction_table.html` with a conditional → rejected, violates SoC
- Merge `_explore_date_range.html` and the new date range into one → rejected, explore's date range is already working

### 4. Update include strategy in Explore and Data

**Decision**: 
- `_explore_table.html` becomes a 1-line wrapper: `{% include "_transaction_table.html" %}`
- `_data_transactions.html` becomes a 1-line wrapper: `{% include "_transaction_table.html" %}`
- Routes (`explore.py`, `data.py`) ensure they pass consistent context

**Rationale**: This makes it crystal clear that both pages use the same table, with only endpoint/target/selectors differing.

**Alternatives considered**:
- Keep routing logic in the templates → rejected, routes should determine behavior
- Create a template factory function → overengineering

### 5. Keep Inbox separate

**Decision**: `_inbox_thead.html` uses the `sort_header()` macro, but Inbox overall stays separate.

**Rationale**: Inbox has a completely different row template (`_inbox_row.html` with editing, checkboxes) and bulk toolbar. Merging it would require too many conditionals and violate the SoC principle. The macro extraction alone gives us most of the DRY benefit.

## Risks / Trade-offs

| Risk | Mitigation |
|---|---|
| Routes don't pass all required context variables | Create test early; define required context schema in comment above `_transaction_table.html` |
| Optional parameters (e.g., `category_options`) are missing at runtime | Add defensive checks in template: `{% if category_options %}...{% endif %}` |
| Date range logic in `_transaction_date_range.html` diverges from Explore's version | Consolidate to one source; `_explore_date_range.html` can import and use the shared one |
| Performance impact from extra template layers | Negligible; Jinja compilation is at startup, not request time |
| Future changes to sorting/filtering logic require changes in three places (macros + Inbox + maybe more) | Accepted; Inbox is separate by design. Document the macros clearly. |

## Migration Plan

### Phase 1: Create new shared templates (no changes to existing)
1. Create `_table_macros.html` with `sort_header()` and `filter_header()`
2. Create `_transaction_table.html` (unified table)
3. Create `_transaction_date_range.html` (shared date picker)

### Phase 2: Update routes to pass consistent context
1. Update `explore.py` to pass: `endpoint`, `target`, `include_selector`, `filters_container_id`, `pagination_id`
2. Update `data.py` data_transactions_page to pass the same

### Phase 3: Swap in new partials (safe because old templates still exist)
1. Update `_explore_table.html` to `{% include "_transaction_table.html" %}`
2. Update `_data_transactions.html` to `{% include "_transaction_table.html" %}`
3. Update `_explore_date_range.html` to use `_transaction_date_range.html` (or just reference it)
4. Update `_inbox_thead.html` to use `sort_header()` macro from `_table_macros.html`

### Phase 4: Clean up (remove old macro definitions)
1. Delete macro definitions from `_explore_table.html` (if keeping as wrapper)
2. Delete macro definitions from `_data_transactions.html` (if keeping as wrapper)
3. Delete date range duplication

### Rollback strategy
- Old templates can be restored from git if new partials have bugs
- No data migration required
- No route changes are breaking

## Open Questions

1. Should `_explore_date_range.html` be replaced entirely, or should it import `_transaction_date_range.html`?
   - **Recommendation**: Replace entirely if identical; reuse if Explore's version has unique features.

2. Should we consolidate the Category filter (the one with "Uncategorized") into a macro too?
   - **Recommendation**: Defer to a follow-up; it's more complex and this is good progress.

3. Do we want to make Inbox's sort headers use the macro too?
   - **Recommendation**: Yes, in Phase 3. No-data for Inbox since its row structure is different, but the headers can benefit.
