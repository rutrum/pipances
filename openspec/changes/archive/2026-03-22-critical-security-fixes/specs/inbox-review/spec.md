## MODIFIED Requirements

### Requirement: Edit endpoints return 404 for invalid IDs
All inline edit endpoints (edit-description, edit-external, edit-category) SHALL return HTTP 404 when the requested transaction ID does not exist, instead of crashing with an unhandled AttributeError.

#### Scenario: Edit description for non-existent transaction
- **WHEN** a request is made to `/transactions/99999/edit-description` and transaction 99999 does not exist
- **THEN** the system SHALL return HTTP 404

### Requirement: Edit widgets use template-rendered HTML
Inline edit endpoints SHALL render HTML via Jinja2 templates (with auto-escaping) instead of Python f-strings. This applies to the description edit input returned by `GET /transactions/{id}/edit-description`.

#### Scenario: Transaction description contains HTML special characters
- **WHEN** a transaction has description `<script>alert(1)</script>`
- **AND** the user clicks to edit the description
- **THEN** the edit input's `value` attribute SHALL contain the HTML-escaped string, not raw HTML

### Requirement: Query parameter validation
The inbox page SHALL validate `page` and `page_size` query parameters. Invalid values (non-numeric, negative, zero) SHALL fall back to defaults (page=1, page_size=25). `page_size` SHALL be clamped to a maximum of 100.

#### Scenario: Non-numeric page parameter
- **WHEN** a request includes `?page=abc`
- **THEN** the system SHALL use page=1 as the default

#### Scenario: Excessive page size
- **WHEN** a request includes `?page_size=999999`
- **THEN** the system SHALL clamp page_size to 100

#### Scenario: Negative page size
- **WHEN** a request includes `?page_size=-1`
- **THEN** the system SHALL use page_size=25 as the default

### Requirement: Date filter validation
The inbox page SHALL validate date filter parameters. Invalid ISO date strings SHALL be silently ignored (treated as no filter).

#### Scenario: Invalid date filter
- **WHEN** a request includes `?date_from=not-a-date`
- **THEN** the system SHALL ignore the date_from filter and show all dates

### Requirement: Upload success toast uses safe JavaScript interpolation
The upload success toast in the inbox page SHALL use `|tojson` filter for all values interpolated into JavaScript string contexts, preventing XSS from account names containing quotes.

#### Scenario: Account name with single quote
- **WHEN** the import summary account name is `O'Brien Savings`
- **THEN** the toast JavaScript SHALL properly escape the name and display it correctly
