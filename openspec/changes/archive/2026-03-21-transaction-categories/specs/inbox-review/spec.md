## ADDED Requirements

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

## MODIFIED Requirements

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

### Requirement: Inbox displays all pending transactions
The inbox page SHALL display all transactions with `status='pending'` in a table.

#### Scenario: Inbox shows pending transactions
- **WHEN** user navigates to /inbox
- **THEN** the page SHALL display a table with columns: date, amount, raw description, description, category, external account, internal account, and approval checkbox
- **THEN** only transactions with `status='pending'` SHALL be shown
- **THEN** transactions marked for approval SHALL be visually distinguished from unmarked ones
