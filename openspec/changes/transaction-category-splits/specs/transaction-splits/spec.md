## ADDED Requirements

### Requirement: User can split a transaction across multiple categories
The system SHALL allow a transaction to be split into multiple category allocations from the transaction edit modal. Each split SHALL have an explicit dollar amount and an optional category. The remaining amount (transaction total minus the sum of all splits) SHALL be implicitly assigned to the transaction's primary category.

#### Scenario: Add a split to a transaction
- **WHEN** user opens the edit modal for a transaction
- **THEN** a Splits section SHALL appear below the Category field
- **WHEN** user enters a valid amount and clicks "Add Split"
- **THEN** the system SHALL create a new split record via POST
- **THEN** the splits section SHALL re-render showing the new split row and updated remainder

#### Scenario: Remainder row appears when splits exist
- **WHEN** one or more splits have been added to a transaction
- **THEN** a read-only remainder row SHALL appear at the top of the splits section
- **THEN** the remainder amount SHALL equal transaction total minus the sum of all split amounts
- **THEN** the remainder row SHALL display the transaction's primary category name as a label

#### Scenario: Live remainder updates as user types
- **WHEN** user types an amount into the new-split amount input
- **THEN** the remainder display SHALL update instantly without a server round-trip

#### Scenario: Remove a split
- **WHEN** user clicks the × button on an existing split row
- **THEN** the system SHALL delete that split record via DELETE
- **THEN** the splits section SHALL re-render with the split removed and remainder updated

#### Scenario: Edit an existing split's amount
- **WHEN** user changes the amount in an existing split row and blurs the field
- **THEN** the system SHALL update the split record via PATCH
- **THEN** the splits section SHALL re-render with updated amounts

#### Scenario: Edit an existing split's category
- **WHEN** user changes the category select on an existing split row
- **THEN** the system SHALL update the split record via PATCH
- **THEN** the splits section SHALL re-render

### Requirement: Split amounts must be valid
The system SHALL enforce that each split amount is greater than zero and that the sum of all splits is strictly less than the transaction total (remainder must remain > 0).

#### Scenario: Add Split button disabled when amount is zero or would eliminate remainder
- **WHEN** the new-split amount input is 0 or empty
- **THEN** the Add Split button SHALL be disabled
- **WHEN** the entered amount equals or exceeds the remaining uncommitted amount
- **THEN** the Add Split button SHALL be disabled

#### Scenario: Server rejects split that would eliminate remainder
- **WHEN** a POST or PATCH request would cause splits to sum to the transaction total or more
- **THEN** the server SHALL return a 422 error
- **THEN** the splits section SHALL display the error message

#### Scenario: Split amount must be positive
- **WHEN** a POST or PATCH request includes an amount_cents of 0 or less
- **THEN** the server SHALL return a 422 error
