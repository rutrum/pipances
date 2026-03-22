## MODIFIED Requirements

### Requirement: List internal accounts
The accounts section SHALL display a table of all active internal accounts with an Explore link per row.

#### Scenario: View active accounts
- **WHEN** user navigates to /data/accounts
- **THEN** the page SHALL display a table with columns: Name, Type, Starting Balance, Balance Date, Actions, and Explore
- **THEN** only active accounts (not closed) SHALL be shown by default

#### Scenario: Explore link per internal account
- **WHEN** internal accounts are displayed
- **THEN** each row SHALL include a link that navigates to `/explore?internal=<account name>`
