## ADDED Requirements

### Requirement: Filter state persists on page refresh
Transaction filter, sort, and pagination state SHALL be reflected in the URL so that refreshing the page restores the same view.

#### Scenario: URL updates on filter change
- **WHEN** user changes any filter, sort, or pagination control on the transactions page
- **THEN** the browser URL SHALL update to include the current filter state as query parameters

#### Scenario: Page load restores filter state
- **WHEN** user loads /transactions with filter query parameters in the URL
- **THEN** the filter controls SHALL be pre-populated with the values from the URL
- **THEN** the displayed transactions SHALL be filtered/sorted/paginated according to those parameters

#### Scenario: Clean URL shows default state
- **WHEN** user navigates to /transactions with no query parameters
- **THEN** all filters SHALL be in their default state
- **THEN** the default date range preset (YTD) SHALL be applied

### Requirement: Amount display format
Amount values in the transactions table SHALL be displayed as plain numbers without a currency symbol, right-aligned for decimal alignment.

#### Scenario: Amount cell formatting
- **WHEN** a transaction is displayed in the transactions table
- **THEN** the amount cell SHALL show only the numeric value (e.g. "12.50" not "$12.50")
- **THEN** the amount cell SHALL be right-aligned
- **THEN** the column header SHALL indicate the currency unit

### Requirement: Custom date range inline layout
The custom date range inputs SHALL appear inline to the right of the preset buttons rather than on a separate row below.

#### Scenario: Custom date range position
- **WHEN** user clicks the Custom preset button
- **THEN** the date inputs and Apply button SHALL appear to the right of the preset button group in the same row
- **THEN** on narrow screens the inputs MAY wrap to a new line
