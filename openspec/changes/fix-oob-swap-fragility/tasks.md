## 1. Phase 1: Hand-Constructed Fragments (Toast & Badge)

- [ ] 1.1 Create `templates/_toast.html` with `oob` parameter support
- [ ] 1.2 Create `templates/_badge.html` with `oob` parameter support
- [ ] 1.3 Update `routes/inbox.py` commit endpoint to render `_toast.html` instead of f-string
- [ ] 1.4 Update `routes/inbox.py` to render `_badge.html` instead of f-string
- [ ] 1.5 Update `routes/inbox.py` retrain endpoint to use `_toast.html` template
- [ ] 1.6 Remove all hand-constructed toast/badge f-strings from `routes/inbox.py`
- [ ] 1.7 Test commit workflow (verify toast and badge appear and OOB swaps work)
- [ ] 1.8 Test retrain workflow (verify toast and badge appear and OOB swaps work)
- [ ] 1.9 Test bulk operations (verify toast and badge appear and OOB swaps work)

## 2. Phase 2: ID Attribute Replace (Pagination & Transaction Rows)

- [ ] 2.1 Update `templates/_pagination.html` to add `{% if oob %}hx-swap-oob="outerHTML:#inbox-pagination"{% endif %}` to root div
- [ ] 2.2 Update `routes/inbox.py` to render `_pagination.html` with `oob=True` instead of string replace
- [ ] 2.3 Remove pagination string replace logic from `routes/inbox.py`
- [ ] 2.4 Update `templates/_transaction_row.html` to add `{% if oob %}hx-swap-oob="outerHTML"{% endif %}` to root tr
- [ ] 2.5 Update `routes/transactions.py` to render `_transaction_row.html` with `oob=True` instead of string replace
- [ ] 2.6 Remove transaction row string replace logic from `routes/transactions.py`
- [ ] 2.7 Update `routes/inbox.py` bulk operations to pass `oob=True` when rendering transaction rows
- [ ] 2.8 Test pagination updates (filter changes, page navigation, page size changes)
- [ ] 2.9 Test transaction row updates (bulk edits, individual edits)
- [ ] 2.10 Test that pagination OOB swap correctly updates `#inbox-pagination` element

## 3. Phase 3: CSS Class Replace (Date Range)

- [ ] 3.1 Update `templates/_explore_date_range.html` to add `{% if oob %}hx-swap-oob="outerHTML:#explore-date-range"{% endif %}` to root div
- [ ] 3.2 Update `routes/explore.py` to render `_explore_date_range.html` with `oob=True` instead of string replace
- [ ] 3.3 Remove date range string replace logic from `routes/explore.py`
- [ ] 3.4 Update `routes/explore.py` filter updates to pass `oob=True` when rendering date range
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
