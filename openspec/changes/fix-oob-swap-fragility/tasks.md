## 1. Phase 1: Hand-Constructed Fragments (Toast & Badge)

- [ ] 1.1 Create `templates/_toast.html` with `hx-swap-oob="innerHTML:#toast-container"` attribute
- [ ] 1.2 Create `templates/_badge.html` with `hx-swap-oob="innerHTML:#inbox-badge"` attribute
- [ ] 1.3 Update `routes/inbox.py` commit endpoint to render `_toast.html` instead of f-string
- [ ] 1.4 Update `routes/inbox.py` to render `_badge.html` instead of f-string
- [ ] 1.5 Update `routes/inbox.py` retrain endpoint to use `_toast.html` template
- [ ] 1.6 Remove all hand-constructed toast/badge f-strings from `routes/inbox.py`
- [ ] 1.7 Test commit workflow (verify toast and badge appear and OOB swaps work)
- [ ] 1.8 Test retrain workflow (verify toast and badge appear and OOB swaps work)
- [ ] 1.9 Test bulk operations (verify toast and badge appear and OOB swaps work)

## 2. Phase 2: ID Attribute Replace (Pagination & Transaction Rows)

- [ ] 2.1 Update `templates/_pagination.html` to add `hx-swap-oob="outerHTML:#inbox-pagination"` to root div
- [ ] 2.2 Update `routes/inbox.py` to render `_pagination.html` without string replace
- [ ] 2.3 Remove pagination string replace logic from `routes/inbox.py`
- [ ] 2.4 Update `templates/_transaction_row.html` to add `hx-swap-oob="outerHTML"` to root tr
- [ ] 2.5 Update `routes/transactions.py` to render `_transaction_row.html` without string replace
- [ ] 2.6 Remove transaction row string replace logic from `routes/transactions.py`
- [ ] 2.7 Verify inbox.py bulk operations use updated transaction row template
- [ ] 2.8 Test pagination updates (filter changes, page navigation, page size changes)
- [ ] 2.9 Test transaction row updates (bulk edits, individual edits)
- [ ] 2.10 Test that pagination OOB swap correctly updates `#inbox-pagination` element

## 3. Phase 3: CSS Class Replace (Date Range)

- [ ] 3.1 Update `templates/_explore_date_range.html` to add `hx-swap-oob="outerHTML:#explore-date-range"` to root div
- [ ] 3.2 Update `routes/explore.py` to render `_explore_date_range.html` without string replace
- [ ] 3.3 Remove date range string replace logic from `routes/explore.py`
- [ ] 3.4 Verify explore.py filter updates use updated date range template
- [ ] 3.5 Test date range updates (preset changes, custom date picks)
- [ ] 3.6 Test that date range OOB swap correctly updates `#explore-date-range` element

## 4. Verification & Cleanup

- [ ] 4.1 Verify all string replace logic removed from codebase (`grep -r "\.replace.*hx-swap-oob"`)
- [ ] 4.2 Verify all f-string OOB fragments removed from routes
- [ ] 4.3 Run full test suite to ensure no regressions
- [ ] 4.4 Test inbox commit workflow end-to-end (filter, select, commit, verify OOB swaps)
- [ ] 4.5 Test explore page filtering end-to-end (date range, categories, accounts)
- [ ] 4.6 Browser test: verify all OOB elements update correctly (no silent failures)
- [ ] 4.7 Code review: verify pattern consistency across all templates
- [ ] 4.8 Update any relevant documentation or comments about OOB pattern
