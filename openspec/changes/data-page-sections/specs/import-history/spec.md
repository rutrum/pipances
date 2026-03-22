## ADDED Requirements

### Requirement: Import history section in Data page
The Data page SHALL include an Import History section at `/data/imports` displaying a read-only log of all past imports.

#### Scenario: View import history
- **WHEN** user navigates to `/data/imports`
- **THEN** the content pane SHALL display a table of all Import records
- **THEN** the table SHALL show columns: Institution, Filename, Imported At, Row Count
- **THEN** records SHALL be sorted by imported_at descending (most recent first)

#### Scenario: Imported At formatting
- **WHEN** import records are displayed
- **THEN** the imported_at timestamp SHALL be formatted in a human-readable format

#### Scenario: No imports exist
- **WHEN** no import records exist in the database
- **THEN** the section SHALL display a message indicating no imports have been performed yet
