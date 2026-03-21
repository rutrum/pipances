## ADDED Requirements

### Requirement: Import result summary after upload
After a successful CSV upload, the inbox page SHALL display a summary of the import results.

#### Scenario: Successful import with no duplicates
- **WHEN** user uploads a CSV and all rows are new
- **THEN** the inbox page SHALL display a summary showing the number of transactions imported, the date range of imported transactions, and the internal account name
- **THEN** the duplicate count SHALL be omitted or shown as zero

#### Scenario: Successful import with some duplicates skipped
- **WHEN** user uploads a CSV where some rows match existing transactions
- **THEN** the inbox page SHALL display a summary showing the number of new transactions imported and the number of duplicates skipped
- **THEN** the summary SHALL include the date range and internal account name

#### Scenario: All rows are duplicates
- **WHEN** user uploads a CSV where every row matches an existing transaction
- **THEN** the inbox page SHALL display a summary indicating zero new transactions were imported and the total number of duplicates skipped
