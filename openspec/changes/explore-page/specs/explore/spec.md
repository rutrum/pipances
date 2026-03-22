## ADDED Requirements

### Requirement: Explore page displays unified filtered view
The app SHALL have an Explore page at `/explore` that combines summary statistics, charts, and a paginated transaction table in a single view. All content SHALL respond to the same set of filters and date range.

#### Scenario: Navigate to Explore
- **WHEN** user navigates to `/explore`
- **THEN** the page SHALL display a date range selector, filter dropdowns, summary stats, charts, and a transaction table
- **THEN** the default date range SHALL be YTD

#### Scenario: No transactions match filters
- **WHEN** no transactions match the current filters and date range
- **THEN** the page SHALL display an informational message instead of charts and an empty table

### Requirement: Explore date range filtering
The Explore page SHALL provide a date range selector with preset buttons and a custom date range option.

#### Scenario: Preset buttons
- **WHEN** the Explore page is displayed
- **THEN** it SHALL show preset buttons: YTD, Last Month, Last 3 Months, Last Year, All
- **THEN** the active preset SHALL be visually highlighted

#### Scenario: Custom date range
- **WHEN** user clicks the Custom preset button
- **THEN** date-from and date-to input fields SHALL appear
- **WHEN** user sets dates and clicks Apply
- **THEN** all content (stats, charts, table) SHALL re-render for the custom range

#### Scenario: Date range change updates all content
- **WHEN** user selects a date range preset or applies a custom range
- **THEN** summary stats, charts, and the transaction table SHALL all update to reflect the new date range

### Requirement: Explore filter dropdowns
The Explore page SHALL provide dropdown filters for internal account, external account, and category.

#### Scenario: Filter dropdowns populated
- **WHEN** the Explore page is displayed
- **THEN** an internal account dropdown SHALL list all non-external accounts
- **THEN** an external account dropdown SHALL list all external accounts
- **THEN** a category dropdown SHALL list all categories with transactions, plus an "Uncategorized" option

#### Scenario: Apply a filter
- **WHEN** user selects a value from any filter dropdown
- **THEN** stats, charts, and the transaction table SHALL re-render showing only transactions matching all active filters

#### Scenario: Compound filters
- **WHEN** user selects values from multiple filter dropdowns
- **THEN** all filters SHALL be applied simultaneously (AND logic)

#### Scenario: Clear filters
- **WHEN** user resets a filter dropdown to its default empty value
- **THEN** that filter SHALL be removed and content SHALL update accordingly

### Requirement: Explore summary statistics
The Explore page SHALL display summary stat cards computed from all transactions matching the current filters and date range.

#### Scenario: View summary stats
- **WHEN** the Explore page has matching transactions
- **THEN** stat cards SHALL display: Total Income, Total Expenses, Net (income plus expenses), and Transaction Count
- **THEN** amounts SHALL be formatted as currency

### Requirement: Explore charts
The Explore page SHALL display three charts computed from all transactions matching the current filters and date range.

#### Scenario: Charts displayed
- **WHEN** the Explore page has matching transactions
- **THEN** the page SHALL display: a monthly income/expenses bar chart (full width), a top expenses by external account bar chart, and a weekly spending trend line chart
- **THEN** charts SHALL be rendered client-side via Vega-Embed from Altair-generated specs

#### Scenario: Charts reflect filters
- **WHEN** filters are applied (e.g. category=Groceries)
- **THEN** all three charts SHALL show data only for transactions matching those filters

### Requirement: Explore transaction table
The Explore page SHALL include a paginated, sortable transaction table below the charts.

#### Scenario: Table displays filtered transactions
- **WHEN** the Explore page has matching transactions
- **THEN** a table SHALL display transactions matching the current filters and date range
- **THEN** the table SHALL show columns: Date, Description, Amount, Internal Account, External Account, Category
- **THEN** the table SHALL be paginated with the same controls as the existing transaction table

#### Scenario: Sort by column
- **WHEN** user clicks a sortable column header
- **THEN** the table SHALL sort by that column, toggling direction on repeated clicks

#### Scenario: Table shows all statuses
- **WHEN** the Explore page is displayed
- **THEN** the transaction table SHALL include both approved and pending transactions

### Requirement: Explore page deep linking
The Explore page filter and date range state SHALL be reflected in the URL for deep linking.

#### Scenario: URL contains filter state
- **WHEN** user applies filters or changes the date range
- **THEN** the URL SHALL update to include query parameters (e.g. `?internal=Chase&category=Groceries&preset=ytd`)

#### Scenario: Load from URL
- **WHEN** user navigates to `/explore?external=Walmart&preset=last_3_months`
- **THEN** the filter dropdowns SHALL be pre-populated with those values
- **THEN** the content SHALL be filtered accordingly

### Requirement: Explore HTMX partial updates
All filter, date range, sorting, and pagination interactions SHALL use HTMX partial updates without full page reloads.

#### Scenario: HTMX partial response
- **WHEN** an HTMX request is made to `/explore` with filter/sort/page parameters
- **THEN** the server SHALL return an HTML partial containing updated stats, charts, and table body
- **THEN** the date range buttons SHALL update via OOB swap to reflect the active preset
