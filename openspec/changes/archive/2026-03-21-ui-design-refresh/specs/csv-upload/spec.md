## MODIFIED Requirements

### Requirement: CSV upload parses and ingests transactions
The upload form SHALL accept a CSV file, parse it using the selected importer, validate the output, and ingest the transactions as pending into the database.

#### Scenario: Successful CSV upload
- **WHEN** user selects an importer, an internal account, and a CSV file, then submits the form
- **THEN** the system SHALL parse the CSV using the selected importer's `parse()` function
- **THEN** the system SHALL validate the output against the ImportedTransaction schema
- **THEN** the system SHALL ingest all transactions as `pending` with `marked_for_approval=false`
- **THEN** the user SHALL be redirected to the inbox page
- **THEN** a toast notification SHALL confirm the upload was successful
