## Context

Internal accounts are currently hardcoded as `SEED_ACCOUNTS` in `db.py` and auto-inserted on app startup. The Account model has three columns: `id`, `name`, `kind`. External accounts are auto-created during CSV ingest. There is no way to manage accounts through the UI, set starting balances, or retire old accounts.

The upload page already queries internal accounts for its dropdown, so moving account creation to the UI has a direct downstream effect there.

## Goals / Non-Goals

**Goals:**
- Users can create, edit, and close internal accounts via a settings page
- Each account can have a starting balance with an as-of date
- Closed accounts are hidden from active use but preserved for historical data
- Settings page uses a tab layout to accommodate future settings sections
- Upload page gracefully handles the zero-accounts state

**Non-Goals:**
- Managing external accounts (handled in inbox)
- Using starting balances in dashboard computations (follow-up change)
- Categories tab or other settings tabs (future)
- Deleting accounts (close/archive only)

## Decisions

### Settings page with tab layout
The settings page lives at `/settings` (redirects to `/settings/accounts`). Each tab is a sub-route (`/settings/accounts`, future `/settings/categories`, etc.). The tab bar is part of a `settings.html` base template that each tab extends.

**Alternative considered:** A single flat accounts page at `/accounts`. Rejected because we know more settings tabs are coming and this avoids navbar clutter.

### Account model changes
Add three columns to Account:
- `starting_balance_cents` (Integer, default 0) — the known balance at a point in time
- `balance_date` (Date, nullable) — the date the starting balance is known for. When null, starting balance is not used in calculations.
- `active` (Boolean, default True) — False means closed/archived

These are nullable-safe additions that won't break existing rows (default values handle migration).

### Kind validation
The `kind` field stays as a freeform string, but the create/edit endpoints validate that the value is not `"external"`. This is enforced at the route level, not the model level, since external accounts are legitimately created by the ingest system.

**Alternative considered:** An enum for kind. Rejected — keeping it freeform lets users use whatever labels make sense to them (checking, savings, credit, brokerage, etc.).

### Inline editing with HTMX
Consistent with the inbox page pattern: click a field to edit, blur/enter to save. Each account row is a partial (`_account_row.html`) that gets swapped on update. This keeps the UX consistent across the app.

### Closing accounts
A close/reopen toggle on each row. Closed accounts:
- Don't appear in the upload page's account dropdown
- Don't appear in the accounts list by default (filtered out)
- Can be shown via a "Show closed" toggle
- Cannot be deleted (FK constraints from transactions)

### Remove seed accounts
`SEED_ACCOUNTS` and `seed_accounts()` are deleted. The lifespan handler no longer calls `seed_accounts()`. On first run, the accounts list is empty and the upload page shows a message directing users to create accounts in settings.

## Risks / Trade-offs

- [Existing databases have accounts without the new columns] → SQLAlchemy's `create_all` will add new columns with defaults. Existing accounts get `starting_balance_cents=0`, `balance_date=null`, `active=true`. No data migration needed.
- [Removing seed accounts breaks existing workflows] → Only affects fresh installs. Existing databases already have the accounts created. The upload page's empty-state message mitigates the UX gap.
- [Freeform kind field allows typos] → Acceptable for now. A future enhancement could suggest common kinds via a datalist element.
