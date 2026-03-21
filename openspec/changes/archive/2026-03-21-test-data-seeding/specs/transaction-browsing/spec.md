## MODIFIED Requirements

### Requirement: Date range filtering with presets
The transactions page SHALL provide a date range widget with preset buttons and a custom date range option.

#### Scenario: Select a date preset
- **WHEN** user clicks a preset button (All, YTD, Last Month, Last 3 Months)
- **THEN** the table SHALL immediately re-render showing only transactions within that date range (or all transactions for "All")
- **THEN** the active preset SHALL be visually highlighted
- **THEN** the page number SHALL reset to 1

#### Scenario: Select "All" preset
- **WHEN** user clicks the "All" preset button
- **THEN** the table SHALL display all approved transactions regardless of date
- **THEN** no date range bounds SHALL be applied

#### Scenario: Select custom date range
- **WHEN** user clicks the Custom button
- **THEN** two date input fields (from, to) SHALL appear
- **WHEN** user sets dates and clicks Apply
- **THEN** the table SHALL re-render showing only transactions within the custom range
- **THEN** the page number SHALL reset to 1
