## ADDED Requirements

### Requirement: On-demand ML prediction in inbox
The system SHALL allow users to re-run ML predictions on pending transactions from the inbox page using a user-initiated action.

#### Scenario: Retrain button present
- **WHEN** user navigates to the inbox page with pending transactions
- **THEN** a "Retrain" button SHALL be displayed in the toolbar next to the Commit button
- **AND** the button SHALL have a visual distinction from Commit (different color)

#### Scenario: User clicks Retrain
- **WHEN** user clicks the Retrain button
- **THEN** the system SHALL train the ML model on all approved transactions
- **AND** the system SHALL predict fields for all pending transactions
- **AND** the system SHALL update each predicted field where new confidence > current confidence

#### Scenario: Field update preserves user edits
- **GIVEN** a pending transaction with a manually edited field (ml_confidence_* is None)
- **WHEN** Retrain runs and produces a prediction for that field
- **THEN** the user's value SHALL be preserved (not overwritten)
- **Reason**: User always gets final say; manually edited fields have no ML confidence

#### Scenario: Field update improves predictions
- **GIVEN** a pending transaction with an ML-suggested value (ml_confidence_* is non-null)
- **WHEN** Retrain runs and produces a prediction with higher confidence
- **THEN** the transaction SHALL be updated with the new value and confidence

#### Scenario: No training data
- **WHEN** user clicks Retrain and no approved transactions exist
- **THEN** the system SHALL show a toast message indicating no training data is available
- **AND** no predictions SHALL be made

#### Scenario: Retrain returns updated table
- **WHEN** Retrain completes successfully
- **THEN** the inbox table SHALL be refreshed with updated ML suggestions
- **AND** a success toast SHALL be displayed

## MODIFIED Requirements

### Requirement: Prediction runs at import time
_(existing from ml-predictions spec)_

**Updated text:**
Predictions SHALL execute automatically during the CSV import flow, after dedup and insertion. Additionally, predictions MAY execute on-demand via user action in the inbox page.

#### Scenario: Import triggers prediction
_(unchanged)_
- **WHEN** CSV import completes and new pending transactions have been inserted
- **THEN** the system SHALL automatically run the prediction engine on the newly inserted transactions
- **THEN** suggested field values and confidence scores SHALL be written to the database before the user is redirected to the inbox
