## MODIFIED Requirements

### Requirement: Data page with sidebar layout
The app SHALL have a Data page at `/data` with a DaisyUI sidebar menu on the left and a content pane on the right. All sidebar sections SHALL be active and functional.

#### Scenario: Sidebar menu structure
- **WHEN** user is on any `/data/*` page
- **THEN** a sidebar menu SHALL be visible with two sections labeled "CONFIGURATION" and "DATA"
- **THEN** the Configuration section SHALL contain active links to: Accounts, Importers
- **THEN** the Data section SHALL contain active links to: Transactions, External Accounts, Categories, Import History
- **THEN** the currently active section SHALL be visually highlighted
