## Why

Internal accounts are hardcoded in `db.py` as seed data. Users cannot create, edit, or retire accounts through the app. There is also no way to set a starting balance, which means dashboard totals only reflect imported transaction deltas rather than real account state. Account management needs to move into the UI.

## What Changes

- Add `starting_balance_cents`, `balance_date`, and `active` columns to the Account model
- New settings page at `/settings` with a tab layout (accounts tab first, room for future tabs)
- Accounts tab: list internal accounts, create new ones, inline edit (name, kind, starting balance, balance date), close/reopen
- Validation: user-created accounts cannot have kind "external"
- "Settings" link added to the navbar
- Remove `SEED_ACCOUNTS` from `db.py` — accounts are managed entirely through the UI
- Upload page handles gracefully when no internal accounts exist (prompt to create one)

## Capabilities

### New Capabilities
- `account-management`: CRUD operations for internal accounts via a settings page, including starting balance tracking and account archival

### Modified Capabilities
- `navigation`: Add "Settings" link to the navbar
- `csv-upload`: Handle empty internal accounts list gracefully (guide user to create accounts first)

## Impact

- `models.py`: New columns on Account (`starting_balance_cents`, `balance_date`, `active`)
- `db.py`: Remove `SEED_ACCOUNTS` and `seed_accounts()`
- `main.py`: New routes under `/settings`, remove `seed_accounts()` from lifespan
- Templates: New `settings.html`, `_accounts_tab.html`; update `_navbar.html`, `upload.html`
- Dashboard stats computation will eventually use `starting_balance_cents` + `balance_date` for accurate totals (can be a follow-up)
