## Purpose
Allow users to organize transactions into categories for expense tracking and analysis.

## Requirements

### Requirement: Category data model
The system SHALL have a `Category` model with an auto-increment `id` and a unique `name` field.

#### Scenario: Category table exists
- **WHEN** the application starts
- **THEN** a `categories` table SHALL exist with columns `id` (integer PK) and `name` (text, unique, not null)

#### Scenario: Category names are unique
- **WHEN** a category is created with a name that already exists
- **THEN** the system SHALL reject the creation with an error

### Requirement: Transactions have an optional category
Each transaction SHALL have an optional `category_id` foreign key referencing the `categories` table.

#### Scenario: New column on transactions
- **WHEN** the application starts with an existing database
- **THEN** the `transactions` table SHALL have a `category_id` column (nullable integer FK to `categories.id`)
- **THEN** existing transactions SHALL have `category_id = NULL`

### Requirement: Categories management page
The categories section at `/data/categories` SHALL display categories with transaction counts and Explore links.

#### Scenario: View categories list
- **WHEN** user navigates to `/data/categories`
- **THEN** the page SHALL display a table of all categories sorted by name
- **THEN** each row SHALL show the category name, transaction count, and an Explore link

#### Scenario: Transaction count per category
- **WHEN** categories are displayed
- **THEN** each row SHALL show the number of transactions assigned to that category

#### Scenario: Explore link per category
- **WHEN** categories are displayed
- **THEN** each row SHALL include a link that navigates to `/explore?category=<category name>`

#### Scenario: Edit category name inline
- **WHEN** user clicks on a category's name in the table
- **THEN** an inline text input SHALL appear
- **WHEN** user changes the value and confirms (blur or Enter)
- **THEN** the category name SHALL be updated
