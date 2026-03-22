## Purpose
Reusable combo box component for searching, selecting, and inline-creating entities (categories, external accounts) within table cells.

## Requirements

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

#### Scenario: Search with no matches
- **WHEN** user types text that matches no existing entities
- **THEN** the dropdown SHALL show only the "Create new" option

#### Scenario: Empty input
- **WHEN** the combo box input is empty
- **THEN** the dropdown SHALL show up to 5 available entities

### Requirement: Combo box offers inline creation
When the user's input does not exactly match an existing entity, the combo box SHALL offer to create a new one.

#### Scenario: Create option appears
- **WHEN** user types text that does not exactly match any existing entity name
- **THEN** a "Create [typed text]" option SHALL appear in the dropdown

#### Scenario: Create option hidden on exact match
- **WHEN** user types text that exactly matches an existing entity name (case-insensitive)
- **THEN** the "Create" option SHALL NOT appear

#### Scenario: User selects create option
- **WHEN** user clicks the "Create [name]" option
- **THEN** the system SHALL create the new entity and assign it to the transaction in a single operation
- **THEN** the cell SHALL update to show the new value

### Requirement: Combo box selects existing entities
The user SHALL be able to select an existing entity from the dropdown via mouse click or keyboard.

#### Scenario: Select existing option via click
- **WHEN** user clicks an existing entity in the dropdown
- **THEN** the system SHALL assign that entity to the transaction
- **THEN** the cell SHALL update to show the selected value without a full page reload

#### Scenario: Select existing option via keyboard
- **WHEN** user highlights an existing entity using arrow keys and presses Enter
- **THEN** the system SHALL assign that entity to the transaction
- **THEN** the cell SHALL update to show the selected value without a full page reload

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

#### Scenario: Enter with no highlight
- **WHEN** user presses Enter with no option highlighted and text matches an existing entity exactly (case-insensitive)
- **THEN** that entity SHALL be selected
- **WHEN** user presses Enter with no option highlighted and text does not match exactly
- **THEN** no action SHALL be taken (user must explicitly select or create)

#### Scenario: Escape cancels
- **WHEN** user presses Escape while the combo box is open
- **THEN** the cell SHALL revert to displaying the previous value
- **THEN** no changes SHALL be saved

### Requirement: Combo box cancels on blur
The combo box SHALL revert to the previous value when the user clicks away without making a selection.

#### Scenario: Blur without selection
- **WHEN** user clicks away from the combo box without selecting an option
- **THEN** the cell SHALL revert to displaying the previous value
- **THEN** no changes SHALL be saved

### Requirement: Safe hx-vals rendering
The combo box results dropdown SHALL render `hx-vals` attributes using properly JSON-encoded values (via `|tojson` filter or equivalent), preventing JSON injection from entity names containing quotes or special characters.

#### Scenario: Category name with double quote
- **WHEN** a category named `Food "Fast"` appears in combo results
- **THEN** the `hx-vals` attribute SHALL contain valid JSON with the name properly escaped

#### Scenario: External account name with backslash
- **WHEN** an external account named `Store\Outlet` appears in combo results
- **THEN** the `hx-vals` attribute SHALL contain valid JSON with the backslash properly escaped

### Requirement: LIKE wildcard escaping in search
The combo box search endpoint SHALL escape SQL LIKE wildcards (`%` and `_`) in the user's search query before using them in ILIKE patterns.

#### Scenario: Search containing percent sign
- **WHEN** a user types `100%` in the combo search
- **THEN** the system SHALL search for the literal string `100%`, not match all records

#### Scenario: Search containing underscore
- **WHEN** a user types `foo_bar` in the combo search
- **THEN** the system SHALL search for the literal string `foo_bar`, not treat `_` as a single-character wildcard

### Requirement: Combo box is reusable across entity types
The combo box component SHALL work for multiple entity types via a parameterized search endpoint.

#### Scenario: Categories combo box
- **WHEN** combo box is used for the category field
- **THEN** it SHALL search and create categories

#### Scenario: External accounts combo box
- **WHEN** combo box is used for the external account field
- **THEN** it SHALL search and create external accounts
