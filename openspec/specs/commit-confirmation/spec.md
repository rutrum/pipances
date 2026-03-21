## Purpose
Provide a confirmation dialog before committing approved transactions, summarizing what will be created.

## Requirements

### Requirement: Commit confirmation dialog
When the user clicks "Commit", a confirmation dialog SHALL appear summarizing the pending commit before it is executed.

#### Scenario: Confirmation dialog shows transaction count
- **WHEN** user clicks the "Commit" button and there are approved transactions
- **THEN** a modal dialog SHALL appear showing the number of transactions to be committed

#### Scenario: Confirmation dialog lists new categories
- **WHEN** the confirmation dialog is shown and approved transactions reference categories that are not yet referenced by any approved transaction
- **THEN** the dialog SHALL list those category names under a "New categories" heading

#### Scenario: Confirmation dialog lists new external accounts
- **WHEN** the confirmation dialog is shown and approved transactions reference external accounts that are not yet referenced by any approved transaction
- **THEN** the dialog SHALL list those external account names under a "New external accounts" heading

#### Scenario: No new entities
- **WHEN** the confirmation dialog is shown and all referenced categories and external accounts already exist on approved transactions
- **THEN** the new categories and new external accounts sections SHALL be omitted

#### Scenario: User confirms commit
- **WHEN** user clicks "Confirm" in the dialog
- **THEN** the commit SHALL proceed (same behavior as the current commit flow)
- **THEN** the dialog SHALL close
- **THEN** the inbox table SHALL re-render showing only remaining pending transactions

#### Scenario: User cancels commit
- **WHEN** user clicks "Cancel" in the dialog
- **THEN** no changes SHALL be made
- **THEN** the dialog SHALL close

#### Scenario: No approved transactions
- **WHEN** user clicks "Commit" but no transactions are marked for approval
- **THEN** the system SHALL display a warning toast ("Nothing to commit")
- **THEN** no dialog SHALL appear
