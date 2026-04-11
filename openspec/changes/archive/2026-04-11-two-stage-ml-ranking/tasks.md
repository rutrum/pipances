## 1. Setup and Constants

- [x] 1.1 Add adjustment factor bounds as constants: `AMOUNT_FACTOR_MATCH` (1.1), `AMOUNT_FACTOR_NOMATCH` (0.9), `SECONDARY_FACTOR_MATCH` (1.05), `SECONDARY_FACTOR_NOMATCH` (1.0)
- [x] 1.2 Document all constants with inline comments explaining their role and the mathematical guarantee that multiplication preserves text-ranking

## 2. Text-Only kNN Infrastructure

- [x] 2.1 Refactor `fit()` to separately train a text-only kNN model (in addition to or instead of combined-feature kNN)
- [x] 2.2 Store text-only TfidfVectorizer and kNN separately (e.g., `self._text_knn`, `self._text_tfidf`)
- [x] 2.3 Verify that existing fit() calls work without breaking (API compatibility)

## 3. Structured Feature Reweighting

- [x] 3.1 Create new helper method `_compute_adjustment_factors()` that takes amount/date/account/institution and returns scalar adjustment multiplier (product of individual factors)
- [x] 3.2 Implement amount factor logic: 1.1 if within 2x tolerance, 0.9 otherwise
- [x] 3.3 Implement day-of-week/month/account/institution factor logic: 1.05 if match, 1.0 otherwise
- [x] 3.4 Test adjustment factor logic independently with unit tests, including edge cases (verify 0.42 × 1.1 < 0.72 × 0.9)

## 4. Two-Stage Prediction Refactor

- [x] 4.1 Refactor `predict()` method to:
  - Stage 1: Retrieve ~50 text-similar neighbors using text-only kNN
  - Stage 2: Compute adjustment factors and multiply similarities (adjustment_factor is always in [0.9, 1.1] range, preserving text ranking)
  - Pass adjusted similarities to existing `_vote_field()` logic
- [x] 4.2 Ensure similarities remain in [0, 1] after adjustment (they should given bounded factors)
- [x] 4.3 Verify that `_vote_field()` logic remains unchanged (no modification to voting threshold logic)

## 5. Testing

- [x] 5.1 Update or create unit tests for `_compute_adjustment_factors()` including verification that text ranking is preserved (0.72×0.9 > 0.42×1.1)
- [x] 5.2 Update or create unit tests for `_build_feature_matrix()` (unchanged but verify it still works)
- [x] 5.3 Create integration test: fit model, make prediction, verify text-similarity-primary behavior (e.g., same description with different amount should match)
- [x] 5.4 Create regression test: fit on existing approved transactions, verify predictions still made (backward compatibility)
- [x] 5.5 Run existing test suite to ensure no breakage

## 6. Validation and Edge Cases

- [x] 6.1 Test with few approved transactions (< 10) to ensure kNN doesn't break
- [x] 6.2 Test with transactions with empty descriptions to ensure TF-IDF handles gracefully
- [x] 6.3 Test edge case: 5 good text matches vs 45 weak text matches, verify good matches win even with opposite adjustment directions
- [x] 6.4 Test with extreme amounts (e.g., $0.01 vs $100,000) to verify multiplicative factors preserve text ranking
- [x] 6.5 Verify that no new dependencies were added (should still be scikit-learn + scipy)

## 7. Documentation and Handoff

- [x] 7.1 Update docstring for `TransactionPredictor.predict()` to explain two-stage behavior and bounded multiplicative factors
- [x] 7.2 Update docstring for `fit()` to explain that text-only kNN is now primary
- [x] 7.3 Add inline comments explaining the mathematical guarantee: "Multiplication by factors in [0.9, 1.1] preserves ordering of text similarities"
- [x] 7.4 Create or update CHANGELOG entry describing the behavior change
- [x] 7.5 Document the adjustment factor constants and their recommended values

## 8. Manual Testing

- [x] 8.1 Seed database with test transactions from `scripts/seed.py`
- [x] 8.2 Manually verify retrain on inbox produces sensible suggestions (text-driven, not amount-driven)
- [x] 8.3 Verify that clearing a category and retraining now restores text-matched suggestions, not amount-matched ones

