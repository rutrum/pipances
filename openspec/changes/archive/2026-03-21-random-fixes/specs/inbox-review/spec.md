## ADDED Requirements

### Requirement: Inbox pagination
The inbox table SHALL be paginated with navigation controls below the table.

#### Scenario: Default page size
- **WHEN** user navigates to /inbox
- **THEN** the inbox SHALL display the first 25 pending transactions
- **THEN** pagination controls SHALL appear below the table

#### Scenario: Navigate between pages
- **WHEN** user clicks Next or Previous in inbox pagination
- **THEN** the table SHALL display the corresponding page of results
- **THEN** all active filters and sort settings SHALL be preserved

#### Scenario: Page indicator
- **WHEN** user views the inbox pagination controls
- **THEN** the current page number and total page count SHALL be displayed

#### Scenario: Configure page size
- **WHEN** user selects a different page size (25, 50, or 100)
- **THEN** the table SHALL re-render with the new page size
- **THEN** the page number SHALL reset to 1

### Requirement: Inbox column sorting
Users SHALL be able to sort the inbox table by clicking column headers for Date, Amount, and Description.

#### Scenario: Sort by column
- **WHEN** user clicks a sortable column header in the inbox
- **THEN** the table SHALL sort by that column in ascending order
- **THEN** a sort indicator SHALL appear on the active column header

#### Scenario: Toggle sort direction
- **WHEN** user clicks the same column header again
- **THEN** the sort direction SHALL toggle between ascending and descending

#### Scenario: Default sort order
- **WHEN** user navigates to /inbox without sort parameters
- **THEN** the table SHALL be sorted by date ascending

#### Scenario: Sort resets page
- **WHEN** user changes the sort column or direction
- **THEN** the page number SHALL reset to 1

### Requirement: ML prediction indicator as blue dot
Fields with ML-predicted values SHALL display a small blue dot indicator that does not affect content layout.

#### Scenario: ML-predicted field shows dot
- **WHEN** a transaction field (description, category, or external account) has an ML confidence value set
- **THEN** a small blue dot SHALL appear next to the field value
- **THEN** the dot SHALL NOT push the field content or affect vertical alignment of the cell
- **THEN** hovering over the dot or field SHALL show a tooltip with the confidence percentage

#### Scenario: User-edited field hides dot
- **WHEN** a user edits a field that previously had an ML prediction
- **THEN** the blue dot SHALL no longer appear after the row re-renders

### Requirement: Amount display format
Amount values in the inbox table SHALL be displayed as plain numbers without a currency symbol, right-aligned for decimal alignment.

#### Scenario: Amount cell formatting
- **WHEN** a transaction is displayed in the inbox table
- **THEN** the amount cell SHALL show only the numeric value (e.g. "12.50" not "$12.50")
- **THEN** the amount cell SHALL be right-aligned
- **THEN** the column header SHALL indicate the currency unit

## MODIFIED Requirements

### Requirement: Inline editing of transaction description
The user SHALL be able to edit a transaction's description directly in the inbox table.

#### Scenario: Edit description
- **WHEN** user clicks on a transaction's description cell in the inbox
- **THEN** the cell SHALL become an editable text input with ghost styling (borderless until focused)
- **WHEN** user submits the edit (blur or enter)
- **THEN** the system SHALL save the new description to the database via HTMX PATCH
- **THEN** the cell SHALL update to show the new value without full page reload

#### Scenario: Empty description placeholder
- **WHEN** a transaction has no description set
- **THEN** the description cell SHALL display italic grey text reading "click to edit"
- **THEN** the placeholder SHALL be visually distinct from actual description text
- **THEN** the placeholder SHALL have no extra padding and align with populated field values

### Requirement: Inline editing of external account
The user SHALL be able to edit a transaction's external account using the combo box component with search and inline creation.

#### Scenario: Edit external account
- **WHEN** user clicks on a transaction's external account cell in the inbox
- **THEN** a combo box SHALL appear with ghost-styled input (borderless until focused) showing matching external accounts as the user types
- **THEN** the user SHALL be able to select an existing account or create a new one
- **WHEN** user selects or creates an account
- **THEN** the system SHALL resolve or create the external account in the database
- **THEN** the system SHALL update the transaction's external_id
- **THEN** the cell SHALL update without full page reload

### Requirement: Inline category editing via combo box
The user SHALL be able to assign or change a transaction's category using the combo box component.

#### Scenario: Assign category to transaction
- **WHEN** user clicks on a transaction's category cell in the inbox
- **THEN** a combo box SHALL appear with ghost-styled input (borderless until focused) allowing search and selection of existing categories or creation of a new one
- **WHEN** user selects or creates a category
- **THEN** the transaction's category SHALL be updated
- **THEN** the row SHALL re-render without a full page reload

### Requirement: Inbox displays category column
The inbox table SHALL include a category column for each transaction.

#### Scenario: Category column in inbox
- **WHEN** user navigates to /inbox
- **THEN** the table SHALL include a "Category" column
- **THEN** transactions with a category SHALL display the category name
- **THEN** transactions without a category SHALL display italic grey text reading "click to edit"
