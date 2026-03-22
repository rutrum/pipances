## ADDED Requirements

### Requirement: Filter state persists on page refresh
Inbox filter, sort, and pagination state SHALL be reflected in the URL so that refreshing the page restores the same view.

#### Scenario: URL updates on filter change
- **WHEN** user changes any filter, sort, or pagination control in the inbox
- **THEN** the browser URL SHALL update to include the current filter state as query parameters

#### Scenario: Page load restores filter state
- **WHEN** user loads /inbox with filter query parameters in the URL
- **THEN** the filter controls SHALL be pre-populated with the values from the URL
- **THEN** the displayed transactions SHALL be filtered/sorted/paginated according to those parameters

#### Scenario: Clean URL shows default state
- **WHEN** user navigates to /inbox with no query parameters
- **THEN** all filters SHALL be in their default state (no date range, all accounts, all imports)
- **THEN** sort SHALL default to date ascending, page 1, page size 25
