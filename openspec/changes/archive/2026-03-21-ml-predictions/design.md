## Context

Users import bank transaction CSVs and manually review them in the inbox before committing. Fields like description, category, and external account must be filled in by hand. Bank transaction descriptions are repetitive and code-like (e.g. "AMZN Mktp US*RT3K21"), making them well-suited for character-level pattern matching. Every approved transaction is a labeled example that can train a model.

## Goals / Non-Goals

**Goals:**
- Pre-fill description, category, and external account on imported transactions using patterns from approved transactions
- Track per-field whether a value was ML-suggested (with confidence score)
- Visually distinguish ML-suggested fields in the inbox UI
- Graceful degradation: zero approved transactions → no predictions, no errors
- Clearing/editing an ML-suggested field makes it human-set (clears confidence)

**Non-Goals:**
- Auto-applying transactions (skipping inbox review) — never
- On-demand re-prediction button in inbox (deferred to TODO)
- Multiple suggestions per field (deferred to TODO)
- Model caching/persistence (rebuild on each import for now)
- User-configurable confidence thresholds (use sensible defaults)
- Semantic embeddings (TF-IDF char n-grams first; upgrade path in TODO)

## Decisions

### Decision: scikit-learn TF-IDF with character n-grams + kNN

The prediction engine uses a scikit-learn pipeline:

```
ColumnTransformer
├── raw_description → TfidfVectorizer(analyzer='char_wb', ngram_range=(3,5))
├── numeric features → StandardScaler
│   ├── amount_cents
│   ├── day_of_week (sin + cos encoded)
│   └── day_of_month (sin + cos encoded)
└── categorical features → OneHotEncoder(handle_unknown='ignore')
    ├── internal_id
    └── importer (institution from Import)

→ Combined feature vector → NearestNeighbors(metric='cosine')
```

Character n-grams are ideal for bank descriptions: "AMZN Mktp US*RT3K21" and "AMZN Mktp US*ZZ1234" share extensive 3-gram overlap. The model is trained on the user's own data, learning their bank's specific abbreviation patterns.

Numeric and categorical features provide context without fragmenting the similarity search — they're additional dimensions in the combined feature space that nudge similarity scores.

**Alternative considered**: Exact/fuzzy match rules. Rejected because it requires user-maintained rules and doesn't generalize.

**Alternative considered**: Sentence embeddings (Model2Vec, FastEmbed). Deferred — char n-grams are purpose-built for structured short text. Embeddings are an upgrade path if TF-IDF proves insufficient.

**Alternative considered**: LLM prompting. Rejected for v1 — adds external API dependency, latency, and cost.

### Decision: Two-stage confidence gating

Predictions use two thresholds to avoid suggesting garbage:

**Stage 1 — Similarity floor**: After kNN retrieval, discard any neighbor below a minimum cosine similarity (e.g. 0.4). This prevents low-quality matches from influencing votes. If no neighbors pass the floor, no suggestion is made.

**Stage 2 — Agreement threshold**: Among passing neighbors, compute a weighted vote per field:

```
confidence(field, value) = sum(similarity of neighbors voting for value)
                           / sum(similarity of all passing neighbors)
```

If the top value's confidence exceeds the agreement threshold (e.g. 0.6), suggest it. Otherwise, leave the field blank.

This handles the case where all neighbors are at sim=0.2 (all filtered in stage 1) and the case where neighbors disagree (low agreement in stage 2).

Thresholds are hardcoded constants in `predict.py` for now. They can be made configurable later if needed.

### Decision: Per-field confidence columns on Transaction

Add three nullable float columns to the Transaction model:

```python
ml_confidence_description: Mapped[float | None]  # None = not ML-suggested
ml_confidence_category: Mapped[float | None]
ml_confidence_external: Mapped[float | None]
```

`None` means the field was not ML-suggested (either human-set, CSV-original, or the model chose not to suggest). A float value (0.0–1.0) means the model suggested this field's current value with that confidence.

When a user edits an ML-suggested field (via inline editing in the inbox), the corresponding confidence column is set to `None` — it's now human-set.

**Alternative considered**: Boolean flags (ml_suggested_description: bool). Rejected because confidence scores enable future UI refinements (e.g. stronger/weaker visual indicator).

**Alternative considered**: JSON blob. Rejected because individual columns are queryable, type-safe, and simpler to migrate.

### Decision: Prediction runs at import time in ingest()

After CSV parsing, dedup, and transaction insertion, `ingest()` calls the prediction engine:

```
parse CSV → dedup → INSERT pending transactions → predict & UPDATE fields
```

The prediction step:
1. Queries all approved transactions (with their Import records for institution)
2. Fits the ColumnTransformer + kNN on approved data
3. Transforms the newly inserted pending transactions
4. For each pending transaction, queries kNN, runs two-stage confidence gating per field
5. Updates the pending transaction with suggested values + confidence scores

If there are 0 approved transactions, step 2 is skipped (nothing to train on). Graceful no-op.

**Alternative considered**: Predict before INSERT (in-memory). Rejected because we need the transaction IDs for the UPDATE, and post-insert is cleaner separation.

### Decision: Cyclical encoding for date features

Day-of-week (0–6) and day-of-month (1–31) are encoded as sin/cos pairs:

```python
sin_dow = sin(2π * day_of_week / 7)
cos_dow = cos(2π * day_of_week / 7)
sin_dom = sin(2π * day_of_month / 31)
cos_dom = cos(2π * day_of_month / 31)
```

This ensures day 31 is close to day 1, and Sunday is close to Monday. Raw ordinal encoding would create an artificial distance between boundary values.

Month and year are excluded — they would introduce temporal bias.

### Decision: Visual distinction via DaisyUI styling

ML-suggested fields in the inbox get a visual indicator. The exact styling will be determined during implementation, but candidates include:

- Tooltip showing "ML suggested (85% confidence)" on hover
- Subtle background tint (e.g. `bg-info/10` or similar DaisyUI utility)
- Small badge or icon adjacent to the value

The indicator is per-field: one transaction might have an ML-suggested description but a human-set category. When the user edits the field, the indicator disappears (confidence cleared).

Exact styling deferred to implementation — try options and pick what looks best with the existing inbox design.

### Decision: External account handling for predictions

When the model suggests an external account, it suggests the `external_id` (the account ID) based on what past similar transactions were assigned to. The external account must already exist in the database (it was created during a prior import or manually).

If the model's top vote is for an external account that has since been deleted/pruned, that vote is excluded from the tally. This is unlikely but handled gracefully.

## Risks / Trade-offs

- **Cold start**: With 0 approved transactions, the model does nothing. With few approved transactions, predictions may be sparse or low-confidence. This is acceptable — the system is purely additive and never worse than the current manual flow.
- **Rebuild cost**: The model is rebuilt from scratch on every import. For typical datasets (<10k approved transactions), TF-IDF + kNN fitting is milliseconds. If this becomes a bottleneck, model caching is a future optimization (in TODO).
- **Feature weighting**: TF-IDF produces many columns (one per n-gram) so text naturally dominates the combined feature space. Numeric/categorical features provide secondary signal. If the balance is wrong, we can scale feature groups, but this is an optimization to defer.
- **scikit-learn dependency**: Adds ~30MB to the install. Acceptable for the functionality gained. No torch/tensorflow required.
- **Threshold tuning**: Hardcoded similarity floor (0.4) and agreement threshold (0.6) are educated guesses. May need adjustment based on real-world usage. Easy to change — they're constants in one file.
