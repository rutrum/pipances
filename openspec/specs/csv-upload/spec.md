## Purpose
Allow users to upload CSV transaction files by selecting an importer and internal account, parsing and ingesting the data into the system.

## Requirements

### Requirement: Upload page presents importer and account selection
The upload page SHALL display a dropdown of available importers (discovered at runtime from `importers/` directory) and a dropdown of internal accounts (from the database). The user MUST select both before uploading.

#### Scenario: Upload page loads with populated dropdowns
- **WHEN** user navigates to /upload
- **THEN** the page SHALL display a dropdown containing all discovered importer names
- **THEN** the page SHALL display a dropdown containing all internal accounts (kind != 'external')
- **THEN** the page SHALL display a file input for CSV selection

### Requirement: CSV upload parses and ingests transactions
The upload form SHALL accept a CSV file, parse it using the selected importer, validate the output, and ingest the transactions as pending into the database.

#### Scenario: Successful CSV upload
- **WHEN** user selects an importer, an internal account, and a CSV file, then submits the form
- **THEN** the system SHALL parse the CSV using the selected importer's `parse()` function
- **THEN** the system SHALL validate the output against the ImportedTransaction schema
- **THEN** the system SHALL ingest all transactions as `pending` with `marked_for_approval=false`
- **THEN** the user SHALL be redirected to the inbox page

#### Scenario: Upload with invalid CSV
- **WHEN** user uploads a CSV that the importer cannot parse or that fails validation
- **THEN** the system SHALL display an error message on the upload page
- **THEN** no transactions SHALL be written to the database

### Requirement: Upload uses HTMX for form submission
The upload form SHALL submit via HTMX without a full page reload.

#### Scenario: HTMX form submission
- **WHEN** user clicks the upload button
- **THEN** the form SHALL submit via HTMX POST
- **THEN** on success, the page SHALL redirect to /inbox
- **THEN** on error, the error message SHALL appear inline without full page reload
