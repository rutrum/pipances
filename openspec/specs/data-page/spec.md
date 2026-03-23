## Purpose
Provide a centralized Data page with sidebar navigation for managing accounts, categories, transactions, external accounts, importers, and import history.

## Requirements

### Requirement: Data page with sidebar layout
The app SHALL have a Data page at `/data` with a DaisyUI sidebar menu on the left and a content pane on the right. All sidebar sections SHALL be active and functional.

#### Scenario: Navigate to Data page
- **WHEN** user navigates to `/data`
- **THEN** the page SHALL redirect to `/data/accounts`

#### Scenario: Sidebar menu structure
- **WHEN** user is on any `/data/*` page
- **THEN** a sidebar menu SHALL be visible with two sections labeled "CONFIGURATION" and "DATA"
- **THEN** the Configuration section SHALL contain active links to: Accounts, Importers
- **THEN** the Data section SHALL contain active links to: Transactions, External Accounts, Categories, Import History
- **THEN** the currently active section SHALL be visually highlighted

#### Scenario: Sidebar navigation swaps content
- **WHEN** user clicks a sidebar menu item
- **THEN** the content pane SHALL update via HTMX without a full page reload
- **THEN** the browser URL SHALL update to reflect the selected section

#### Scenario: Direct navigation to section
- **WHEN** user navigates directly to a section URL (e.g. `/data/transactions`)
- **THEN** the full page SHALL render with the sidebar and the correct section content
- **THEN** the corresponding sidebar item SHALL be highlighted

### Requirement: Data page transactions section
The Data page SHALL include a Transactions section at `/data/transactions` displaying a full transaction table with filters, sorting, and pagination.

#### Scenario: View transactions in Data page
- **WHEN** user navigates to `/data/transactions`
- **THEN** the content pane SHALL display a transaction table with date range selector, filter dropdowns, column sorting, and pagination
- **THEN** the table SHALL show all transactions (approved and pending)
- **THEN** no charts SHALL be displayed

#### Scenario: Transaction table interactions
- **WHEN** user interacts with filters, sorting, or pagination in the Data transactions view
- **THEN** the table SHALL update via HTMX within the content pane
- **THEN** the sidebar SHALL remain unchanged

### Requirement: Data page accounts section
The Data page SHALL include an Accounts section at `/data/accounts` for managing internal accounts with the same editing capabilities as the previous Settings page.

#### Scenario: View accounts in Data page
- **WHEN** user navigates to `/data/accounts`
- **THEN** the content pane SHALL display the internal accounts table with columns: Name, Type, Starting Balance, Balance Date, and Actions
- **THEN** the table SHALL include an inline input row for creating new accounts

#### Scenario: Account CRUD operations
- **WHEN** user creates, edits, or closes/reopens an account in the Data page
- **THEN** the behavior SHALL be identical to the previous Settings accounts page

### Requirement: Data page categories section
The Data page SHALL include a Categories section at `/data/categories` displaying categories with rename capability but no delete or create actions.

#### Scenario: View categories in Data page
- **WHEN** user navigates to `/data/categories`
- **THEN** the content pane SHALL display a table of all categories sorted by name
- **THEN** each row SHALL show the category name (click-to-edit for rename)
- **THEN** no delete button SHALL be displayed
- **THEN** no inline input row for creating categories SHALL be displayed

#### Scenario: Rename category
- **WHEN** user clicks on a category name
- **THEN** an inline text input SHALL appear
- **WHEN** user changes the value and confirms
- **THEN** the category name SHALL be updated
