## MODIFIED Requirements

### Requirement: Combo box displays filtered results on input
The combo box component SHALL show a dropdown of matching options as the user types. The dropdown SHALL show at most 5 matching entities, plus a "Create new" option at the bottom when applicable. The dropdown SHALL NOT be clipped by parent container overflow.

#### Scenario: Search with matches
- **WHEN** user types into a combo box input field
- **THEN** the system SHALL query the server for entities matching the input text (case-insensitive partial match)
- **THEN** at most 5 matching results SHALL appear in a dropdown below the input
- **THEN** results SHALL update as the user continues typing (debounced at ~200ms)

#### Scenario: Dropdown not clipped by table overflow
- **WHEN** the combo box dropdown is rendered inside a table or scrollable container
- **THEN** the dropdown SHALL be fully visible and NOT clipped by parent overflow constraints
