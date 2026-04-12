## Context

The `TransactionPredictor` class in `src/pipances/predict.py` uses k-NN with TF-IDF text features to recommend descriptions, categories, and external accounts for pending transactions based on approved transaction history. Currently, any value that achieves sufficient confidence in the voting stage is recommended, even if it appears only once in training data. This causes unique/non-recurring values to pollute suggestions.

## Goals / Non-Goals

**Goals:**
- Filter out values that appear in fewer than 2 training transactions
- Apply this filter uniformly across all recommended fields (description, category, external)
- Treat filtered values as "no recommendation" (blank) — consistent with low-confidence behavior
- No API changes or database schema modifications
- Maintain backward compatibility with existing code

**Non-Goals:**
- Making the recurrence threshold configurable (fixed at 2 for MVP)
- Changing the voting or confidence mechanisms
- Modifying `fit()` or `predict()` method signatures

## Decisions

**Decision 1: Frequency tracking during fit()**
- Store three Counter objects: `_description_freq`, `_category_freq`, `_external_freq`
- Each maps value → count of how many training transactions have that value
- Computed once during `fit()`, reused for all predictions
- **Rationale**: One-pass computation; minimal memory overhead; fast O(1) lookup during prediction

**Decision 2: Filter applied after voting**
- Voting logic unchanged: neighbors still vote as before
- After `_vote_field()` determines the winner, check: `if freq_map[winner] >= 2, use it; else return None`
- **Rationale**: Orthogonal to voting; simpler to reason about; consistent with existing confidence filtering

**Decision 3: Treatment as blank field**
- Sub-threshold values return `None` (no prediction), not a reduced-confidence Prediction
- Existing code treats `None` as "blank field" — no new logic needed
- **Rationale**: Matches existing low-confidence behavior; minimal code change; predictable UX

**Alternatives Considered:**
- *Dynamic threshold* (e.g., 3 for high-stakes fields): Rejected — too complex, no user input on threshold preference
- *Reduced confidence score instead of blank*: Rejected — user sees same prediction twice (confusing); blank is clearer
- *Apply filter before voting*: Rejected — expensive O(k) check per neighbor; after voting is simpler

## Risks / Trade-offs

**Trade-off: Conservative early behavior**
- New merchants invisible until 2nd+ transaction (0 → 1 occurrence below threshold)
- **Mitigation**: User accepted this as acceptable (preference for missing over noise)
- On 2nd transaction of a new merchant, recommendation appears

**Risk: Frequency data staleness**
- If training data changes mid-session, model must be re-fit to pick up new frequencies
- **Mitigation**: No different from current model retraining — already explicit via `retrain` button

**Risk: Edge case with very few transactions**
- If only 2 training transactions exist, no value appears 2+ times
- **Mitigation**: Rare scenario; user wanted this behavior anyway

## Migration Plan

1. Add frequency tracking to `fit()` (new instance attributes)
2. Add recurrence check to prediction path (after voting)
3. Expand test suite to verify threshold enforcement
4. On deploy: Model will recompute frequencies from existing approved transactions
5. No user action required; retraining existing data picks up new behavior

## Open Questions

- None; approach is straightforward. User approved the 2-transaction threshold.
