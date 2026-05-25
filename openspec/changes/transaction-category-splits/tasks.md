## 1. Model and DB

- [x] 1.1 Add `TransactionSplit` model to `models.py` (fields: id, transaction_id FK cascade, category_id FK nullable, amount_cents NOT NULL)
- [x] 1.2 Add `splits` relationship to `Transaction` in `models.py` (cascade all/delete-orphan, ordered by id)
- [x] 1.3 Add `transaction_splits` table migration to `db.py` `create_tables()` (check if table exists before creating)

## 2. Backend Routes

- [x] 2.1 Import `TransactionSplit` in `routes/transactions.py` and add `selectinload` for splits in the `edit_modal` route
- [x] 2.2 Add helper `_render_splits_section(request, session, txn)` that renders `_splits_section.jinja2` with txn + categories
- [x] 2.3 Add `POST /transactions/{txn_id}/splits` — parse `amount_dollars` + `category_id`, validate (amount > 0, sum < total), create split, return partial
- [x] 2.4 Add `PATCH /transactions/{txn_id}/splits/{split_id}` — update amount and/or category, validate remainder > 0, return partial
- [x] 2.5 Add `DELETE /transactions/{txn_id}/splits/{split_id}` — delete split, return partial

## 3. Templates

- [x] 3.1 Add Alpine.js script to `base.jinja2` (`/static/js/alpine.min.js` with `defer`)
- [x] 3.2 Create `templates/shared/_splits_section.jinja2`:
- [x] 3.3 Include `_splits_section.jinja2` in `_transaction_edit_modal.jinja2` after the Category field, passing `txn` and `categories`

## 4. API-Level Tests

- [x] 4.1 Create `tests/test_splits.py` with in-memory DB + HTTPX client
- [x] 4.2 Add fixture `txn_with_split` (transaction + one pre-existing split)
- [x] 4.3 `POST /transactions/{id}/splits` — valid create (with and without category), 422 on zero/excess/exact amount, 404 on missing txn
- [x] 4.4 `PATCH /transactions/{id}/splits/{sid}` — update amount, update category, 422 if remainder eliminated, 404 on missing split
- [x] 4.5 `DELETE /transactions/{id}/splits/{sid}` — delete and return partial, 404 on missing split

## 5. UI Tests (Story-Based)

- [x] 5.1 Create `tests/ui/test_transaction_splits.py`
- [x] 5.2 Add `txn_for_splitting` fixture to `ui/conftest.py` — picks pending Target (-$125.00), ensures description + external set, yields `{txn_id, amount_cents}`, cleans up splits + restores txn on teardown
- [x] 5.3 **Story A: "Add and remove a split"** — complete lifecycle of a single split on a fresh transaction
- [x] 5.4 **Story B: "Multiple splits and edit validation"** — build multiples, hit server 422
- [x] 5.5 **Story C: "Three-split transaction"** — build to 3, delete mid-sequence

## 6. Verification

- [x] 6.1 `just test` — confirm API-level split tests pass (124 passed)
- [x] 6.2 `just test-ui` — confirm story-based UI tests pass (3/3 passed)
- [x] 6.3 `just fmt` and `just lint` (2 pre-existing warnings in test_inbox_modal_edit.py)
