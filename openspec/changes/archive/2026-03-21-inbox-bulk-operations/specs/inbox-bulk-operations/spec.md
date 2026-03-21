## ADDED Requirements

### Requirement: Selection checkboxes on inbox rows
Each inbox row SHALL have a checkbox for multi-selection, separate from the approve button.

#### Scenario: Checkbox per row
- **WHEN** user navigates to /inbox with pending transactions
- **THEN** each row SHALL have a checkbox on the left side
- **THEN** checkboxes SHALL be unchecked by default

#### Scenario: Select all checkbox
- **WHEN** user clicks the "select all" checkbox in the table header
- **THEN** all currently visible (filtered) rows SHALL be selected
- **WHEN** user unchecks the "select all" checkbox
- **THEN** all visible rows SHALL be deselected

#### Scenario: Selection is client-side only
- **WHEN** user checks or unchecks row selection checkboxes
- **THEN** no server requests SHALL be made (selection is ephemeral UI state)

### Requirement: Bulk toolbar is always visible
A bulk editing toolbar SHALL be displayed above the table at all times, with controls disabled when no rows are selected.

#### Scenario: Toolbar with no selection
- **WHEN** no row checkboxes are selected
- **THEN** the bulk toolbar SHALL display "0 selected"
- **THEN** all toolbar inputs and buttons SHALL be disabled

#### Scenario: Toolbar with selection
- **WHEN** one or more row checkboxes are selected
- **THEN** the toolbar SHALL display the selection count (e.g. "3 selected")
- **THEN** all toolbar inputs and buttons SHALL be enabled

### Requirement: Bulk edit category, external, and description
The bulk toolbar SHALL allow setting category, external account, and description across all selected rows.

#### Scenario: Bulk set category
- **WHEN** user enters a category in the toolbar's category field and clicks "Apply"
- **THEN** all selected rows SHALL have their category updated to the specified value
- **THEN** if the category does not exist, it SHALL be created

#### Scenario: Bulk set external account
- **WHEN** user enters an external account in the toolbar's external field and clicks "Apply"
- **THEN** all selected rows SHALL have their external account updated to the specified value
- **THEN** if the external account does not exist, it SHALL be created

#### Scenario: Bulk set description
- **WHEN** user enters a description in the toolbar's description field and clicks "Apply"
- **THEN** all selected rows SHALL have their description updated to the specified value

#### Scenario: Partial apply — empty fields are no-ops
- **WHEN** user fills in only the category field and leaves external and description empty, then clicks "Apply"
- **THEN** only the category SHALL be updated on selected rows
- **THEN** existing external account and description values SHALL NOT be changed

#### Scenario: Rows re-render after bulk edit
- **WHEN** a bulk edit is applied
- **THEN** all affected rows SHALL re-render to reflect the updated values
- **THEN** approve button states SHALL update based on the new data

### Requirement: Bulk approve selected transactions
The bulk toolbar SHALL include an "Approve Selected" button.

#### Scenario: Bulk approve
- **WHEN** user clicks "Approve Selected" in the bulk toolbar
- **THEN** all selected rows that meet the approval criteria (description is set) SHALL have `marked_for_approval` set to true
- **THEN** selected rows that do not meet the criteria SHALL be skipped

#### Scenario: Rows re-render after bulk approve
- **WHEN** bulk approve is applied
- **THEN** all affected rows SHALL re-render with updated approve button states
