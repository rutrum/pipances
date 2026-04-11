## Why

The current ML prediction model uses k-NN with combined text (TF-IDF) and numeric/categorical features (amount, date, account) in a single feature space. The amount feature has such high discriminative power that identical amounts create very strong similarity signals, dominating predictions even when transaction descriptions are quite different. This causes poor suggestions: a "$87.43 grocery store" matches "$87.43 Shell Gas Station" more strongly than "$5 Kroger" even though the latter is semantically identical. We need to flip the primary signal: text description should drive matching, and amount/date/account should refine rather than dominate.

## What Changes

- Refactor prediction pipeline to use a **two-stage ranking** approach:
  1. **Stage 1 (primary)**: Find neighbors based on text similarity (TF-IDF cosine) alone
  2. **Stage 2 (secondary)**: Re-rank candidates using structured features (amount, date, account) as tiebreakers
- Update the `TransactionPredictor.predict()` method to:
  - First retrieve ~50 text-based neighbors from the kNN model
  - Weight their similarities based on amount/date/account agreement
  - Apply voting with the reweighted similarities
- Keep all voting logic unchanged; only the neighbor selection and weighting strategy changes
- No API changes; signatures of `fit()` and `predict()` remain the same

## Capabilities

### New Capabilities

*(None - this is an implementation refinement of existing capability)*

### Modified Capabilities

- `ml-predictions`: Text-based similarity becomes primary signal; structured features (amount, date, account) now act as re-ranking refinements instead of co-equal features in the distance metric

## Impact

- **Code**: `src/pipances/predict.py` - refactor kNN pipeline and similarity reweighting logic
- **Behavior**: Predictions will prioritize semantic similarity (matching descriptions) over matching amounts
- **Testing**: Existing unit tests may need updates to reflect new behavior
- **Performance**: Slightly increased computation per prediction (two-stage vs. single k-NN query), but negligible for typical use cases
- **Dependencies**: None new; continues using scikit-learn and scipy
