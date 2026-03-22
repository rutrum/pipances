## Purpose
Enable filtering of inbox transactions by date range, internal account, and import batch.

## Requirements

### Requirement: Filter bar displayed above inbox table
The inbox page SHALL display a filter bar above the transaction table with controls for narrowing the visible transactions.

#### Scenario: Filter bar visible
- **WHEN** user navigates to /inbox and there are pending transactions
- **THEN** a filter bar SHALL be displayed above the table
- **THEN** the filter bar SHALL contain: date range inputs (from/to), internal account dropdown, and import batch dropdown
- **THEN** a "Clear" button SHALL be displayed to reset all filters

### Requirement: Filter by date range
The user SHALL be able to filter inbox transactions by a date range.

#### Scenario: Filter with both dates
- **WHEN** user sets a "from" date and a "to" date in the filter bar
- **THEN** the table SHALL re-render via HTMX showing only transactions with dates within the specified range (inclusive)

#### Scenario: Filter with only from date
- **WHEN** user sets only a "from" date
- **THEN** the table SHALL show transactions on or after that date

#### Scenario: Filter with only to date
- **WHEN** user sets only a "to" date
- **THEN** the table SHALL show transactions on or before that date

### Requirement: Filter by internal account
The user SHALL be able to filter inbox transactions by internal account.

#### Scenario: Select internal account filter
- **WHEN** user selects an internal account from the dropdown
- **THEN** the table SHALL re-render showing only transactions belonging to that internal account

#### Scenario: Default shows all accounts
- **WHEN** no internal account filter is selected (dropdown shows "All")
- **THEN** all pending transactions SHALL be displayed regardless of internal account

### Requirement: Filter by import batch
The user SHALL be able to filter inbox transactions by import batch.

#### Scenario: Select import batch filter
- **WHEN** user selects an import batch from the dropdown
- **THEN** the table SHALL re-render showing only transactions from that import

#### Scenario: Default shows all imports
- **WHEN** no import batch filter is selected (dropdown shows "All")
- **THEN** all pending transactions SHALL be displayed regardless of import batch

### Requirement: Clear filters
The user SHALL be able to reset all filters at once.

#### Scenario: Clear all filters
- **WHEN** user clicks the "Clear" button in the filter bar
- **THEN** all filter inputs SHALL be reset to their default (empty/all) state
- **THEN** the table SHALL re-render showing all pending transactions

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

### Requirement: Filters persist across commits
Filter state SHALL be preserved when the user commits transactions.

#### Scenario: Filter persists after commit
- **WHEN** user has active filters and commits approved transactions
- **THEN** the filter values SHALL remain set
- **THEN** the table SHALL re-render with the same filters applied to the remaining pending transactions
