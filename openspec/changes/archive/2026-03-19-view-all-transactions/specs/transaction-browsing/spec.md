## ADDED Requirements

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
- **WHEN** user clicks a preset button (YTD, Last Month, Last 3 Months)
- **THEN** the table SHALL immediately re-render showing only transactions within that date range
- **THEN** the active preset SHALL be visually highlighted
- **THEN** the page number SHALL reset to 1

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

### Requirement: Server-side rendering via HTMX
All filtering, sorting, and pagination interactions SHALL be handled server-side with HTMX partial updates.

#### Scenario: HTMX partial update
- **WHEN** user interacts with any table control (filter, sort, paginate)
- **THEN** the system SHALL send an HTMX request with all current state
- **THEN** the server SHALL return updated table body and pagination controls
- **THEN** the page SHALL NOT perform a full reload
