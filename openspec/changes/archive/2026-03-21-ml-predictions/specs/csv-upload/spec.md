## Delta

### Modified Requirement: CSV upload parses and ingests transactions

Add after dedup and insertion step:

#### Scenario: Import triggers ML prediction
- **WHEN** CSV import successfully inserts new pending transactions
- **THEN** the system SHALL run the ML prediction engine on the newly inserted transactions before redirecting to inbox
- **THEN** predicted fields (description, category, external account) SHALL be pre-populated with confidence scores where the model has sufficient confidence
- **THEN** the import result summary SHALL continue to display as before (prediction is transparent to the summary)
