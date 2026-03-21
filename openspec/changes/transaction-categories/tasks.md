## 1. Category Data Model

- [ ] 1.1 Add `Category` model to `models.py` (id, name with unique constraint)
- [ ] 1.2 Add `category_id` nullable FK column to `Transaction` model with relationship
- [ ] 1.3 Add ALTER TABLE migration in `db.py` `create_tables()` for `category_id` on existing databases

## 2. Combo Box Search Endpoint

- [ ] 2.1 Add generic search endpoint `GET /api/combo/{entity}?q=...` that returns up to 5 matching entities (case-insensitive partial match) plus a "Create new" option when no exact match exists
- [ ] 2.2 Implement `categories` entity handler (search by name)
- [ ] 2.3 Implement `external-accounts` entity handler (search external accounts by name)

## 3. Combo Box Templates

- [ ] 3.1 Create `_combo_edit.html` partial: text input with `hx-get` to search endpoint, dropdown results container, inline JS for arrow key navigation / Enter / Escape handling
- [ ] 3.2 Create `_combo_results.html` partial: list of matching options (each with `hx-patch` to assign) plus "Create [query]" option at bottom when applicable
- [ ] 3.3 Style combo box dropdown (positioned below input, highlighted option visually distinguished)

## 4. Inbox Category Column

- [ ] 4.1 Add category column to `_inbox_row.html` with click-to-edit span (show category name or "click to edit" placeholder)
- [ ] 4.2 Add `GET /transactions/{txn_id}/edit-category` endpoint that returns the combo box partial for categories
- [ ] 4.3 Add `category` field handling to `PATCH /transactions/{txn_id}` — accept category name, find-or-create category, assign to transaction
- [ ] 4.4 Update inbox page query to eagerly load `Transaction.category` relationship
- [ ] 4.5 Update `inbox.html` table header to include Category column

## 5. Retrofit External Account to Combo Box

- [ ] 5.1 Update `GET /transactions/{txn_id}/edit-external` to return the combo box partial instead of a plain text input
- [ ] 5.2 Verify existing `PATCH /transactions/{txn_id}` external field handling works with combo box selection flow (find-or-create via `_resolve_account`)

## 6. Categories Management Page

- [ ] 6.1 Add "Categories" tab link to `settings.html` tab bar
- [ ] 6.2 Create `settings_categories.html` template extending `settings.html` — table of categories with inline edit and input row for new entries
- [ ] 6.3 Create `_category_row.html` partial (name with click-to-edit, delete button)
- [ ] 6.4 Create `_category_input_row.html` partial (input row for creating new categories)
- [ ] 6.5 Add `GET /settings/categories` endpoint (list all categories, render page)
- [ ] 6.6 Add `POST /settings/categories` endpoint (create category, return new row partial)
- [ ] 6.7 Add `PATCH /categories/{category_id}` endpoint (update category name inline)
- [ ] 6.8 Add `DELETE /categories/{category_id}` endpoint (delete category, SET NULL on transactions, remove row)
- [ ] 6.9 Add `GET /categories/{category_id}/edit-name` endpoint (return inline text input)

## 7. Transaction Browsing — Category Filter and Column

- [ ] 7.1 Add category column to `_txn_row.html` (display category name or dash)
- [ ] 7.2 Add category filter dropdown to `transactions.html` filters (list categories with approved transactions, plus "Uncategorized" option)
- [ ] 7.3 Update `GET /transactions` endpoint to accept `category` query param and filter accordingly (including uncategorized)
- [ ] 7.4 Update transactions page query to eagerly load `Transaction.category` relationship
- [ ] 7.5 Update `_txn_table_body.html` table header to include Category column

## 8. Testing and Verification

- [ ] 8.1 Browser test: create categories via settings page, verify CRUD works
- [ ] 8.2 Browser test: assign category to inbox transaction via combo box (mouse and keyboard)
- [ ] 8.3 Browser test: edit external account via combo box, verify inline creation works
- [ ] 8.4 Browser test: verify category filter on transactions page
- [ ] 8.5 Browser test: delete a category and verify transactions revert to uncategorized
