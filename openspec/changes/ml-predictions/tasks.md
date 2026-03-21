## 1. Data Model

- [x] 1.1 Add `ml_confidence_description` (Float, nullable), `ml_confidence_category` (Float, nullable), `ml_confidence_external` (Float, nullable) columns to the Transaction model in `models.py`
- [x] 1.2 Add ALTER TABLE migrations in `db.py` with PRAGMA table_info checks for each new column

## 2. Prediction Engine

- [x] 2.1 Add `scikit-learn` to project dependencies via uv
- [x] 2.2 Create `src/financial_pipeline/predict.py` with the prediction engine:
  - Build training DataFrame from approved transactions (raw_description, amount_cents, date, internal_id, institution)
  - Cyclical encoding for day_of_week and day_of_month (sin/cos)
  - ColumnTransformer: TF-IDF char n-grams on raw_description, StandardScaler on numerics, OneHotEncoder on categoricals
  - NearestNeighbors with cosine metric
  - Two-stage confidence gating: similarity floor then agreement threshold
  - Per-field weighted voting among qualifying neighbors
  - Return predictions as a list of per-transaction field suggestions with confidence scores
- [x] 2.3 Define confidence constants (similarity floor, agreement threshold, k neighbors) at module level in `predict.py`

## 3. Integration with Import Flow

- [x] 3.1 Call prediction engine from `ingest()` after transaction insertion: fit on approved transactions, predict for newly inserted pending transactions, UPDATE predicted fields + confidence scores
- [x] 3.2 Handle graceful no-op when 0 approved transactions exist (skip prediction entirely)

## 4. Inbox UI: ML Indicators

- [x] 4.1 Update `_inbox_row.html` to visually distinguish ML-suggested fields (per-field styling when `ml_confidence_*` is not None) — try DaisyUI utilities and pick what looks good
- [x] 4.2 Update PATCH endpoints in `main.py` to clear the corresponding `ml_confidence_*` column when a user edits a field (description, category, external account)

## 5. Verification

- [x] 5.1 Run `just seed` to populate approved test data, then import `test_export.csv` — verify predictions appear on new transactions where similar approved transactions exist
- [x] 5.2 Verify ML-suggested fields are visually distinct in the inbox
- [x] 5.3 Verify editing an ML-suggested field clears the visual indicator
- [x] 5.4 Verify importing with 0 approved transactions produces no errors and no predictions
- [x] 5.5 Run `just lint` and `just fmt` to ensure code quality
