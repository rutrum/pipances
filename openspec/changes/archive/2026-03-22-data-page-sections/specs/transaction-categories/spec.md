## MODIFIED Requirements

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
