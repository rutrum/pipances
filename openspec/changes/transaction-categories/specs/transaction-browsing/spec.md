## ADDED Requirements

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
