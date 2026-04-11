## Context

Currently, `TransactionPredictor` uses a single-stage kNN pipeline where:
1. All features (text TF-IDF + numeric StandardScaler + categorical OneHotEncoder) are combined via hstack into a single feature matrix
2. kNN finds K nearest neighbors using cosine distance over the combined matrix
3. Voting is applied to predict each field (description, category, external)

The problem: numeric features (especially amount) have high variance and discriminative power, dominating the distance metric. Similar descriptions with different amounts receive lower similarity scores than different descriptions with identical amounts.

Current pipeline in `predict.py`:
- `_build_feature_matrix()` creates numeric + categorical array
- Text features come from TF-IDF vectorizer
- `ColumnTransformer` (StandardScaler + OneHotEncoder) processes structured features
- `hstack()` combines text + structured into single matrix
- kNN operates on combined matrix
- `_vote_field()` aggregates neighbor labels

## Goals / Non-Goals

**Goals:**
- Make text description (TF-IDF) the primary matching signal
- Reduce amount's influence on neighbor selection
- Preserve voting logic (no changes to `_vote_field()`)
- Maintain API compatibility (fit/predict signatures unchanged)
- No new dependencies

**Non-Goals:**
- Replacing TF-IDF with embeddings (that's Option C)
- Bucketing amounts into ranges
- Changing the voting threshold or confidence logic
- Optimizing for performance (acceptable to be slightly slower)
- Retraining existing models (this is a code change, not a model format change)

## Decisions

**Decision 1: Two-stage retrieval with text as primary**

Approach:
1. **Stage 1 - Text retrieval**: Build kNN on text features alone, retrieve top ~50 neighbors by text similarity
2. **Stage 2 - Structured re-ranking**: Among those 50, weight similarities based on amount/date/account agreement

Why text-only kNN first: Text similarity is stable and uncontaminated by numeric features. A description like "KROGER" should match other grocery transactions regardless of amount.

Why re-weight after: Numeric features are useful for tiebreaking. Among 10 "grocery store" neighbors, prefer the $40 one over the $5000 one if the new transaction is $40.

Alternative considered: Manually down-weight amount in the ColumnTransformer (e.g., scale by 0.1). Rejected because:
- Still mixes primary and secondary signals
- Harder to tune (one number for all scenarios)
- Two-stage approach is clearer and more controllable

**Decision 2: Reweighting formula with bounded multiplicative factors**

Among the top text neighbors, reweight similarities using small **multiplicative adjustment factors** bounded to [0.9, 1.1]:
- Amount: factor = 1.1 if within 2x tolerance, 0.9 otherwise
- Day-of-week/month: factor = 1.05 if match, 1.0 otherwise
- Account: factor = 1.05 if match, 1.0 otherwise
- Institution: factor = 1.05 if match, 1.0 otherwise

Reweighting combines factors multiplicatively:
```
adjusted_sim = text_sim * amount_factor * dow_factor * account_factor * institution_factor
```

**Why small bounded factors (0.9–1.1) solve the ordering problem:**

Multiplication preserves ordering: if A > B, then A×k₁ > B×k₂ for any positive k₁, k₂ in [0.9, 1.1]. This guarantees that strong text matches cannot be beaten by weak text matches, even with opposite adjustment directions.

Example: Good match (0.72 text sim) vs. weak match (0.42 text sim)
- Best case for weak (boost): 0.42 × 1.1 = 0.462
- Worst case for good (penalty): 0.72 × 0.9 = 0.648
- Result: 0.648 > 0.462 ✅ Text ranking is preserved

This approach is simple, clean, and mathematically guarantees that structured features refine but never invert text-based rankings.

Alternative considered: Large factors (e.g., up to 2.0) with explicit clamping logic. Rejected because bounded multiplicative factors are simpler and the math is cleaner.

**Decision 3: Architecture changes to predict.py**

Refactor `predict()` method:
1. Call text-only kNN to retrieve ~50 neighbors (instead of K=10 neighbors on combined features)
2. Compute adjustment factors for each neighbor based on amount/date/account
3. Apply adjustments to similarities
4. Pass adjusted similarities to `_vote_field()` as before

Keep `fit()` method similar but ensure we train both:
- Text kNN on text features alone (new)
- Optionally keep combined-feature kNN as fallback (old approach) during transition

No changes to `_vote_field()`, `_cyclical_encode()`, or voting thresholds.

**Decision 4: Tuning parameters**

New hyperparameters (all with defaults in code):
- `STAGE1_K`: Number of text neighbors to retrieve (~50, or 5x the final K=10)
- `AMOUNT_TOLERANCE`: Factor for amount agreement (e.g., 2.0 = within 2x is OK)
- `ADJUSTMENT_BOOST`: How much structured features can boost similarity (e.g., 1.2 = up to 20% boost)

All tunable but not exposed in API (only via code constants).

## Risks / Trade-offs

**Risk 1: Different predictions**
→ *Mitigation*: New behavior is intentional (text-primary). Document in CHANGELOG. Run A/B if concerned.

**Risk 2: Slight performance degradation**
→ *Mitigation*: Two kNN lookups instead of one. Impact: ~5-10% slower per prediction. Acceptable for inbox workload (<100 pending txns). Monitor if retrain is slow.

**Risk 3: Extreme amounts (e.g., $0.01 vs $10,000) might still be problematic**
→ *Mitigation*: Log-scale amount in reweighting formula, or use amount buckets. Future improvement (not in this change).

**Risk 4: Text-only kNN is very sparse (many transactions with no description)**
→ *Mitigation*: Fallback to combined-feature kNN if text neighbors have low similarity. Can add with extra if-statement in Stage 1.

**Trade-off: Simpler vs. cleaner**
The adjustment-factor approach is pragmatic but not as clean as complete re-architecture. We keep StandardScaler + hstack infrastructure in case we need fallback. Alternative: Completely separate text and structured pipelines. Chosen approach because incremental, reversible, less risk.

## Migration Plan

1. Deploy code change to `predict.py` (backward compatible, API unchanged)
2. All future retrains use new two-stage logic automatically
3. Existing approved transactions still used as training data (no migration needed)
4. Monitor prediction accuracy on retrained models (compare suggestion acceptance rate)
5. If issues: quick rollback by reverting predict.py

No data migrations, no database changes, no user-facing changes.

## Open Questions

- **Exact adjustment formula**: Should amount factor be sigmoid, linear, or step-function? (Needs experimentation)
- **STAGE1_K tuning**: Is 50 neighbors enough, or does it vary by dataset size? (Can tune later)
- **Fallback strategy**: Should we add text-only fallback if Stage 1 neighbors have sim < 0.3? (Nice-to-have)
