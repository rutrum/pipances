## 1. Create Data Page Layout

- [ ] 1.1 Create `data.html` template extending `base.html` — flex layout with sidebar (`w-56`) and content pane (`flex-1`)
- [ ] 1.2 Sidebar: DaisyUI `menu` component with `menu-title` items for "CONFIGURATION" and "DATA" section headers
- [ ] 1.3 Sidebar menu items: Accounts, Importers (under Configuration); Transactions, External Accounts, Categories, Import History (under Data)
- [ ] 1.4 Active state: highlight the current sidebar item based on the active section (passed as template variable)
- [ ] 1.5 Each menu item: `hx-get="/data/{section}"` targeting `#data-content`, with `hx-push-url="true"` for URL updates
- [ ] 1.6 Content pane: `<div id="data-content">{% block data_content %}{% endblock %}</div>`

## 2. Migrate Internal Accounts

- [ ] 2.1 Create `_data_accounts.html` partial (content for the accounts section) — move content from `settings_accounts.html` into this partial
- [ ] 2.2 Update routes: rename `GET /settings/accounts` to `GET /data/accounts`, update to use new layout template
- [ ] 2.3 Return partial on HTMX request (sidebar click), full page on direct navigation
- [ ] 2.4 Update `POST /settings/accounts` to `POST /data/accounts` for creating new accounts
- [ ] 2.5 Keep existing `PATCH /accounts/{id}` and edit endpoints unchanged (they return row partials, not pages)

## 3. Migrate Categories

- [ ] 3.1 Create `_data_categories.html` partial — move content from `settings_categories.html`, remove delete button from `_category_row.html`
- [ ] 3.2 Delete `DELETE /categories/{id}` endpoint from settings routes
- [ ] 3.3 Remove delete button markup from `_category_row.html`
- [ ] 3.4 Update routes: rename `GET /settings/categories` to `GET /data/categories`
- [ ] 3.5 Remove `POST /settings/categories` (category creation endpoint) — categories are created inline from transaction editing
- [ ] 3.6 Keep `PATCH /categories/{id}` and edit-name endpoints unchanged

## 4. Migrate Transactions Table

- [ ] 4.1 Create `_data_transactions.html` partial — the full transaction table with filters, sorting, pagination (content from old `transactions.html`)
- [ ] 4.2 Create `GET /data/transactions` route — same query logic as the old `GET /transactions`, returns partial on HTMX or full page on direct nav
- [ ] 4.3 Ensure HTMX interactions within the transaction table (sort, filter, paginate) still work correctly within the data page layout

## 5. Update Redirects and Router

- [ ] 5.1 `GET /data` redirects to `/data/accounts` (default section)
- [ ] 5.2 Register data router in `main.py`, remove old settings router registration
- [ ] 5.3 Delete old templates: `settings.html`, `settings_accounts.html`, `settings_categories.html`
- [ ] 5.4 Rename or refactor `routes/settings.py` to `routes/data.py`

## 6. Navbar Update

- [ ] 6.1 Update `_navbar.html`: rename "Settings" to "Data", update href to `/data`, update `active_page` check

## 7. Verification

- [ ] 7.1 Rebuild CSS (`just css`)
- [ ] 7.2 Verify `/data` redirects to `/data/accounts`
- [ ] 7.3 Verify sidebar navigation switches content without full page reload
- [ ] 7.4 Verify direct navigation to `/data/transactions` renders full page with sidebar
- [ ] 7.5 Verify internal accounts CRUD still works (create, edit name/type/balance/date, toggle active)
- [ ] 7.6 Verify category rename still works, delete button is gone
- [ ] 7.7 Verify transaction table filters, sort, pagination work within data page
- [ ] 7.8 Verify old `/settings/*` URLs return 404
- [ ] 7.9 Run `just check`
