## MODIFIED Requirements

### Requirement: Inline editing of transaction description
The user SHALL be able to edit a transaction's description directly in the inbox table.

#### Scenario: Edit description
- **WHEN** user clicks on a transaction's description cell in the inbox
- **THEN** the cell SHALL become an editable text input
- **WHEN** user submits the edit (blur or enter)
- **THEN** the system SHALL save the new description to the database via HTMX PATCH
- **THEN** the cell SHALL update to show the new value without full page reload

#### Scenario: Empty description placeholder
- **WHEN** a transaction has no description set
- **THEN** the description cell SHALL display a badge-styled placeholder indicating it is editable
- **THEN** the placeholder SHALL be visually distinct from actual description text
