## Why

The ML model currently recommends transaction descriptions, categories, and external accounts based on text similarity alone, even when those values appear only once in the training data. This introduces noise: unique, non-recurring descriptions get recommended anyway, polluting the suggestions with one-off labels. We need to enforce a minimum recurrence threshold so only values seen in at least 2 training transactions are eligible for recommendation.

## What Changes

- The ML model tracks frequency (recurrence count) for each recommended value during training
- Predictions now filter out values that appear fewer than 2 times in training data
- Single-occurrence values are treated as "no recommendation" (blank field) — same as low-confidence predictions
- No API changes: `fit()` and `predict()` signatures remain identical

## Capabilities

### New Capabilities
<!-- none -->

### Modified Capabilities
- `ml-predictions`: Add recurrence threshold filtering to ensure only recurring patterns (≥2 occurrences) are recommended for description, category, and external account fields

## Impact

- **Code**: `src/pipances/predict.py` - Add frequency tracking and filtering logic
- **Tests**: Expand test suite to cover minimum recurrence enforcement
- **DB schema**: No changes
- **API**: No breaking changes
