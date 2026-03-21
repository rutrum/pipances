## MODIFIED Requirements

### Requirement: Inbox displays all pending transactions
The inbox page SHALL display all transactions with `status='pending'` in a two-tier row layout.

#### Scenario: Two-tier row layout
- **WHEN** user navigates to /inbox
- **THEN** each transaction row SHALL display a top tier containing: date, amount, description (editable), category (editable), and external account (editable)
- **THEN** each transaction row SHALL display a bottom tier in muted/smaller text containing: internal account name and raw description
- **THEN** only transactions with `status='pending'` SHALL be shown

#### Scenario: Approved transactions visually distinguished
- **WHEN** a transaction has `marked_for_approval=true`
- **THEN** the row SHALL be visually distinguished from unapproved rows

### Requirement: Mark transactions for approval
Each inbox row SHALL have an approve button that toggles the approval state.

#### Scenario: Approve button disabled state
- **WHEN** a transaction has no description set (null)
- **THEN** the approve button SHALL be rendered in a disabled/ghost style
- **THEN** the button SHALL NOT be clickable

#### Scenario: Approve button ready state
- **WHEN** a transaction has a description set
- **THEN** the approve button SHALL be rendered as a clickable outlined button with text "Approve"

#### Scenario: Approve button approved state
- **WHEN** a transaction has `marked_for_approval=true`
- **THEN** the approve button SHALL be rendered as a success-styled button with text "Approved"
- **THEN** clicking the button SHALL toggle `marked_for_approval` back to false

#### Scenario: Approve single transaction
- **WHEN** user clicks the approve button on a ready-state row
- **THEN** the system SHALL set `marked_for_approval=true` via HTMX PATCH
- **THEN** the row SHALL re-render with the approved button state

#### Scenario: Unapprove single transaction
- **WHEN** user clicks the approve button on an approved-state row
- **THEN** the system SHALL set `marked_for_approval=false` via HTMX PATCH
- **THEN** the row SHALL re-render with the ready button state

### Requirement: Column width stability
Editable cells SHALL maintain consistent width when toggling between view and edit modes.

#### Scenario: Description cell width stable
- **WHEN** user clicks to edit a transaction's description
- **THEN** the cell width SHALL NOT change (the input and the display span occupy the same minimum width)

#### Scenario: Category cell width stable
- **WHEN** user clicks to edit a transaction's category
- **THEN** the cell width SHALL NOT change

#### Scenario: External account cell width stable
- **WHEN** user clicks to edit a transaction's external account
- **THEN** the cell width SHALL NOT change

### Requirement: Empty inbox state
The inbox SHALL display a friendly empty state when there are no pending transactions.

#### Scenario: Empty inbox
- **WHEN** user navigates to /inbox and there are no pending transactions
- **THEN** the page SHALL display a friendly message (e.g. "All cleaned up!")
- **THEN** the page SHALL link to the upload page
