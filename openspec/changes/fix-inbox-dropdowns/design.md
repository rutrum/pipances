## Context

The inbox uses a combo box component for inline editing of transaction fields (category, external account). Currently, several issues exist:

1. **Internal accounts missing from dropdown**: The import preview and manual import pages filter `Account.kind != AccountKind.EXTERNAL`, showing only internal accounts. But users need to select internal accounts during import, and the existing external account dropdown in the inbox only shows external accounts.

2. **Search limit too restrictive**: The combo search API hardcodes `.limit(5)` (widgets.py:26,41), but users often have more than 5 categories/external accounts.

3. **Approved transactions remain editable**: The inbox row template doesn't check `marked_for_approval` before rendering click-to-edit spans. Users can modify already-committed transactions.

4. **Description lacks autocomplete**: Description uses a simple `_edit_input.html` with no dropdown. Users want the same autocomplete experience as category/external.

5. **Keyboard navigation issues**: Tab key doesn't move between fields, and there's a race condition between blur timeout and dropdown item clicks.

## Goals / Non-Goals

**Goals:**
- Allow internal account selection in import dropdowns
- Increase combo search results from 5 to 50
- Make approved transactions read-only
- Add description autocomplete dropdown
- Fix keyboard navigation (tab order) and blur race condition

**Non-Goals:**
- No changes to database schema
- No changes to ML prediction behavior
- No new external dependencies

## Decisions

### D1: Internal accounts in external dropdown

**Decision**: Combine internal and external accounts in a single grouped dropdown for import pages.

**Alternatives considered**:
- Separate dropdowns for internal/external: Rejected - adds clutter, user needs to pick one account during import
- Filter-based selection: Rejected - adds complexity, single account is simpler

**Implementation**:
- Modify `_get_active_accounts()` in `import_page.py` to return all accounts (remove the filter)
- Update `_import_preview.html` template to group accounts by `kind` with visual separators
- Same for `_import_manual.html`

### D2: Dropdown limit increase

**Decision**: Change hardcoded `.limit(5)` to `.limit(50)` in `widgets.py`.

**Rationale**: Current limit is too restrictive for users with many categories/external accounts. 50 provides ample coverage while remaining performant.

### D3: Approved transaction fields read-only but togglable

**Decision**: Make text fields read-only while preserving the ability to un-approve.

**Implementation**:
- In `_inbox_row.html`, wrap edit triggers in `{% if not txn.marked_for_approval %}...{% endif %}`
- Keep the approval button functional - pressing it toggles from approved → pending (un-approve)

### D4: Description combo box

**Decision**: Create a new combo box pattern specifically for description field.

**Implementation**:
- Add new endpoint `/api/combo/descriptions` in `widgets.py`
- Query unique non-null descriptions from Transaction table
- Create new template `_edit_combo.html` (reusing `_combo_edit.html` logic)
- Modify `_inbox_row.html` to use combo pattern for description

### D5: Fix blur race condition

**Decision**: Use `pointer-events: none` on the input during blur timeout to prevent interaction attempts.

**Implementation**:
- In `_combo_edit.html`, add `pointer-events-none` class to input during blur timeout
- Alternatively: use `mousedown` event with `preventDefault()` on the wrapper

## Risks / Trade-offs

- **Risk**: Description combo could return thousands of unique descriptions for large datasets
- **Mitigation**: Add `.limit(50)` to description query, same as categories

- **Risk**: Grouped dropdown in import pages adds template complexity
- **Mitigation**: Use Jinja2 `{% groupby %}`` or pre-group in Python before rendering

- **Risk**: Tab navigation may conflict with existing HTMX behavior
- **Mitigation**: Test thoroughly; may need to prevent default on tab and manually handle focus

## Migration Plan

1. Deploy updated `widgets.py` (new endpoint, increased limit)
2. Deploy updated templates (`_inbox_row.html`, `_import_preview.html`, `_import_manual.html`, new `_edit_combo.html`)
3. Deploy updated `transactions.py` (description edit endpoint)
4. No database migration needed
5. Rollback: Revert to previous version - no data changes

## Open Questions

- Should description autocomplete search only approved transactions, or all transactions (including pending)?
- Should the dropdown group accounts by kind (checking, savings, credit card, external) in import pages, or just list them alphabetically?
- Should approved transactions be completely hidden from inbox (filtered out) or just non-editable?
