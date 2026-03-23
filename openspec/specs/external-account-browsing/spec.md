## Purpose
Display external accounts with transaction counts and links to explore filtered views.

## Requirements

### Requirement: External accounts section in Data page
The Data page SHALL include an External Accounts section at `/data/external-accounts` displaying a read-only list of all external accounts.

#### Scenario: View external accounts
- **WHEN** user navigates to `/data/external-accounts`
- **THEN** the content pane SHALL display a table of all accounts with kind "external"
- **THEN** the table SHALL show columns: Name, Transaction Count
- **THEN** accounts SHALL be sorted by name

#### Scenario: Transaction count per external account
- **WHEN** external accounts are displayed
- **THEN** each row SHALL show the number of transactions referencing that external account

#### Scenario: Explore link per external account
- **WHEN** external accounts are displayed
- **THEN** each row SHALL include a link that navigates to `/explore?external=<account name>`

#### Scenario: No external accounts exist
- **WHEN** no external accounts exist in the database
- **THEN** the section SHALL display a message indicating no external accounts have been created from transactions yet
