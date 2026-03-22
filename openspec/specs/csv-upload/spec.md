## Purpose
Allow users to upload CSV transaction files by selecting an importer and internal account, parsing and ingesting the data into the system.

## Requirements

### Requirement: Upload page presents importer and account selection
The upload page SHALL display a dropdown of available importers (discovered at runtime from `importers/` directory) and a dropdown of active internal accounts (from the database). The user MUST select both before uploading.

#### Scenario: Upload page loads with populated dropdowns
- **WHEN** user navigates to /upload
- **THEN** the page SHALL display a dropdown containing all discovered importer names
- **THEN** the page SHALL display a dropdown containing all active internal accounts (kind != 'external', active = true)
- **THEN** the page SHALL display a file input for CSV selection

#### Scenario: Upload page with no internal accounts
- **WHEN** user navigates to /upload and no active internal accounts exist
- **THEN** the page SHALL display a message indicating no accounts are available
- **THEN** the page SHALL link to /settings/accounts to create one
- **THEN** the upload form SHALL NOT be submittable

### Requirement: CSV upload parses and ingests transactions
The upload form SHALL accept a CSV file, parse it using the selected importer, validate the output, and ingest the transactions as pending into the database. Duplicate transactions from prior imports SHALL be automatically skipped. After upload, the user SHALL see a summary of import results.

#### Scenario: Successful CSV upload
- **WHEN** user selects an importer, an internal account, and a CSV file, then submits the form
- **THEN** the system SHALL parse the CSV using the selected importer's `parse()` function
- **THEN** the system SHALL validate the output against the ImportedTransaction schema
- **THEN** the system SHALL skip rows that match existing transactions by `(date, amount_cents, raw_description)`
- **THEN** the system SHALL ingest remaining transactions as `pending` with `marked_for_approval=false`
- **THEN** the user SHALL be redirected to the inbox page with import result summary

#### Scenario: Import triggers ML prediction
- **WHEN** CSV import successfully inserts new pending transactions
- **THEN** the system SHALL run the ML prediction engine on the newly inserted transactions before redirecting to inbox
- **THEN** predicted fields (description, category, external account) SHALL be pre-populated with confidence scores where the model has sufficient confidence
- **THEN** the import result summary SHALL continue to display as before (prediction is transparent to the summary)

#### Scenario: Upload with identical same-file rows
- **WHEN** user uploads a CSV containing multiple rows with the same date, amount, and description
- **THEN** the system SHALL treat all same-file duplicates as distinct real transactions
- **THEN** all rows SHALL be inserted

#### Scenario: Upload overlapping with prior import
- **WHEN** user uploads a CSV where some rows have matching `(date, amount_cents, raw_description)` already in the database
- **THEN** the system SHALL count existing matches per unique key
- **THEN** the system SHALL only insert `max(0, csv_count - db_count)` transactions per unique key

#### Scenario: Re-upload of identical file
- **WHEN** user uploads a CSV where all rows match existing transactions
- **THEN** the system SHALL insert zero new transactions
- **THEN** the user SHALL be redirected to the inbox with a summary showing zero imported and the total duplicates skipped

#### Scenario: Import result summary with no duplicates
- **WHEN** user uploads a CSV and all rows are new
- **THEN** the inbox page SHALL display a summary showing the number of transactions imported, the date range, and the internal account name

#### Scenario: Import result summary with duplicates skipped
- **WHEN** user uploads a CSV where some rows match existing transactions
- **THEN** the inbox page SHALL display a summary showing the number of new transactions imported and the number of duplicates skipped
- **THEN** the summary SHALL include the date range and internal account name

#### Scenario: raw_description is immutable
- **WHEN** a transaction exists in the database
- **THEN** the system SHALL NOT allow modification of the `raw_description` field through any endpoint

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
