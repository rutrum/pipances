## Purpose
Provide transient feedback to users after key actions via toast notifications.

## Requirements

### Requirement: Toast notification container
The app SHALL have a toast notification area available on all pages for displaying transient feedback messages.

#### Scenario: Toast container present
- **WHEN** user is on any page
- **THEN** a toast container SHALL exist in the DOM, positioned at the bottom-right of the viewport

### Requirement: Toast auto-dismiss
Toast notifications SHALL automatically dismiss after a short duration.

#### Scenario: Toast disappears after timeout
- **WHEN** a toast notification is displayed
- **THEN** the toast SHALL automatically disappear after approximately 4 seconds
- **THEN** the toast SHALL NOT require manual dismissal

### Requirement: Toast on upload success
The system SHALL display a success toast when a CSV upload completes.

#### Scenario: Upload success toast
- **WHEN** user successfully uploads a CSV and is redirected to the inbox
- **THEN** a success toast SHALL appear confirming the upload

### Requirement: Toast on inbox commit
The system SHALL display a toast when inbox transactions are committed.

#### Scenario: Commit success toast
- **WHEN** user clicks Commit and transactions are approved
- **THEN** a success toast SHALL appear confirming the number of transactions committed

#### Scenario: Commit with nothing to commit
- **WHEN** user clicks Commit but no transactions are marked
- **THEN** a warning toast SHALL appear indicating nothing was committed
