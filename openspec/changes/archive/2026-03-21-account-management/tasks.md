## 1. Model and database changes

- [x] 1.1 Add `starting_balance_cents` (Integer, default 0), `balance_date` (Date, nullable), and `active` (Boolean, default True) columns to the Account model in `models.py`
- [x] 1.2 Remove `SEED_ACCOUNTS` and `seed_accounts()` from `db.py`
- [x] 1.3 Remove `seed_accounts()` call from the lifespan handler in `main.py`

## 2. Settings page shell and routing

- [x] 2.1 Add `/settings` route that redirects to `/settings/accounts`
- [x] 2.2 Create `settings.html` template with tab layout (Accounts tab active, room for future tabs)
- [x] 2.3 Create `settings_accounts.html` template extending settings layout with the accounts table
- [x] 2.4 Add "Settings" link with icon to `_navbar.html` (after Dashboard)

## 3. Account listing

- [x] 3.1 Add `GET /settings/accounts` route that queries active internal accounts (kind != 'external', active = True) and renders the accounts table
- [x] 3.2 Create `_account_row.html` partial for rendering a single account row (name, type, starting balance, balance date, actions)
- [x] 3.3 Handle empty state: display message when no accounts exist, with the input row still available
- [x] 3.4 Add "Show closed" toggle that re-fetches the table via HTMX to include closed accounts, visually distinguishing them

## 4. Account creation (inline row)

- [x] 4.1 Add inline input row at the bottom of the accounts table (visually distinct from data rows) with fields: name, type, starting balance, balance date, and Add button
- [x] 4.2 Add `POST /settings/accounts` route that creates a new account, validates kind != "external" and unique name, returns the new row + fresh empty input row via HTMX
- [x] 4.3 Display inline error messages for validation failures (duplicate name, "external" type)

## 5. Inline editing

- [x] 5.1 Add click-to-edit endpoints for account name (`GET /accounts/{id}/edit-name`) returning an inline text input
- [x] 5.2 Add click-to-edit endpoints for account type (`GET /accounts/{id}/edit-type`) returning an inline text input
- [x] 5.3 Add click-to-edit endpoints for starting balance (`GET /accounts/{id}/edit-balance`) returning an inline number input
- [x] 5.4 Add click-to-edit endpoints for balance date (`GET /accounts/{id}/edit-balance-date`) returning an inline date input
- [x] 5.5 Add `PATCH /accounts/{id}` route that updates account fields, validates kind != "external" and unique name, returns the updated `_account_row.html`

## 6. Close and reopen

- [x] 6.1 Add close action button on each active account row that sends `PATCH /accounts/{id}` with `active=false`
- [x] 6.2 Add reopen action button on closed account rows (visible when "Show closed" is on) that sends `PATCH /accounts/{id}` with `active=true`

## 7. Upload page modifications

- [x] 7.1 Update the upload page account dropdown query to filter by `active=True` in addition to `kind != 'external'`
- [x] 7.2 Add empty-state handling: when no active internal accounts exist, show a message linking to `/settings/accounts` and disable the upload form
