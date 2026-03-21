## Purpose
Allow users to review, edit, and approve pending transactions before they become part of the approved financial record.

## Requirements

### Requirement: Inbox displays all pending transactions
The inbox page SHALL display all transactions with `status='pending'` in a two-tier row layout, with a selection checkbox on each row.

#### Scenario: Two-tier row layout with selection
- **WHEN** user navigates to /inbox
- **THEN** each transaction row SHALL display a selection checkbox on the left
- **THEN** each transaction row SHALL display a top tier containing: date, amount, description (editable), category (editable), and external account (editable)
- **THEN** each transaction row SHALL display a bottom tier in muted/smaller text containing: internal account name and raw description
- **THEN** only transactions with `status='pending'` SHALL be shown

#### Scenario: Approved transactions visually distinguished
- **WHEN** a transaction has `marked_for_approval=true`
- **THEN** the row SHALL be visually distinguished from unapproved rows

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
Each inbox row SHALL have an approve button that toggles the approval state.

#### Scenario: Approve button disabled state
- **WHEN** a transaction has no description set (null)
- **THEN** the approve button SHALL be rendered in a disabled/ghost style
- **THEN** the button SHALL NOT be clickable

#### Scenario: Approve button ready state
- **WHEN** a transaction has a description set
- **THEN** the approve button SHALL be rendered as a clickable outlined button with text "Approve"

#### Scenario: Approve button approved state
- **WHEN** a transaction has `marked_for_approval=true`
- **THEN** the approve button SHALL be rendered as a success-styled button with text "Approved"
- **THEN** clicking the button SHALL toggle `marked_for_approval` back to false

#### Scenario: Approve single transaction
- **WHEN** user clicks the approve button on a ready-state row
- **THEN** the system SHALL set `marked_for_approval=true` via HTMX PATCH
- **THEN** the row SHALL re-render with the approved button state

#### Scenario: Unapprove single transaction
- **WHEN** user clicks the approve button on an approved-state row
- **THEN** the system SHALL set `marked_for_approval=false` via HTMX PATCH
- **THEN** the row SHALL re-render with the ready button state

### Requirement: Column width stability
Editable cells SHALL maintain consistent width when toggling between view and edit modes.

#### Scenario: Description cell width stable
- **WHEN** user clicks to edit a transaction's description
- **THEN** the cell width SHALL NOT change (the input and the display span occupy the same minimum width)

#### Scenario: Category cell width stable
- **WHEN** user clicks to edit a transaction's category
- **THEN** the cell width SHALL NOT change

#### Scenario: External account cell width stable
- **WHEN** user clicks to edit a transaction's external account
- **THEN** the cell width SHALL NOT change

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

### Requirement: Empty inbox state
The inbox SHALL display a friendly empty state when there are no pending transactions.

#### Scenario: Empty inbox
- **WHEN** user navigates to /inbox and there are no pending transactions
- **THEN** the page SHALL display a friendly message (e.g. "All cleaned up!")
- **THEN** the page SHALL link to the upload page
