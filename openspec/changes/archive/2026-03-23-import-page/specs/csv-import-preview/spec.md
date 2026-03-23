## ADDED Requirements

### Requirement: CSV file auto-detection tries all importers
When a user uploads a CSV file, the system SHALL try every discovered importer's `parse()` function against the file and report which ones succeeded and which failed.

#### Scenario: Single importer matches
- **WHEN** user uploads a CSV file and exactly one importer successfully parses it
- **THEN** that importer SHALL be auto-selected
- **THEN** the preview SHALL display which importer was matched

#### Scenario: Multiple importers match
- **WHEN** user uploads a CSV file and multiple importers successfully parse it
- **THEN** the preview SHALL display all matching importers
- **THEN** the user SHALL select which importer to use via a dropdown
- **THEN** the preview table SHALL update to reflect the selected importer's output

#### Scenario: No importers match
- **WHEN** user uploads a CSV file and no importers can parse it
- **THEN** the system SHALL display an error message indicating no importers could parse the file
- **THEN** no preview table SHALL be shown

### Requirement: Preview displays parsed transactions before commit
After a CSV file is uploaded and an importer is selected, the system SHALL display a table of parsed transactions for user review before any data is written to the database.

#### Scenario: Preview table shows parsed rows
- **WHEN** a file is successfully parsed by an importer
- **THEN** the system SHALL display a table showing all parsed rows with columns: Date, Amount, Description
- **THEN** no data SHALL be written to the database at this stage

#### Scenario: Preview table highlights duplicate rows
- **WHEN** a preview table is displayed and the user has selected an account
- **THEN** rows that match existing transactions in the database (by date, amount_cents, raw_description, internal_account) SHALL be displayed with strikethrough styling
- **THEN** a summary SHALL show the count of new rows and duplicate rows

#### Scenario: Duplicate highlighting requires account selection
- **WHEN** a preview table is displayed but no account is selected
- **THEN** the table SHALL show all parsed rows without duplicate highlighting
- **THEN** selecting an account SHALL trigger an HTMX request to re-render the preview with duplicate annotations

### Requirement: Server-side temp file storage for preview-to-commit flow
The uploaded CSV file SHALL be stored server-side in a temp file between the preview and commit steps, identified by a UUID token.

#### Scenario: File stored on preview
- **WHEN** user uploads a CSV for preview
- **THEN** the system SHALL save the raw file bytes to a temp file named `import_{uuid}.csv`
- **THEN** the preview response SHALL include the UUID token as a hidden form input

#### Scenario: File read on commit
- **WHEN** user confirms the import by clicking "Add to Inbox"
- **THEN** the system SHALL read the CSV from the temp file using the provided token
- **THEN** the system SHALL parse it with the selected importer and ingest via the standard pipeline
- **THEN** the temp file SHALL be deleted after successful commit

#### Scenario: Stale temp files are cleaned up
- **WHEN** a new file is uploaded for preview
- **THEN** the system SHALL delete any temp files older than 1 hour

#### Scenario: Invalid or missing token on commit
- **WHEN** user submits a commit with an invalid or expired token
- **THEN** the system SHALL return an error indicating the preview has expired
- **THEN** the user SHALL be prompted to re-upload the file

### Requirement: Account selection and commit on preview page
The preview step SHALL include an account dropdown and an "Add to Inbox" button to finalize the import.

#### Scenario: Commit from preview
- **WHEN** user selects an account and clicks "Add to Inbox" on the preview page
- **THEN** the system SHALL POST to `/import/commit` with the token, selected importer, and account
- **THEN** on success, the user SHALL be redirected to the inbox with an import summary toast
- **THEN** on error, an error message SHALL be displayed inline
