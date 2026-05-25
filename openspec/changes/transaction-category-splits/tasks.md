## 1. Model and DB

- [ ] 1.1 Add `TransactionSplit` model to `models.py` (fields: id, transaction_id FK cascade, category_id FK nullable, amount_cents NOT NULL)
- [ ] 1.2 Add `splits` relationship to `Transaction` in `models.py` (cascade all/delete-orphan, ordered by id)
- [ ] 1.3 Add `transaction_splits` table migration to `db.py` `create_tables()` (check if table exists before creating)

## 2. Backend Routes

- [ ] 2.1 Import `TransactionSplit` in `routes/transactions.py` and add `selectinload` for splits in the `edit_modal` route
- [ ] 2.2 Add helper `_render_splits_section(request, session, txn)` that renders `_splits_section.jinja2` with txn + categories
- [ ] 2.3 Add `POST /transactions/{txn_id}/splits` — parse `amount_dollars` + `category_id`, validate (amount > 0, sum < total), create split, return partial
- [ ] 2.4 Add `PATCH /transactions/{txn_id}/splits/{split_id}` — update amount and/or category, validate remainder > 0, return partial
- [ ] 2.5 Add `DELETE /transactions/{txn_id}/splits/{split_id}` — delete split, return partial

## 3. Templates

- [ ] 3.1 Add Alpine.js script to `base.jinja2` (`/static/js/alpine.min.js` with `defer`)
- [ ] 3.2 Create `templates/shared/_splits_section.jinja2`:
  - Outer `<div id="splits-section-{txn.id}">` with Alpine `x-data` tracking `splitAmounts` dict, `newAmountDollars`, computed `remainder`
  - Remainder row (shown only when splits exist): read-only calculated amount + primary category label
  - Per-split rows: amount input (`@input` updates Alpine state, `hx-patch` on blur), category select (`hx-patch` on change), × delete button (`hx-delete`)
  - Add-split row: amount input (`x-model="newAmountDollars"`), category select, Add button (`:disabled` when invalid, `hx-post`)
  - Inline error display when remainder ≤ 0
- [ ] 3.3 Include `_splits_section.jinja2` in `_transaction_edit_modal.jinja2` after the Category field, passing `txn` and `categories`

## 4. API-Level Tests

- [ ] 4.1 Create `tests/test_splits.py` with in-memory DB + HTTPX client
- [ ] 4.2 Add fixture `txn_with_split` (transaction + one pre-existing split)
- [ ] 4.3 `POST /transactions/{id}/splits` — valid create (with and without category), 422 on zero/excess/exact amount, 404 on missing txn
- [ ] 4.4 `PATCH /transactions/{id}/splits/{sid}` — update amount, update category, 422 if remainder eliminated, 404 on missing split
- [ ] 4.5 `DELETE /transactions/{id}/splits/{sid}` — delete and return partial, 404 on missing split

## 5. UI Tests (Story-Based)

- [ ] 5.1 Create `tests/ui/test_transaction_splits.py`
- [ ] 5.2 Add `txn_for_splitting` fixture to `ui/conftest.py` — picks pending Target (-$125.00), ensures description + external set, yields `{txn_id, amount_cents}`, cleans up splits + restores txn on teardown
- [ ] 5.3 **Story A: "Add and remove a split"** — complete lifecycle of a single split on a fresh transaction
  - Open modal → splits form present, Add Split disabled (empty amount)
  - Type amount = total → disabled (remainder = 0)
  - Type valid amount ($50.00) → remainder shows $75.00, button enabled
  - Add split (no category) → split row + remainder row appear
  - Change split category to "Groceries" → PATCH persists
  - Re-open modal → split still there
  - Delete split → remainder row hidden, form back to clean state
  - Close modal → inbox row refreshes
- [ ] 5.4 **Story B: "Multiple splits and edit validation"** — build multiples, hit server 422
  - Add first split ($80.00, Entertainment) → remainder $118.00
  - Attempt second split ($120.00) → Alpine gate disabled (exceeds remainder)
  - Add valid second split ($60.00, Groceries) → two splits, remainder $58.00
  - Edit first split amount to $198.00 → blur → PATCH 422 with error + revert
  - Edit first split to $75.00 → blur → persists, remainder $63.00
  - Close modal → row refreshes
- [ ] 5.5 **Story C: "Three-split transaction"** — build to 3, delete mid-sequence
  - Add $60.00→Utilities → remainder $96.00
  - Add $45.00→Shopping → remainder $51.00
  - Add $30.00→Entertainment → remainder $21.00
  - Attempt 4th split ($25.00) → disabled ($25 > $21)
  - Delete middle split ("Shopping") → remainder jumps to $66.00
  - Close modal

## 6. Verification

- [ ] 6.1 `just test` — confirm API-level split tests pass
- [ ] 6.2 `just test-ui` — confirm story-based UI tests pass
- [ ] 6.3 `just fmt` and `just lint`
