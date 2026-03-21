## MODIFIED Requirements

### Requirement: Settings page with tab layout
The app SHALL have a settings page at `/settings` with a tab navigation bar. The default tab SHALL be "Accounts". `/settings` SHALL redirect to `/settings/accounts`.

#### Scenario: Navigate to settings
- **WHEN** user navigates to /settings
- **THEN** the page SHALL redirect to /settings/accounts

#### Scenario: Tab layout displayed
- **WHEN** user is on any /settings/* page
- **THEN** a tab bar SHALL be visible showing available settings sections including "Accounts" and "Categories"
- **THEN** the active tab SHALL be visually distinguished
