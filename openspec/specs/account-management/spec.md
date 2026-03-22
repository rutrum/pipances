## Purpose
Allow users to manage internal accounts (create, edit, close/reopen) through a settings page, including setting starting balances.

## Requirements

### Requirement: Settings page with tab layout
The app SHALL have a settings page at `/settings` with a tab navigation bar. The default tab SHALL be "Accounts". `/settings` SHALL redirect to `/settings/accounts`.

#### Scenario: Navigate to settings
- **WHEN** user navigates to /settings
- **THEN** the page SHALL redirect to /settings/accounts

#### Scenario: Tab layout displayed
- **WHEN** user is on any /settings/* page
- **THEN** a tab bar SHALL be visible showing available settings sections including "Accounts" and "Categories"
- **THEN** the active tab SHALL be visually distinguished

### Requirement: List internal accounts
The accounts tab SHALL display a table of all active internal accounts.

#### Scenario: View active accounts
- **WHEN** user navigates to /settings/accounts
- **THEN** the page SHALL display a table with columns: Name, Type, Starting Balance, Balance Date, and Actions
- **THEN** only active accounts (not closed) SHALL be shown by default

#### Scenario: No accounts exist
- **WHEN** user navigates to /settings/accounts and no internal accounts exist
- **THEN** the page SHALL display a message indicating no accounts have been created
- **THEN** the create account form SHALL still be available

#### Scenario: Show closed accounts
- **WHEN** user toggles "Show closed" filter
- **THEN** the table SHALL include closed accounts
- **THEN** closed accounts SHALL be visually distinguished from active ones

### Requirement: Create internal account via inline table row
The accounts table SHALL include an input row at the bottom for creating new accounts. The input row SHALL be visually distinct from data rows (e.g. subtle background or dashed border).

#### Scenario: Create account with required fields
- **WHEN** user fills in the name and type fields in the inline input row and clicks the Add button
- **THEN** the system SHALL create a new account with the given name and type
- **THEN** the account SHALL have `active=true`, `starting_balance_cents=0`, and `balance_date=null` by default
- **THEN** the new account row SHALL appear in the table via HTMX without a full page reload
- **THEN** the inline input row SHALL reset to empty for the next entry

#### Scenario: Create account with starting balance
- **WHEN** user fills in name, type, starting balance, and balance date in the inline input row, then clicks Add
- **THEN** the system SHALL create the account with the specified starting balance and date

#### Scenario: Reject duplicate account name
- **WHEN** user submits a name that already exists
- **THEN** the system SHALL display an error message
- **THEN** no account SHALL be created

#### Scenario: Reject "external" as account type
- **WHEN** user submits "external" as the account type
- **THEN** the system SHALL display an error message
- **THEN** no account SHALL be created

### Requirement: Edit internal account inline
Account fields SHALL be editable inline, consistent with the inbox editing pattern.

#### Scenario: Edit account name
- **WHEN** user clicks on an account's name field
- **THEN** an inline text input SHALL appear
- **WHEN** user changes the value and confirms (blur or Enter)
- **THEN** the account name SHALL be updated
- **THEN** the row SHALL re-render without a full page reload

#### Scenario: Edit account type
- **WHEN** user clicks on an account's type field
- **THEN** an inline text input SHALL appear
- **WHEN** user changes the value and confirms
- **THEN** the account type SHALL be updated, subject to the "external" validation rule

#### Scenario: Edit starting balance and date
- **WHEN** user clicks on the starting balance or balance date field
- **THEN** an inline input SHALL appear (number for balance, date picker for date)
- **WHEN** user changes the value and confirms
- **THEN** the field SHALL be updated

### Requirement: Edit endpoints return 404 for invalid IDs
All inline edit endpoints (edit-name, edit-type, edit-balance, edit-balance-date) SHALL return HTTP 404 when the requested account ID does not exist, instead of crashing with an unhandled error.

#### Scenario: Edit name for non-existent account
- **WHEN** a request is made to `/accounts/99999/edit-name` and account 99999 does not exist
- **THEN** the system SHALL return HTTP 404

### Requirement: Edit widgets use template-rendered HTML
Inline edit endpoints SHALL render HTML via Jinja2 templates (with auto-escaping) instead of Python f-strings.

#### Scenario: Account name contains HTML special characters
- **WHEN** an account has name `Savings <Main>`
- **AND** the user clicks to edit the name
- **THEN** the edit input's `value` attribute SHALL contain the HTML-escaped string

### Requirement: Category edit endpoint returns 404 for invalid IDs
The `GET /categories/{id}/edit-name` endpoint SHALL return HTTP 404 when the category does not exist.

#### Scenario: Edit name for non-existent category
- **WHEN** a request is made to `/categories/99999/edit-name` and category 99999 does not exist
- **THEN** the system SHALL return HTTP 404

### Requirement: Close and reopen accounts
Users SHALL be able to close (archive) and reopen internal accounts.

#### Scenario: Close an active account
- **WHEN** user clicks the close action on an active account
- **THEN** the account SHALL be marked as inactive (`active=false`)
- **THEN** the account SHALL disappear from the default view (unless "Show closed" is on)

#### Scenario: Reopen a closed account
- **WHEN** user clicks the reopen action on a closed account (visible when "Show closed" is on)
- **THEN** the account SHALL be marked as active (`active=true`)

### Requirement: Closed accounts excluded from upload
Closed accounts SHALL NOT appear in the upload page's internal account dropdown.

#### Scenario: Upload page filters closed accounts
- **WHEN** user navigates to /upload
- **THEN** the internal account dropdown SHALL only include active accounts
