# inbox-dropdown-improvement Specification

## Purpose
TBD - created by archiving change fix-inbox-dropdowns. Update Purpose after archive.
## Requirements
### Requirement: Inbox row displays read-only state for approved transactions
When a transaction has been marked as approved in the inbox, the text fields SHALL be read-only but the approval button remains functional to allow un-approving.

#### Scenario: Approved transaction renders as read-only
- **WHEN** a transaction has `marked_for_approval == True`
- **THEN** the description, category, and external account cells SHALL NOT trigger the edit UI when clicked
- **THEN** the approval button SHALL show "Approved" in a success state but pressing it SHALL toggle to un-approve the transaction

### Requirement: Combo box displays up to 50 results
The combo box component SHALL show a dropdown of matching options as the user types. The dropdown SHALL show at most 50 matching entities, plus a "Create new" option at the bottom when applicable. The dropdown SHALL NOT be clipped by parent container overflow.

#### Scenario: Search with matches shows up to 50 results
- **WHEN** user types into a combo box input field
- **THEN** at most 50 matching results SHALL appear in a dropdown below the input

#### Scenario: Empty input shows up to 50 results
- **WHEN** the combo box input is empty
- **THEN** the dropdown SHALL show up to 50 available entities

### Requirement: Description field supports autocomplete dropdown
The description field in the inbox SHALL support the same combo box autocomplete pattern as category and external account fields.

#### Scenario: Description dropdown shows suggestions on focus
- **WHEN** user clicks on the description cell (when not already editing)
- **THEN** the cell SHALL render an input field with autocomplete
- **THEN** the dropdown SHALL show up to 50 existing descriptions as suggestions

#### Scenario: Description dropdown shows matches on input
- **WHEN** user types text into the description input
- **THEN** the system SHALL query for descriptions matching the input (case-insensitive partial match)
- **THEN** at most 50 matching results SHALL appear in the dropdown

#### Scenario: Description dropdown offers creation
- **WHEN** user types text that does not exactly match any existing description
- **THEN** a "Create [typed text]" option SHALL appear in the dropdown

### Requirement: Account dropdown shows grouped accounts by type
The account dropdown in import pages SHALL group accounts by their type (internal vs external) for easier selection.

#### Scenario: Import preview shows grouped accounts
- **WHEN** user navigates to import preview
- **THEN** the account dropdown SHALL show internal accounts grouped under a "Internal Accounts" header
- **THEN** the dropdown SHALL show external accounts grouped under an "External Accounts" header

