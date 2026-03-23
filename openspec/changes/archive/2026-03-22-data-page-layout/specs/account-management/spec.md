## MODIFIED Requirements

### Requirement: Settings page with tab layout
The app SHALL have a Data page at `/data` with a sidebar menu layout. The default section SHALL be "Accounts". `/data` SHALL redirect to `/data/accounts`.

#### Scenario: Navigate to data page
- **WHEN** user navigates to /data
- **THEN** the page SHALL redirect to /data/accounts

#### Scenario: Sidebar layout displayed
- **WHEN** user is on any /data/* page
- **THEN** a sidebar menu SHALL be visible showing available data sections
- **THEN** the active section SHALL be visually distinguished

### Requirement: List internal accounts
The accounts section SHALL display a table of all active internal accounts.

#### Scenario: View active accounts
- **WHEN** user navigates to /data/accounts
- **THEN** the page SHALL display a table with columns: Name, Type, Starting Balance, Balance Date, and Actions
- **THEN** only active accounts (not closed) SHALL be shown by default

#### Scenario: No accounts exist
- **WHEN** user navigates to /data/accounts and no internal accounts exist
- **THEN** the page SHALL display a message indicating no accounts have been created
- **THEN** the create account form SHALL still be available

#### Scenario: Show closed accounts
- **WHEN** user toggles "Show closed" filter
- **THEN** the table SHALL include closed accounts
- **THEN** closed accounts SHALL be visually distinguished from active ones
