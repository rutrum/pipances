## MODIFIED Requirements

### Requirement: Combo box displays filtered results on input
The combo box component SHALL show a dropdown of matching options as the user types. The dropdown SHALL show at most 5 matching entities, plus a "Create new" option at the bottom when applicable. The dropdown SHALL render in the browser's top layer (via the Popover API) so it is NOT clipped by parent container overflow, modal boundaries, or stacking contexts.

#### Scenario: Search with matches
- **WHEN** user types into a combo box input field
- **THEN** the system SHALL query the server for entities matching the input text (case-insensitive partial match)
- **THEN** at most 5 matching results SHALL appear in a dropdown below the input
- **THEN** results SHALL update as the user continues typing (debounced at ~200ms)

#### Scenario: Dropdown not clipped by table overflow
- **WHEN** the combo box dropdown is rendered inside a table or scrollable container
- **THEN** the dropdown SHALL be fully visible and NOT clipped by parent overflow constraints

#### Scenario: Dropdown not clipped by modal
- **WHEN** the combo box is rendered inside a dialog modal
- **THEN** the dropdown SHALL render above the modal in the top layer
- **THEN** the dropdown SHALL be fully visible and interactive

#### Scenario: Dropdown flips above when insufficient space below
- **WHEN** the combo box input is near the bottom of the viewport or modal
- **THEN** the dropdown SHALL open above the input instead of below
- **THEN** the dropdown SHALL remain fully visible within the viewport

#### Scenario: Search with no matches
- **WHEN** user types text that matches no existing entities
- **THEN** the dropdown SHALL show only the "Create new" option

#### Scenario: Empty input
- **WHEN** the combo box input is empty
- **THEN** the dropdown SHALL show up to 5 available entities

### Requirement: Keyboard navigation
The combo box SHALL be fully navigable via keyboard for efficient data entry.

#### Scenario: Arrow key navigation
- **WHEN** the dropdown is visible and user presses the Down arrow key
- **THEN** the highlight SHALL move to the next option in the list
- **WHEN** user presses the Up arrow key
- **THEN** the highlight SHALL move to the previous option in the list
- **THEN** the highlighted option SHALL be visually distinguished from other options

#### Scenario: Wrap-around navigation
- **WHEN** the highlight is on the last option and user presses Down
- **THEN** the highlight SHALL wrap to the first option
- **WHEN** the highlight is on the first option and user presses Up
- **THEN** the highlight SHALL wrap to the last option

#### Scenario: Enter confirms highlighted option
- **WHEN** user presses Enter with an option highlighted
- **THEN** that option SHALL be selected (same as clicking it)
- **THEN** if the highlighted option is "Create new", the entity SHALL be created and assigned

#### Scenario: Enter with no highlight and selectable items present
- **WHEN** user presses Enter with no option highlighted and there are existing entity matches in the dropdown
- **THEN** no action SHALL be taken
- **THEN** the dropdown SHALL remain open

#### Scenario: Enter with no highlight and only Create option present
- **WHEN** user presses Enter with no option highlighted and the only item in the dropdown is the "Create [typed text]" option
- **THEN** the system SHALL create the new entity and assign it to the transaction (same as clicking the Create option)

#### Scenario: Escape cancels
- **WHEN** user presses Escape while the combo box is open
- **THEN** the cell SHALL revert to displaying the previous value
- **THEN** no changes SHALL be saved

### Requirement: Combo box cancels on blur
The combo box SHALL revert to the previous value when the user clicks away without making a selection.

#### Scenario: Blur without selection
- **WHEN** user clicks away from the combo box without selecting an option
- **THEN** the dropdown SHALL close
- **THEN** the cell SHALL revert to displaying the previous value
- **THEN** no changes SHALL be saved

#### Scenario: Click on dropdown item does not trigger blur
- **WHEN** user clicks on a dropdown item
- **THEN** the blur handler SHALL NOT fire before the click registers
- **THEN** the selected item SHALL be applied to the transaction
