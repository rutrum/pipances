## MODIFIED Requirements

### Requirement: Model uses text-primary matching with structured re-ranking
The prediction model SHALL use `raw_description` as the primary matching signal (text stage). Predictions SHALL be made by finding neighbors whose transaction descriptions are most similar via TF-IDF character n-grams, then re-ranking those neighbors based on agreement on secondary features (amount, date, account, institution).

#### Scenario: Feature extraction and two-stage matching
- **GIVEN** a transaction with raw_description, amount_cents, date, internal_id, and import institution
- **WHEN** the model makes predictions for this transaction
- **THEN** the system SHALL:
  1. Extract TF-IDF character n-grams (3-5 characters) from raw_description
  2. Retrieve ~50 training transactions with highest text similarity (cosine distance on TF-IDF alone)
  3. Adjust the similarity scores of those neighbors based on amount, date, and account agreement (multiplicative factors; structured features act as refinement, not as primary matching criteria)
  4. Apply voting on the adjusted similarities to determine final predictions
- **THEN** transactions with very different descriptions but identical amounts SHALL NOT automatically match
- **THEN** transactions with identical descriptions but different amounts SHALL still be strong matches

#### Scenario: Contextual features as secondary signals
- **GIVEN** multiple training transactions with similar descriptions to a pending transaction
- **WHEN** determining which neighbor prediction to use
- **THEN** the system SHALL prefer neighbors with:
  - Similar amount_cents (within a tolerance, e.g., 2x original)
  - Same day-of-week or day-of-month patterns
  - Same internal account
  - Same importer institution
- **THEN** these structural features SHALL NOT override text similarity decisions
- **THEN** if two neighbors have very different text similarity scores, the higher text similarity SHALL win even if the lower-scoring neighbor has better amount match

### Requirement: Backward compatibility
The system's public API (fit/predict method signatures and database schema) SHALL remain unchanged.

#### Scenario: Existing code continues to work
- **WHEN** existing code calls `TransactionPredictor.fit(...)` and `predict(...)`
- **THEN** the method signatures SHALL be identical
- **THEN** the system SHALL work with existing approved transaction data without migration
- **THEN** the system SHALL accept retrained models without schema changes
