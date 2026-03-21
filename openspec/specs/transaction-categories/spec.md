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

#### Scenario: Category deletion cascades to NULL
- **WHEN** a category is deleted that is assigned to one or more transactions
- **THEN** the affected transactions SHALL have their `category_id` set to NULL

### Requirement: Categories management page
The system SHALL provide a management page at `/settings/categories` for creating, editing, and deleting categories.

#### Scenario: View categories list
- **WHEN** user navigates to `/settings/categories`
- **THEN** the page SHALL display a table of all categories sorted by name
- **THEN** each row SHALL show the category name and a delete action

#### Scenario: Create category
- **WHEN** user enters a name in the inline input row and submits
- **THEN** the system SHALL create the category
- **THEN** the new category SHALL appear in the table without a full page reload

#### Scenario: Reject duplicate category name
- **WHEN** user submits a category name that already exists
- **THEN** the system SHALL display an error message
- **THEN** no category SHALL be created

#### Scenario: Edit category name inline
- **WHEN** user clicks on a category's name in the table
- **THEN** an inline text input SHALL appear
- **WHEN** user changes the value and confirms (blur or Enter)
- **THEN** the category name SHALL be updated

#### Scenario: Delete category
- **WHEN** user clicks the delete action on a category
- **THEN** the category SHALL be deleted
- **THEN** any transactions referencing that category SHALL have their `category_id` set to NULL
- **THEN** the row SHALL be removed from the table without a full page reload
