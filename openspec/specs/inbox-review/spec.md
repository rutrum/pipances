## Purpose
Allow users to review, edit, and approve pending transactions before they become part of the approved financial record.

## Requirements

### Requirement: Inbox displays all pending transactions
The inbox page SHALL display all transactions with `status='pending'` in a table.

#### Scenario: Inbox shows pending transactions
- **WHEN** user navigates to /inbox
- **THEN** the page SHALL display a table with columns: date, amount, raw description, description, category, external account, internal account, and approval checkbox
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

#### Scenario: Empty description placeholder
- **WHEN** a transaction has no description set
- **THEN** the description cell SHALL display a badge-styled placeholder indicating it is editable
- **THEN** the placeholder SHALL be visually distinct from actual description text

### Requirement: Inline editing of external account
The user SHALL be able to edit a transaction's external account using the combo box component with search and inline creation.

#### Scenario: Edit external account
- **WHEN** user clicks on a transaction's external account cell in the inbox
- **THEN** a combo box SHALL appear showing matching external accounts as the user types
- **THEN** the user SHALL be able to select an existing account or create a new one
- **WHEN** user selects or creates an account
- **THEN** the system SHALL resolve or create the external account in the database
- **THEN** the system SHALL update the transaction's external_id
- **THEN** the cell SHALL update without full page reload

### Requirement: Inbox displays category column
The inbox table SHALL include a category column for each transaction.

#### Scenario: Category column in inbox
- **WHEN** user navigates to /inbox
- **THEN** the table SHALL include a "Category" column
- **THEN** transactions with a category SHALL display the category name
- **THEN** transactions without a category SHALL display a placeholder indicating it is editable

### Requirement: Inline category editing via combo box
The user SHALL be able to assign or change a transaction's category using the combo box component.

#### Scenario: Assign category to transaction
- **WHEN** user clicks on a transaction's category cell in the inbox
- **THEN** a combo box SHALL appear allowing search and selection of existing categories or creation of a new one
- **WHEN** user selects or creates a category
- **THEN** the transaction's category SHALL be updated
- **THEN** the row SHALL re-render without a full page reload

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
