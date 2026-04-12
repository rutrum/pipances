## 1. Add frequency tracking to model

- [x] 1.1 Add three Counter instance attributes to `TransactionPredictor`: `_description_freq`, `_category_freq`, `_external_freq`
- [x] 1.2 Populate frequency counters in `fit()` method from approved training data
- [x] 1.3 Verify counters are initialized (add `assert` or early test)

## 2. Implement recurrence filtering

- [x] 2.1 Create helper method `_meets_recurrence_threshold()` that checks if a value exists in frequency map with count ≥ 2
- [x] 2.2 Add recurrence check in prediction path: after `_vote_field()` returns a winner, filter out sub-threshold values
- [x] 2.3 Sub-threshold values return `None` (treated as blank field by existing UI logic)

## 3. Unit tests for recurrence threshold

- [x] 3.1 Test: Single-occurrence value is filtered out (returns None)
- [x] 3.2 Test: Two-occurrence value passes threshold (returns prediction)
- [x] 3.3 Test: Threshold applied independently per field (one field filtered, another passes)
- [x] 3.4 Test: Frequency counters created correctly during fit()
- [x] 3.5 Test: Empty training data or few transactions doesn't crash

## 4. Integration tests

- [x] 4.1 Test: Full workflow with realistic training data (multiple unique and recurring values)
- [x] 4.2 Test: Retrain flow re-computes frequencies correctly
- [x] 4.3 Test: Backward compatibility: existing approved transactions work without schema changes

## 5. Manual testing

- [x] 5.1 Reset database, seed with test data (`just reset-db && just seed`)
- [x] 5.2 Retrain and verify predictions only show recurring patterns
- [x] 5.3 Spot-check inbox to confirm single-occurrence values are not suggested

## 6. Verification

- [x] 6.1 Run `just test` to confirm all tests pass (no regressions)
- [x] 6.2 Run code quality checks: `just lint` and `just fmt`
