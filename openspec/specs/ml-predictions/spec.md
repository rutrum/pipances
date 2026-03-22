## Purpose
Predict description, category, and external account for newly imported transactions based on patterns in previously approved transactions, reducing manual data entry while preserving human review.

## Requirements

### Requirement: Prediction engine uses approved transactions as training data
The system SHALL use all approved transactions as labeled training data for predicting fields on new pending transactions.

#### Scenario: Prediction with approved transaction history
- **WHEN** new transactions are imported and approved transactions exist in the database
- **THEN** the system SHALL fit a model on approved transactions and predict fields for the new transactions

#### Scenario: Prediction with no approved transactions
- **WHEN** new transactions are imported and zero approved transactions exist in the database
- **THEN** the system SHALL skip prediction entirely
- **THEN** all fields on new transactions SHALL remain at their default values (no description, no category, auto-created external)

#### Scenario: Prediction with few approved transactions
- **WHEN** new transactions are imported and few approved transactions exist
- **THEN** the system SHALL still attempt prediction
- **THEN** predictions with low confidence SHALL be omitted (fields left blank)

### Requirement: Model uses text and contextual features
The prediction model SHALL use `raw_description` as the primary feature, supplemented by amount, date patterns, internal account, and importer institution.

#### Scenario: Feature extraction
- **GIVEN** a transaction with raw_description, amount_cents, date, internal_id, and an import with institution
- **THEN** the model SHALL extract: TF-IDF character n-grams from raw_description, scaled amount_cents, cyclically-encoded day-of-week and day-of-month, and one-hot-encoded internal_id and institution

### Requirement: Two-stage confidence gating
The system SHALL use two thresholds to filter low-quality predictions.

#### Scenario: Neighbors below similarity floor
- **WHEN** all kNN neighbors for a transaction have cosine similarity below the similarity floor
- **THEN** no suggestion SHALL be made for any field on that transaction

#### Scenario: Neighbors pass floor but disagree
- **WHEN** kNN neighbors pass the similarity floor but no single value achieves agreement above the confidence threshold for a given field
- **THEN** no suggestion SHALL be made for that field
- **THEN** other fields with sufficient agreement MAY still receive suggestions

#### Scenario: High-confidence prediction
- **WHEN** kNN neighbors pass the similarity floor and a value achieves agreement above the confidence threshold for a field
- **THEN** the field SHALL be set to the winning value
- **THEN** the corresponding confidence column SHALL be set to the agreement score

### Requirement: Per-field confidence tracking
Each predictable field SHALL have a corresponding nullable float column storing the ML confidence score.

#### Scenario: ML-suggested field
- **WHEN** the model suggests a value for a field
- **THEN** the field SHALL be populated with the suggested value
- **THEN** the corresponding `ml_confidence_*` column SHALL be set to the confidence score (0.0–1.0)

#### Scenario: Field not suggested
- **WHEN** the model does not suggest a value for a field (insufficient confidence or no training data)
- **THEN** the corresponding `ml_confidence_*` column SHALL be `None`

#### Scenario: User edits an ML-suggested field
- **WHEN** user modifies a field that has a non-null `ml_confidence_*` value
- **THEN** the `ml_confidence_*` column SHALL be set to `None`
- **THEN** the field value SHALL be the user's input

### Requirement: Prediction runs at import time
Predictions SHALL execute automatically during the CSV import flow, after dedup and insertion.

#### Scenario: Import triggers prediction
- **WHEN** CSV import completes and new pending transactions have been inserted
- **THEN** the system SHALL automatically run the prediction engine on the newly inserted transactions
- **THEN** suggested field values and confidence scores SHALL be written to the database before the user is redirected to the inbox

### Requirement: Predicted fields use existing entities only
ML predictions for category and external account SHALL only reference entities that already exist in the database.

#### Scenario: Predicted external account
- **WHEN** the model suggests an external account for a transaction
- **THEN** the suggested account SHALL be an existing account in the database
- **THEN** the transaction's `external_id` SHALL be updated to the suggested account's ID

#### Scenario: Predicted category
- **WHEN** the model suggests a category for a transaction
- **THEN** the suggested category SHALL be an existing category in the database
- **THEN** the transaction's `category_id` SHALL be updated to the suggested category's ID
