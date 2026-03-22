## MODIFIED Requirements

### Requirement: Categories management page
The system SHALL provide a categories section at `/data/categories` for viewing and renaming categories. Category creation and deletion SHALL NOT be available from this page.

#### Scenario: View categories list
- **WHEN** user navigates to `/data/categories`
- **THEN** the page SHALL display a table of all categories sorted by name
- **THEN** each row SHALL show the category name

#### Scenario: Edit category name inline
- **WHEN** user clicks on a category's name in the table
- **THEN** an inline text input SHALL appear
- **WHEN** user changes the value and confirms (blur or Enter)
- **THEN** the category name SHALL be updated

## REMOVED Requirements

### Requirement: Category deletion cascades to NULL
**Reason**: Category delete functionality removed. Categories are managed implicitly through transaction editing.
**Migration**: Categories can no longer be deleted from the UI. Orphaned categories remain in the database.
