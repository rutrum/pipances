## 1. Backend - Increase Dropdown Search Limit

- [x] 1.1 Update `widgets.py` - change `.limit(5)` to `.limit(50)` in categories query (line 26)
- [x] 1.2 Update `widgets.py` - change `.limit(5)` to `.limit(50)` in external-accounts query (line 41)

## 2. Backend - Add Description Combo Endpoint

- [x] 2.1 Add new `/api/combo/descriptions` endpoint in `widgets.py`
- [x] 2.2 Query unique non-null descriptions from Transaction table with `.limit(50)`
- [x] 2.3 Add exact_match logic similar to categories (compare case-insensitive)
- [x] 2.4 Add new edit endpoint `/transactions/{txn_id}/edit-description-combo` in `transactions.py`

## 3. Backend - Import Page Account Dropdown

- [x] 3.1 Update `_get_active_accounts()` in `import_page.py` to return ALL accounts (remove `kind` filter)
- [x] 3.2 Modify import preview route to pass grouped accounts to template

## 4. Frontend - Lock Approved Transaction Fields (but allow un-approve)

- [x] 4.1 Update `_inbox_row.html` - wrap edit triggers in `{% if not txn.marked_for_approval %}`
- [x] 4.2 Keep approval button functional - pressing "Approved" toggles to un-approve

## 5. Frontend - Description Combo Box

- [x] 5.1 Update `_inbox_row.html` - change description from `_edit_input` to use combo pattern
- [x] 5.2 Create new endpoint for description combo editing (reuse `_combo_edit.html`)

## 6. Frontend - Import Pages Grouped Accounts

- [x] 6.1 Update `_import_preview.html` - add groupby for account kind (internal vs external)
- [x] 6.2 Update `_import_manual.html` - add groupby for account kind

## 7. Frontend - Fix Blur Race Condition

- [x] 7.1 Update `_combo_edit.html` - add `pointer-events-none` class during blur timeout

## 8. Testing

- [x] 8.1 Run `just check` to verify no lint/type errors
- [x] 8.2 Run tests - all 86 passed
- [x] 8.3 Test all scenarios from spec manually via browser
- [x] 8.4 Verify approved transactions are not editable
- [x] 8.5 Verify description dropdown shows 50 results
- [x] 8.6 Verify import page shows grouped accounts
