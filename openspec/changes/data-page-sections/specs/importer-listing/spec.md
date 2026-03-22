## ADDED Requirements

### Requirement: Importers section in Data page
The Data page SHALL include an Importers section at `/data/importers` displaying a read-only list of discovered importer files.

#### Scenario: View importers
- **WHEN** user navigates to `/data/importers`
- **THEN** the content pane SHALL display a table of all Python importer files found in the `importers/` directory
- **THEN** the table SHALL show columns: Importer Name, Filename
- **THEN** the importer name SHALL be read from each module's `IMPORTER_NAME` attribute

#### Scenario: Missing IMPORTER_NAME attribute
- **WHEN** an importer file does not define `IMPORTER_NAME`
- **THEN** the filename SHALL be used as a fallback for the name column

#### Scenario: No importers exist
- **WHEN** the `importers/` directory contains no Python files
- **THEN** the section SHALL display a message indicating no importers have been defined
