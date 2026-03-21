## ADDED Requirements

### Requirement: Dashboard displays summary statistics
The dashboard page SHALL display summary stat cards for all approved transactions.

#### Scenario: View summary stats
- **WHEN** user navigates to /dashboard
- **THEN** the page SHALL display stat cards showing: Total Income, Total Expenses, Net (income minus expenses), and Net Total (sum of all transactions)
- **THEN** amounts SHALL be formatted as currency

#### Scenario: No approved transactions
- **WHEN** user navigates to /dashboard and no approved transactions exist
- **THEN** the page SHALL display a message indicating no data is available
- **THEN** the page SHALL link to the upload page

### Requirement: Monthly income vs expenses chart
The dashboard SHALL display a side-by-side grouped bar chart of monthly income and expenses.

#### Scenario: View monthly chart
- **WHEN** user navigates to /dashboard with approved transactions
- **THEN** the page SHALL display a bar chart with months on the x-axis
- **THEN** each month SHALL have two bars: one for income (positive amounts) and one for expenses (absolute value of negative amounts)
- **THEN** the chart SHALL be rendered client-side via Vega-Embed from an Altair-generated spec

### Requirement: Top expenses by external account chart
The dashboard SHALL display a horizontal bar chart of the top 10 external accounts by total spend.

#### Scenario: View top expenses chart
- **WHEN** user navigates to /dashboard with approved transactions
- **THEN** the page SHALL display a horizontal bar chart showing the top 10 external accounts ranked by total expense amount
- **THEN** only expense transactions (negative amounts) SHALL be included
- **THEN** amounts SHALL be displayed as positive values (absolute)

### Requirement: Weekly spending trend chart
The dashboard SHALL display a line chart of per-week expense totals.

#### Scenario: View weekly trend
- **WHEN** user navigates to /dashboard with approved transactions
- **THEN** the page SHALL display a line chart with ISO weeks on the x-axis and total expenses per week on the y-axis
- **THEN** only expense transactions (negative amounts) SHALL be included
- **THEN** amounts SHALL be displayed as positive values (absolute)

### Requirement: Charts computed server-side with Polars
All chart data aggregation SHALL be performed server-side using Polars. Chart specifications SHALL be generated using Altair.

#### Scenario: Server-side computation
- **WHEN** the dashboard route is requested
- **THEN** the server SHALL query approved transactions, aggregate data using Polars, and generate Altair Vega-Lite JSON specs
- **THEN** the template SHALL embed the specs for client-side rendering via Vega-Embed
