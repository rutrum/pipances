## ADDED Requirements

### Requirement: Dashboard time range filter
The dashboard SHALL display a time range filter above the tab bar that controls the date range for all dashboard content.

#### Scenario: Default time range
- **WHEN** user navigates to /dashboard
- **THEN** the time range SHALL default to "Last 3 Months"

#### Scenario: Preset buttons
- **WHEN** the time range filter is displayed
- **THEN** it SHALL show preset buttons: Last Month, Last 3 Months, YTD, Last Year, All Time
- **THEN** the active preset SHALL be visually highlighted

#### Scenario: Custom date range
- **WHEN** user clicks the "Custom" preset button
- **THEN** date-from and date-to input fields SHALL appear
- **THEN** user SHALL be able to enter custom dates and click "Apply"

#### Scenario: Time range change re-renders active tab
- **WHEN** user selects a time range preset or applies a custom range
- **THEN** the currently active tab's content SHALL be re-fetched with the new time range
- **THEN** the active tab selection SHALL be preserved

### Requirement: Last year preset
The `_compute_date_range` helper SHALL support a `last_year` preset.

#### Scenario: Last year date range
- **WHEN** the `last_year` preset is selected
- **THEN** the date range SHALL cover January 1 through December 31 of the previous calendar year

### Requirement: Dashboard tab navigation
The dashboard SHALL display a tab bar with three tabs: Summary, Categories, and By Account.

#### Scenario: Tab bar display
- **WHEN** user navigates to /dashboard
- **THEN** the page SHALL display tabs labeled "Summary", "Categories", and "By Account"
- **THEN** the "Summary" tab SHALL be active by default

#### Scenario: Switching tabs
- **WHEN** user clicks a tab
- **THEN** the tab content area SHALL be replaced with the selected tab's content via HTMX
- **THEN** the clicked tab SHALL become visually active
- **THEN** the current time range SHALL be preserved and applied to the new tab

### Requirement: Tab content loaded via HTMX partials
Each tab's content SHALL be loaded from a dedicated endpoint returning an HTML partial.

#### Scenario: Summary tab endpoint
- **WHEN** the Summary tab is active
- **THEN** content SHALL be loaded from GET /dashboard/summary

#### Scenario: Categories tab endpoint
- **WHEN** the Categories tab is active
- **THEN** content SHALL be loaded from GET /dashboard/categories

#### Scenario: Accounts tab endpoint
- **WHEN** the By Account tab is active
- **THEN** content SHALL be loaded from GET /dashboard/accounts

### Requirement: Category spending pie chart
The Categories tab SHALL display a pie/donut chart showing spending breakdown by category.

#### Scenario: Pie chart with categories
- **WHEN** the Categories tab is displayed with transactions that have categories
- **THEN** a pie chart SHALL show each category's share of total expenses
- **THEN** only expense transactions (negative amounts) SHALL be included
- **THEN** amounts SHALL be displayed as positive values

#### Scenario: Uncategorized transactions in pie chart
- **WHEN** transactions exist with no category assigned
- **THEN** they SHALL appear as an "Uncategorized" slice in the pie chart

#### Scenario: No expense transactions
- **WHEN** no expense transactions exist in the selected time range
- **THEN** the pie chart SHALL not be displayed

### Requirement: Category drill-down selector
The Categories tab SHALL provide a dropdown to select a specific category for drill-down.

#### Scenario: Category dropdown
- **WHEN** the Categories tab is displayed
- **THEN** a dropdown SHALL list all categories that have transactions in the selected time range
- **THEN** the dropdown SHALL include an "Uncategorized" option if uncategorized transactions exist

#### Scenario: Selecting a category
- **WHEN** user selects a category from the dropdown
- **THEN** the drill-down section below SHALL update via HTMX

### Requirement: Category drill-down content
When a category is selected, the Categories tab SHALL display detailed information for that category.

#### Scenario: Category totals
- **WHEN** a category is selected
- **THEN** the page SHALL display income and expense totals for that category within the time range

#### Scenario: Top transactions table
- **WHEN** a category is selected
- **THEN** the page SHALL display a scrollable table of the top 10 transactions by absolute amount for that category
- **THEN** the table SHALL show date, description, and amount columns

### Requirement: Account selector
The By Account tab SHALL provide a dropdown to select an internal account.

#### Scenario: Account dropdown
- **WHEN** the By Account tab is displayed
- **THEN** a dropdown SHALL list all internal accounts
- **THEN** no account SHALL be selected by default

#### Scenario: Selecting an account
- **WHEN** user selects an account from the dropdown
- **THEN** the drill-down section below SHALL update via HTMX with data for that account

### Requirement: Account balance at end of period
When an account is selected, the tab SHALL display the account balance at the end of the selected time period.

#### Scenario: Balance calculation
- **WHEN** an account is selected and a time range is active
- **THEN** the balance SHALL be computed as starting_balance_cents plus the sum of all transactions for that account with date on or before the end of the time range
- **THEN** the balance SHALL be displayed as formatted currency

#### Scenario: All time range
- **WHEN** the "All Time" preset is selected
- **THEN** the balance SHALL include all transactions for that account

### Requirement: Account income, expenses, and net
When an account is selected, the tab SHALL display income, expenses, and net totals scoped to the selected time range.

#### Scenario: Account period stats
- **WHEN** an account is selected
- **THEN** the page SHALL display income (sum of positive amounts), expenses (sum of negative amounts), and net (income + expenses) for transactions within the time range

### Requirement: Account monthly trend chart
When an account is selected, the tab SHALL display a monthly cumulative balance chart.

#### Scenario: Monthly balance trend
- **WHEN** an account is selected
- **THEN** the page SHALL display a line chart with months on the x-axis and cumulative balance on the y-axis
- **THEN** the cumulative balance SHALL start from starting_balance_cents and accumulate transaction amounts month by month
- **THEN** only months within the selected time range SHALL be displayed

### Requirement: Account top external accounts chart
When an account is selected, the tab SHALL display the top external accounts by transaction volume.

#### Scenario: Top external accounts
- **WHEN** an account is selected
- **THEN** the page SHALL display a horizontal bar chart of the top 10 external accounts by total absolute transaction amount
- **THEN** the chart SHALL be scoped to the selected time range

## MODIFIED Requirements

### Requirement: Dashboard displays summary statistics
The dashboard summary tab SHALL display summary stat cards for approved transactions within the selected time range.

#### Scenario: View summary stats
- **WHEN** user views the Summary tab
- **THEN** the page SHALL display stat cards showing: Total Income, Total Expenses, and Net (income plus expenses)
- **THEN** amounts SHALL be formatted as currency
- **THEN** stats SHALL reflect only transactions within the selected time range

#### Scenario: No approved transactions
- **WHEN** user navigates to /dashboard and no approved transactions exist
- **THEN** the page SHALL display a message indicating no data is available
- **THEN** the page SHALL link to the upload page

## REMOVED Requirements

### Requirement: Net Total stat
**Reason**: Redundant with the Net stat when both are scoped to the same time range.
**Migration**: Users see Income, Expenses, and Net. The Net stat provides the same information.
