## MODIFIED Requirements

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
