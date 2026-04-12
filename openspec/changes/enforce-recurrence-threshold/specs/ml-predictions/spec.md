## ADDED Requirements

### Requirement: Minimum recurrence threshold for predictions
The prediction model SHALL filter out recommended values that appear fewer than 2 times in the training data. A value is considered "recommended" if it is produced by the voting stage for a particular field (description, category, or external account).

#### Scenario: Value appears 2+ times in training data
- **GIVEN** a training dataset with 2+ transactions having description="Groceries"
- **WHEN** the model votes and selects "Groceries" as the predicted description
- **THEN** the system SHALL return the prediction (as "Groceries")

#### Scenario: Value appears only once in training data
- **GIVEN** a training dataset with exactly 1 transaction having description="Unique Coffee Shop"
- **WHEN** the model votes and selects "Unique Coffee Shop" as the predicted description
- **THEN** the system SHALL return `None` for that field (no prediction; blank in UI)
- **THEN** the system SHALL treat this the same as low-confidence filtering (not a special case)

#### Scenario: Threshold applied per-field independently
- **GIVEN** training data where category_id=5 appears 1 time but description="Utilities" appears 3 times
- **WHEN** the model votes and determines both category_id=5 and description="Utilities" as winners
- **THEN** the system SHALL return description="Utilities" (meets threshold)
- **THEN** the system SHALL return `None` for category_id (below threshold)
- **THEN** the external account field MAY still return a prediction independently if it meets threshold

#### Scenario: Minimum recurrence (edge case: exactly 2 occurrences)
- **GIVEN** training data with exactly 2 transactions having external_id=42
- **WHEN** the model votes and selects external_id=42
- **THEN** the system SHALL return the prediction (meets the ≥2 threshold)
