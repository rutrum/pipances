## Why

Manually filling in description, category, and external account for every imported transaction is tedious. Most bank transactions are repetitive — the same merchants appear over and over with similar raw descriptions. Users who have already reviewed hundreds of transactions have effectively built a labeled dataset. We should use that data to pre-fill fields on new imports, reducing manual work while keeping the human review gate intact.

## What Changes

- Add a prediction engine that uses approved transactions as training data to suggest description, category, and external account for newly imported transactions
- The engine uses scikit-learn TF-IDF with character n-grams on `raw_description`, combined with numeric features (amount, date patterns) and categorical features (internal account, importer) via a `ColumnTransformer` + kNN pipeline
- Predictions run at import time: after CSV parsing and dedup, the model is fitted on all approved transactions and used to fill fields on the new pending transactions
- Each predicted field stores its confidence score in a new column on the Transaction model (`ml_confidence_description`, `ml_confidence_category`, `ml_confidence_external`)
- A two-stage confidence gate ensures quality: a minimum similarity floor filters irrelevant neighbors, then an agreement threshold among remaining neighbors determines whether to suggest
- The inbox UI visually distinguishes ML-suggested values from human-set or CSV-original values using per-field styling (e.g. colored background or badge via DaisyUI)
- Predictions are auto-fill only — transactions always land in the inbox as pending, the user always reviews before committing

## Capabilities

### New Capabilities
- `ml-predictions`: ML prediction engine for transaction field suggestions

### Modified Capabilities
- `csv-upload`: Import flow triggers prediction after dedup, before returning results
- `inbox-review`: Inbox rows visually distinguish ML-suggested fields from human-set fields; editing an ML-suggested field clears its confidence (becomes human-set)

## Impact

- **New files**: `predict.py` (prediction engine module)
- **Modified files**: `models.py` (3 new nullable float columns), `db.py` (ALTER TABLE migrations), `ingest.py` (call prediction after insert), `main.py` (PATCH endpoints clear confidence on edit), inbox templates (visual indicators for ML fields)
- **New dependency**: `scikit-learn` (TF-IDF vectorizer, NearestNeighbors, ColumnTransformer, StandardScaler, OneHotEncoder)
- **Behavior change**: Imported transactions may arrive in inbox with fields pre-filled; the model degrades gracefully with 0 approved transactions (no predictions made)
