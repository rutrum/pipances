## ADDED Requirements

### Requirement: Inbox displays all pending transactions
The inbox page SHALL display all transactions with `status='pending'` in a table.

#### Scenario: Inbox shows pending transactions
- **WHEN** user navigates to /inbox
- **THEN** the page SHALL display a table with columns: date, amount, raw description, description, external account, and approval checkbox
- **THEN** only transactions with `status='pending'` SHALL be shown
- **THEN** transactions marked for approval SHALL be visually distinguished from unmarked ones

#### Scenario: Empty inbox
- **WHEN** user navigates to /inbox and there are no pending transactions
- **THEN** the page SHALL display a message indicating the inbox is empty
- **THEN** the page SHALL link to the upload page

### Requirement: Inline editing of transaction description
The user SHALL be able to edit a transaction's description directly in the inbox table.

#### Scenario: Edit description
- **WHEN** user clicks on a transaction's description cell in the inbox
- **THEN** the cell SHALL become an editable text input
- **WHEN** user submits the edit (blur or enter)
- **THEN** the system SHALL save the new description to the database via HTMX PATCH
- **THEN** the cell SHALL update to show the new value without full page reload

### Requirement: Inline editing of external account
The user SHALL be able to edit a transaction's external account as a free text field.

#### Scenario: Edit external account
- **WHEN** user clicks on a transaction's external account cell in the inbox
- **THEN** the cell SHALL become an editable text input
- **WHEN** user submits the edit
- **THEN** the system SHALL resolve or create the new external account in the database
- **THEN** the system SHALL update the transaction's external_id
- **THEN** the cell SHALL update without full page reload

### Requirement: Mark transactions for approval
Each inbox row SHALL have an approval checkbox that persists to the database.

#### Scenario: Mark single transaction for approval
- **WHEN** user toggles the approval checkbox on a transaction row
- **THEN** the system SHALL update `marked_for_approval` in the database via HTMX
- **THEN** the row SHALL be visually distinguished as marked

#### Scenario: Unmark transaction
- **WHEN** user unchecks the approval checkbox on a marked transaction
- **THEN** the system SHALL set `marked_for_approval=false` in the database
- **THEN** the row styling SHALL revert to unmarked

### Requirement: Commit approved transactions
The inbox page SHALL have a "Commit" button that approves all marked transactions.

#### Scenario: Commit marked transactions
- **WHEN** user clicks the "Commit" button
- **THEN** all transactions with `marked_for_approval=true` SHALL have their status set to `approved`
- **THEN** `marked_for_approval` SHALL be reset to `false` on committed transactions
- **THEN** orphaned external accounts (kind='external' with no transaction references) SHALL be pruned
- **THEN** the inbox table SHALL re-render showing only remaining pending transactions

#### Scenario: Commit with no marked transactions
- **WHEN** user clicks "Commit" but no transactions are marked for approval
- **THEN** the system SHALL display a message indicating nothing to commit
- **THEN** no database changes SHALL occur

### Requirement: Navigation between pages
The app SHALL have a navigation bar visible on all pages with links to Upload and Inbox.

#### Scenario: Navigate between pages
- **WHEN** user is on any page
- **THEN** a navigation bar SHALL be visible with links to /upload and /inbox
