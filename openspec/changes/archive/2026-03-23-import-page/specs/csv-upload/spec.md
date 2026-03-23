## MODIFIED Requirements

### Requirement: Upload page presents importer and account selection
The import page SHALL auto-detect compatible importers after file upload rather than requiring manual importer selection upfront. Account selection moves to the preview step.

#### Scenario: Import page loads with file upload
- **WHEN** user navigates to `/import`
- **THEN** the page SHALL display a file input for CSV selection and a "Scan File" button
- **THEN** the page SHALL NOT display importer or account dropdowns on the initial view

#### Scenario: Import page with no internal accounts
- **WHEN** user navigates to `/import` and no active internal accounts exist
- **THEN** the page SHALL display a message indicating no accounts are available
- **THEN** the page SHALL link to the Data page to create one
- **THEN** the upload form SHALL NOT be submittable

### Requirement: CSV upload parses and ingests transactions
The CSV import SHALL use a two-step flow: first preview parsed transactions with duplicate highlighting, then commit on user confirmation. Duplicate transactions from prior imports SHALL be highlighted in the preview and skipped on commit.

#### Scenario: Successful CSV upload
- **WHEN** user uploads a CSV, reviews the preview, selects an account, and clicks "Add to Inbox"
- **THEN** the system SHALL parse the CSV using the selected importer's `parse()` function
- **THEN** the system SHALL validate the output against the ImportedTransaction schema
- **THEN** the system SHALL convert decimal dollar amounts to integer cents using `int(round(amount * 100))`
- **THEN** the system SHALL skip rows that match existing transactions by `(date, amount_cents, raw_description, internal_account)`
- **THEN** the system SHALL ingest remaining transactions as `pending` with `marked_for_approval=false`
- **THEN** the user SHALL be redirected to the inbox page with import result summary

#### Scenario: Import triggers ML prediction
- **WHEN** CSV import successfully inserts new pending transactions
- **THEN** the system SHALL run the ML prediction engine on the newly inserted transactions before redirecting to inbox
- **THEN** predicted fields (description, category, external account) SHALL be pre-populated with confidence scores where the model has sufficient confidence

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

#### Scenario: raw_description is immutable
- **WHEN** a transaction exists in the database
- **THEN** the system SHALL NOT allow modification of the `raw_description` field through any endpoint

#### Scenario: Upload with invalid CSV
- **WHEN** user uploads a CSV that no importer can parse
- **THEN** the system SHALL display an error message indicating no importers could handle the file
- **THEN** no transactions SHALL be written to the database

### Requirement: Upload uses HTMX for form submission
The import flow SHALL use HTMX for all interactions: file scanning, preview rendering, account selection updates, and final commit.

#### Scenario: HTMX scan submission
- **WHEN** user clicks the "Scan File" button
- **THEN** the form SHALL submit via HTMX POST to `/import/preview`
- **THEN** the preview area SHALL be replaced with the scan results and preview table

#### Scenario: HTMX commit submission
- **WHEN** user clicks "Add to Inbox" on the preview
- **THEN** the form SHALL submit via HTMX POST to `/import/commit`
- **THEN** on success, the page SHALL redirect to `/inbox`
- **THEN** on error, the error message SHALL appear inline without full page reload

## REMOVED Requirements

### Requirement: Import result summary with no duplicates
**Reason**: Import result summaries are now shown via the existing toast notification system on redirect to inbox. The behavior is unchanged but the requirement is redundant with the toast-notifications spec.
**Migration**: No migration needed; toast behavior is preserved in the "Successful CSV upload" scenario.

### Requirement: Import result summary with duplicates skipped
**Reason**: Same as above — covered by toast notifications on inbox redirect.
**Migration**: No migration needed.
