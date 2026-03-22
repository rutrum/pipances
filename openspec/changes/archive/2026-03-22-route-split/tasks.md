## 1. Create routes package and shared utils

- [x] 1.1 Create `src/financial_pipeline/routes/__init__.py` (empty)
- [x] 1.2 Create `src/financial_pipeline/routes/_utils.py` with:
  - `TEMPLATES_DIR` path constant
  - `templates` Jinja2Templates instance
  - `shared_context()` async function (moved from `main.py`)

## 2. Extract route modules

Each task: create the module with an `APIRouter`, move the route handlers and their private helpers from `main.py`, update imports.

- [x] 2.1 Create `routes/dashboard.py` with:
  - `GET /dashboard` (`dashboard_page`)
  - `GET /dashboard/content` (`dashboard_content`)
  - `_dashboard_query()`, `_transactions_to_df()`, `_summary_context()`
  - `_render_categories_tab()`, `_render_accounts_tab()`
- [x] 2.2 Create `routes/upload.py` with:
  - `GET /upload` (`upload_page`)
  - `POST /upload` (`upload_file`)
- [x] 2.3 Create `routes/settings.py` with:
  - `GET /settings` redirect (`settings_redirect`)
  - `GET /settings/accounts` (`settings_accounts_page`)
  - `POST /settings/accounts` (`create_account`)
  - `PATCH /accounts/{account_id}` (`update_account`)
  - `GET /accounts/{account_id}/edit-*` (name, type, balance, balance-date)
  - `GET /settings/categories` (`settings_categories_page`)
  - `POST /settings/categories` (`create_category`)
  - `PATCH /categories/{category_id}` (`update_category`)
  - `DELETE /categories/{category_id}` (`delete_category`)
  - `GET /categories/{category_id}/edit-name` (`edit_category_name`)
- [x] 2.4 Create `routes/transactions.py` with:
  - `GET /transactions` (`transactions_page`)
  - `PATCH /transactions/bulk` (`bulk_update_transactions`)
  - `PATCH /transactions/{txn_id}` (`update_transaction`)
  - `GET /transactions/{txn_id}/edit-description` (`edit_description`)
  - `GET /transactions/{txn_id}/edit-external` (`edit_external`)
  - `GET /transactions/{txn_id}/edit-category` (`edit_category`)
  - `SORT_COLUMNS` constant (if used only here)
- [x] 2.5 Create `routes/inbox.py` with:
  - `GET /inbox` (`inbox_page`)
  - `GET /inbox/commit-summary` (`commit_summary`)
  - `POST /inbox/commit` (`commit_inbox`)
- [x] 2.6 Create `routes/widgets.py` with:
  - `GET /api/combo/{entity}` (`combo_search`)

## 3. Slim down main.py

- [x] 3.1 Remove all moved route handlers and helpers from `main.py`
- [x] 3.2 Import and register all routers via `app.include_router()`
- [x] 3.3 Keep in `main.py`: app creation, lifespan, static mount, `GET /` redirect, `STATIC_DIR`, uvicorn entry point

## 4. Verification

- [x] 4.1 Run `just test` and verify all tests pass
- [x] 4.2 Run `just check` and verify linting passes
- [x] 4.3 Run `just fmt` to fix any formatting issues
- [x] 4.4 Run `just seed && just serve` and spot-check that all pages render correctly
