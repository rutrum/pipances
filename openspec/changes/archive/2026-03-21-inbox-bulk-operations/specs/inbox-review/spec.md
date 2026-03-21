## MODIFIED Requirements

### Requirement: Inbox displays all pending transactions
The inbox page SHALL display all transactions with `status='pending'` in a two-tier row layout, with a selection checkbox on each row.

#### Scenario: Two-tier row layout with selection
- **WHEN** user navigates to /inbox
- **THEN** each transaction row SHALL display a selection checkbox on the left
- **THEN** each transaction row SHALL display a top tier containing: date, amount, description (editable), category (editable), and external account (editable)
- **THEN** each transaction row SHALL display a bottom tier in muted/smaller text containing: internal account name and raw description
- **THEN** only transactions with `status='pending'` SHALL be shown
