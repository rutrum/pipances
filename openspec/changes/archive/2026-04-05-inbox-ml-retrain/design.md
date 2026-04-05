## Context

The inbox page allows users to review and approve pending transactions. ML predictions run automatically at import time using approved transactions as training data. During a long cleaning session, users approve many transactions but the ML model doesn't benefit from this new labeled data until the next import.

## Goals / Non-Goals

**Goals:**
- Allow users to re-run ML predictions mid-session using newly approved transactions as training data
- Preserve user manual edits (never overwrite what user explicitly set)
- Only update predictions when new confidence exceeds current confidence

**Non-Goals:**
- Real-time prediction as each transaction is approved (button click is sufficient)
- Spinner/loading state (immediate return is acceptable for 1-10k transactions)
- Prediction for transactions with no approved training data

## Decisions

### 1. Selective Update Strategy

**Decision:** Only update a field if `new_confidence > current_confidence`

**Rationale:** This ensures:
- User manual edits are never overwritten (they have `ml_confidence_* = None`, so any prediction beats `None`)
- Better predictions replace worse ones
- No-op when model confidence hasn't improved

**Alternative considered:** Always replace. Rejected because it would overwrite user edits.

### 2. Training Data Scope

**Decision:** Train on ALL approved transactions, not just those from current session

**Rationale:** 
- 1-10k transactions is small enough for full retrain
- Historical data provides more signal than just current batch
- Simpler implementation (reuses existing `_predict_for_transactions` logic)

### 3. Button Placement

**Decision:** Add Retrain button in inbox toolbar, to the left of Commit button, with `btn-secondary` class

**Rationale:**
- Natural workflow: retrain → see suggestions → approve → commit
- Visual distinction from Commit (secondary vs primary color)
- No additional toolbar needed

### 4. Response Handling

**Decision:** Return HTMX response that refreshes the inbox table with OOB toast

**Rationale:** Matches existing patterns for bulk operations in inbox. User sees updated ML suggestions without full page reload.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Retrain takes too long with large data | Current assumption is 1-10k transactions; monitor and add async if needed |
| No approved transactions exist | Show toast "No training data available"; button could be disabled in that state |
| Model degrades with noisy new data | Confidence gating filters low-quality predictions (existing in `predict.py`) |

## Open Questions

1. **Should Retrain be disabled when no approved transactions exist?** Currently leaning toward showing a toast message instead, so users understand why nothing happened.
