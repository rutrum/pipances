# Proposal: Data Page Layout (Phase 2 of 3)

## Problem

The Settings page currently only manages internal accounts and categories. There's no place to view external accounts, import history, or browse transactions outside of the Explore page. The app needs a central "data management" area that distinguishes between user-configured entities and data derived from transactions.

## Solution

Replace the `/settings` page with a `/data` page featuring a DaisyUI sidebar menu on the left and a content pane on the right. The sidebar has two sections:

- **Configuration**: Internal Accounts (editable, as today), Importers (read-only listing)
- **Data**: Transactions (full table), External Accounts, Categories, Import History

Clicking a sidebar menu item swaps the content pane via HTMX. Each section has its own URL (`/data/accounts`, `/data/transactions`, etc.) for deep linking.

The navbar changes "Settings" to "Data".

## Scope

- New `/data` layout template with DaisyUI sidebar menu
- Migrate internal accounts management from `/settings/accounts` to `/data/accounts` (same functionality)
- Migrate transaction table from the now-deleted `/transactions` to `/data/transactions`
- Remove category delete button and `DELETE /categories/{id}` endpoint
- Keep category rename (click-to-edit name)
- Update all internal links and redirects
- Delete old `settings.html`, `settings_accounts.html`, `settings_categories.html` templates
- Navbar: rename "Settings" to "Data"

## Capabilities

### New Capabilities
- `data-page`: Sidebar-driven data management page with configuration and data sections

### Modified Capabilities
- `account-management`: Moves from /settings/accounts to /data/accounts
- `navigation`: "Settings" becomes "Data"

### Removed Capabilities
- Category delete functionality

## Impact

- New: `data.html` (layout with sidebar), updated route URLs
- Modified: `_navbar.html`, `routes/settings.py` (rename routes), `main.py`
- Deleted: `settings.html`, `settings_accounts.html`, `settings_categories.html`, `DELETE /categories/{id}` endpoint
- Reused: `_account_row.html`, `_account_input_row.html`, `_category_row.html` (minus delete button), transaction table partials
