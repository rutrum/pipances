## Purpose
Allow users to browse, filter, sort, and paginate through approved transactions.

## Requirements

### Requirement: Transactions page displays approved transactions
The transactions page SHALL display all transactions with `status='approved'` in a read-only paginated table with columns: date, amount, description, external account, and internal account.

#### Scenario: View transactions page
- **WHEN** user navigates to /transactions
- **THEN** the page SHALL display a table of approved transactions
- **THEN** transactions SHALL be sorted by date descending by default
- **THEN** the default date range SHALL be YTD (January 1 of current year to today)

#### Scenario: No approved transactions
- **WHEN** user navigates to /transactions and no approved transactions exist
- **THEN** the page SHALL display a message indicating no transactions found

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

### Requirement: Column sorting
Users SHALL be able to sort the table by clicking column headers.

#### Scenario: Sort by column
- **WHEN** user clicks a column header
- **THEN** the table SHALL sort by that column in ascending order
- **THEN** a sort indicator SHALL appear on the active column header

#### Scenario: Toggle sort direction
- **WHEN** user clicks the same column header again
- **THEN** the sort direction SHALL toggle between ascending and descending
- **THEN** the sort indicator SHALL update to reflect the current direction

#### Scenario: Sort resets page
- **WHEN** user changes the sort column or direction
- **THEN** the page number SHALL reset to 1

### Requirement: Account column filtering
The internal and external account columns SHALL have auto-filter dropdowns for filtering by specific account values.

#### Scenario: Open account filter
- **WHEN** user clicks the filter icon on an account column header
- **THEN** a dropdown SHALL appear listing all account names present in the current result set

#### Scenario: Apply account filter
- **WHEN** user selects an account from the filter dropdown
- **THEN** the table SHALL re-render showing only transactions matching that account
- **THEN** the page number SHALL reset to 1
- **THEN** the column header SHALL indicate an active filter

#### Scenario: Clear account filter
- **WHEN** user clears the account filter (selects "All" or removes selection)
- **THEN** the table SHALL re-render without that account filter applied

### Requirement: Pagination
The transactions table SHALL be paginated with navigation controls.

#### Scenario: Navigate between pages
- **WHEN** user clicks Next or Previous
- **THEN** the table SHALL display the corresponding page of results
- **THEN** all active filters and sort settings SHALL be preserved

#### Scenario: Page indicator
- **WHEN** user views the pagination controls
- **THEN** the current page number and total page count SHALL be displayed

#### Scenario: Configure page size
- **WHEN** user selects a different page size (25, 50, or 100)
- **THEN** the table SHALL re-render with the new page size
- **THEN** the page number SHALL reset to 1

### Requirement: Filter transactions by category
The transactions page SHALL allow filtering by category.

#### Scenario: Category filter dropdown
- **WHEN** user navigates to /transactions
- **THEN** a category filter dropdown SHALL be available alongside the existing account filters
- **THEN** the dropdown SHALL list all categories that have at least one approved transaction

#### Scenario: Apply category filter
- **WHEN** user selects a category from the filter dropdown
- **THEN** only transactions with that category SHALL be displayed
- **THEN** the filter SHALL work in combination with existing date range and account filters

#### Scenario: Filter uncategorized transactions
- **WHEN** user selects an "Uncategorized" option from the category filter
- **THEN** only transactions with no category assigned SHALL be displayed

### Requirement: Category displayed in transaction table
The transactions table SHALL show the category for each transaction.

#### Scenario: Category column in transaction table
- **WHEN** user views the transactions table
- **THEN** a "Category" column SHALL display the category name for categorized transactions
- **THEN** uncategorized transactions SHALL show a dash or empty cell

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

### Requirement: Custom date range inline layout
The custom date range inputs SHALL appear inline to the right of the preset buttons rather than on a separate row below.

#### Scenario: Custom date range position
- **WHEN** user clicks the Custom preset button
- **THEN** the date inputs and Apply button SHALL appear to the right of the preset button group in the same row
- **THEN** on narrow screens the inputs MAY wrap to a new line

### Requirement: Server-side rendering via HTMX
All filtering, sorting, and pagination interactions SHALL be handled server-side with HTMX partial updates.

#### Scenario: HTMX partial update
- **WHEN** user interacts with any table control (filter, sort, paginate)
- **THEN** the system SHALL send an HTMX request with all current state
- **THEN** the server SHALL return updated table body and pagination controls
- **THEN** the page SHALL NOT perform a full reload
