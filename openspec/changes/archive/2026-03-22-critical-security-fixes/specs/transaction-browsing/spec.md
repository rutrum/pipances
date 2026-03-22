## MODIFIED Requirements

### Requirement: Query parameter validation
The transactions page SHALL validate `page` and `page_size` query parameters. Invalid values SHALL fall back to defaults (page=1, page_size=25). `page_size` SHALL be clamped to a maximum of 100.

#### Scenario: Non-numeric page parameter
- **WHEN** a request to `/transactions` includes `?page=abc`
- **THEN** the system SHALL use page=1 as the default

#### Scenario: Excessive page size
- **WHEN** a request includes `?page_size=999999`
- **THEN** the system SHALL clamp page_size to 100

### Requirement: Date filter validation
The transactions page SHALL validate date parameters from presets and custom ranges. Invalid ISO date strings SHALL be silently ignored.

#### Scenario: Invalid custom date range
- **WHEN** a request includes `?preset=custom&date_from=bad&date_to=bad`
- **THEN** the system SHALL fall back to the default date range (YTD)
