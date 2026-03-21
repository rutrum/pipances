## MODIFIED Requirements

### Requirement: CSV upload parses and ingests transactions
The upload form SHALL accept a CSV file, parse it using the selected importer, validate the output, and ingest the transactions as pending into the database. Duplicate transactions from prior imports SHALL be automatically skipped. After upload, the user SHALL see a summary of import results.

#### Scenario: Successful CSV upload
- **WHEN** user selects an importer, an internal account, and a CSV file, then submits the form
- **THEN** the system SHALL parse the CSV using the selected importer's `parse()` function
- **THEN** the system SHALL validate the output against the ImportedTransaction schema
- **THEN** the system SHALL skip rows that match existing transactions by `(date, amount_cents, raw_description)`
- **THEN** the system SHALL ingest remaining transactions as `pending` with `marked_for_approval=false`
- **THEN** the user SHALL be redirected to the inbox page with import result summary

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
