## Why

Currently, ML predictions only run at import time. In a long inbox cleaning session, the model is trained on data from before the session started. As users approve transactions, there's valuable new training data that could improve predictions for remaining pending transactions—but it's not being used until the next import.

## What Changes

- Add a "Retrain" button to the inbox toolbar (next to Commit, different color)
- New endpoint `POST /inbox/retrain` that:
  1. Trains the ML model on all approved transactions (existing + newly approved)
  2. Re-predicts all pending transactions
  3. Updates each field only if new confidence > current confidence (preserving user edits)
- Returns HTMX response to refresh the inbox table with updated ML suggestions

## Capabilities

### New Capabilities
- `inbox-ml-retrain`: Ability to re-run ML predictions on pending transactions mid-session using newly approved data as training input

### Modified Capabilities
- `ml-predictions`: Requirement change - predictions can now run on-demand, not just at import time. Add requirement: "Prediction runs on-demand via user action in inbox"

## Impact

- **New file**: `routes/inbox.py` - add `POST /inbox/retrain` endpoint
- **Modified**: `ingest.py` - the `_predict_for_transactions` function already exists, may need a variant that updates selectively (confidence comparison)
- **UI**: Add Retrain button to `inbox.html` toolbar
- **No DB changes**: Uses existing ml_confidence_* columns
