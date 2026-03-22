## MODIFIED Requirements

### Requirement: Edit endpoints return 404 for invalid IDs
All inline edit endpoints (edit-name, edit-type, edit-balance, edit-balance-date) SHALL return HTTP 404 when the requested account ID does not exist, instead of crashing with an unhandled AttributeError.

#### Scenario: Edit name for non-existent account
- **WHEN** a request is made to `/accounts/99999/edit-name` and account 99999 does not exist
- **THEN** the system SHALL return HTTP 404

### Requirement: Edit widgets use template-rendered HTML
Inline edit endpoints SHALL render HTML via Jinja2 templates (with auto-escaping) instead of Python f-strings. This applies to edit-name, edit-type, edit-balance, and edit-balance-date endpoints.

#### Scenario: Account name contains HTML special characters
- **WHEN** an account has name `Savings <Main>`
- **AND** the user clicks to edit the name
- **THEN** the edit input's `value` attribute SHALL contain the HTML-escaped string

### Requirement: Category edit endpoint returns 404 for invalid IDs
The `GET /categories/{id}/edit-name` endpoint SHALL return HTTP 404 when the category does not exist.

#### Scenario: Edit name for non-existent category
- **WHEN** a request is made to `/categories/99999/edit-name` and category 99999 does not exist
- **THEN** the system SHALL return HTTP 404
