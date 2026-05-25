## MODIFIED Requirements

### Requirement: Inline editing of transaction description
The user SHALL be able to edit a transaction's description via the transaction edit modal.

#### Scenario: Edit description via modal
- **WHEN** user clicks the Edit button on an inbox row
- **THEN** a modal SHALL open containing a description text input pre-filled with the current value
- **WHEN** user edits the description and the input loses focus (blur)
- **THEN** the system SHALL save the new description via HTMX PATCH without closing the modal
- **THEN** the row in the inbox table SHALL update via OOB swap

#### Scenario: Editing an ML-suggested description clears confidence
- **WHEN** user edits a transaction's description that was ML-suggested
- **THEN** `ml_confidence_description` SHALL be set to `None`
- **THEN** the ML visual indicator SHALL disappear from the description field

### Requirement: Inline editing of external account
The user SHALL be able to edit a transaction's external account via the transaction edit modal using a combo box with search and inline creation.

#### Scenario: Edit external account via modal
- **WHEN** user opens the transaction edit modal
- **THEN** an external account combo box SHALL be present pre-filled with the current value
- **WHEN** user selects or creates an account and the field loses focus
- **THEN** the system SHALL update the transaction's external_id via HTMX PATCH
- **THEN** the row in the inbox table SHALL update via OOB swap

#### Scenario: Editing an ML-suggested external account clears confidence
- **WHEN** user edits a transaction's external account that was ML-suggested
- **THEN** `ml_confidence_external` SHALL be set to `None`
- **THEN** the ML visual indicator SHALL disappear from the external account field

### Requirement: Inline category editing via combo box
The user SHALL be able to assign or change a transaction's category via the transaction edit modal using the combo box component.

#### Scenario: Assign category via modal
- **WHEN** user opens the transaction edit modal
- **THEN** a category combo box SHALL be present pre-filled with the current value
- **WHEN** user selects or creates a category
- **THEN** the transaction's category SHALL be updated via HTMX PATCH
- **THEN** the row in the inbox table SHALL update via OOB swap

#### Scenario: Editing an ML-suggested category clears confidence
- **WHEN** user edits a transaction's category that was ML-suggested
- **THEN** `ml_confidence_category` SHALL be set to `None`
- **THEN** the ML visual indicator SHALL disappear from the category field

## ADDED Requirements

### Requirement: Edit modal includes a Splits section
The transaction edit modal SHALL include a Splits section below the Category field, allowing users to split the transaction across multiple categories.

#### Scenario: Splits section always visible in modal
- **WHEN** user opens the transaction edit modal
- **THEN** a Splits section SHALL be visible below the Category field
- **THEN** an "Add Split" button SHALL be present

#### Scenario: Splits section shows existing splits on modal open
- **WHEN** a transaction has existing splits and user opens the edit modal
- **THEN** the splits section SHALL render the remainder row and all existing split rows
