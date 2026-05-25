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

## 4. Verification

- [ ] 4.1 `just seed` and restart server; manually smoke-test the full split flow in the browser
- [ ] 4.2 Verify: add split → remainder updates live → split persists → modal close refreshes row
- [ ] 4.3 Verify: edit split amount → remainder recalculates → persists on blur
- [ ] 4.4 Verify: delete split → remainder restores
- [ ] 4.5 Verify: Add Split button disabled when amount = 0 or would eliminate remainder
- [ ] 4.6 `just test` — confirm no unit test regressions
- [ ] 4.7 `just fmt` and `just lint`
