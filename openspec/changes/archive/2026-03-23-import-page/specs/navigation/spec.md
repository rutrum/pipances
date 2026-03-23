## MODIFIED Requirements

### Requirement: Global navigation bar
The app SHALL have a navigation bar visible on all pages with links to all major sections. The navbar SHALL indicate the currently active page and display icons alongside each link.

#### Scenario: Navigate between pages
- **WHEN** user is on any page
- **THEN** a navigation bar SHALL be visible with links to /import, /inbox, /explore, and /data
- **THEN** each link SHALL display an icon alongside the link text
- **THEN** the link corresponding to the current page SHALL be visually distinguished using DaisyUI's built-in menu active class

#### Scenario: Inbox badge shows pending count
- **WHEN** user is on any page and there are pending transactions in the inbox
- **THEN** the Inbox nav link SHALL display a badge showing the number of pending transactions

#### Scenario: Inbox badge hidden when empty
- **WHEN** user is on any page and there are no pending transactions
- **THEN** the Inbox nav link SHALL NOT display a count badge

#### Scenario: Inbox badge updates after commit
- **WHEN** user commits transactions from the inbox
- **THEN** the inbox badge count SHALL update to reflect the remaining pending transactions without a full page reload
