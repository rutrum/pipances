## MODIFIED Requirements

### Requirement: Upload page presents importer and account selection
The upload page SHALL display a dropdown of available importers (discovered at runtime from `importers/` directory) and a dropdown of active internal accounts (from the database). The user MUST select both before uploading.

#### Scenario: Upload page loads with populated dropdowns
- **WHEN** user navigates to /upload
- **THEN** the page SHALL display a dropdown containing all discovered importer names
- **THEN** the page SHALL display a dropdown containing all active internal accounts (kind != 'external', active = true)
- **THEN** the page SHALL display a file input for CSV selection

#### Scenario: Upload page with no internal accounts
- **WHEN** user navigates to /upload and no active internal accounts exist
- **THEN** the page SHALL display a message indicating no accounts are available
- **THEN** the page SHALL link to /settings/accounts to create one
- **THEN** the upload form SHALL NOT be submittable
