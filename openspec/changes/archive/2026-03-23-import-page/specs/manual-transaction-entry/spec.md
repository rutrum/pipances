## ADDED Requirements

### Requirement: Manual entry tab provides a multi-row spreadsheet form
The Import page SHALL include a "Manual Entry" tab with a spreadsheet-style form for hand-entering transactions.

#### Scenario: Manual entry form layout
- **WHEN** user selects the "Manual Entry" tab on the Import page
- **THEN** the page SHALL display an account dropdown at the top
- **THEN** the page SHALL display a table with columns: Date, Amount, Description, and a remove button
- **THEN** the table SHALL have at least one empty row by default
- **THEN** the page SHALL have an "Add Row" button to append more empty rows
- **THEN** the page SHALL have an "Add to Inbox" button to submit all rows

#### Scenario: Adding and removing rows
- **WHEN** user clicks "Add Row"
- **THEN** a new empty row SHALL be appended to the table
- **WHEN** user clicks the remove button on a row
- **THEN** that row SHALL be removed from the table

### Requirement: Manual entry creates Import and Transaction records
Submitting the manual entry form SHALL create an Import record and Transaction records following the standard pipeline.

#### Scenario: Successful manual entry submission
- **WHEN** user fills in one or more rows with date, amount, and description, selects an account, and clicks "Add to Inbox"
- **THEN** the system SHALL create an Import record with `institution="Manual"` and `filename=None`
- **THEN** the system SHALL create a Transaction for each non-empty row with `raw_description` and `description` both set to the user-provided description
- **THEN** transactions SHALL be created with `status="pending"` and `marked_for_approval=false`
- **THEN** the user SHALL be redirected to the inbox with an import summary toast

#### Scenario: Empty rows are skipped
- **WHEN** user submits the manual entry form and some rows are completely empty
- **THEN** the system SHALL silently skip empty rows
- **THEN** only rows with all required fields (date, amount, description) SHALL be processed

#### Scenario: No valid rows submitted
- **WHEN** user submits the manual entry form but all rows are empty
- **THEN** the system SHALL display an error message indicating no transactions were provided

#### Scenario: Manual entry with no accounts available
- **WHEN** user navigates to the manual entry tab and no active internal accounts exist
- **THEN** the page SHALL display a message indicating no accounts are available
- **THEN** the page SHALL link to the Data page to create one

### Requirement: Manual entries receive ML predictions
Manual transaction entries SHALL flow through the same ML prediction pipeline as CSV imports.

#### Scenario: ML predictions run on manual entries
- **WHEN** manual entries are successfully committed
- **THEN** the system SHALL run the ML prediction engine on the newly inserted transactions
- **THEN** predicted fields (description, category, external account) SHALL be pre-populated where the model has sufficient confidence
