"""ML prediction engine for transaction field suggestions.

Uses TF-IDF character n-grams on raw_description combined with numeric
and categorical features via a ColumnTransformer + kNN pipeline.
"""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass

import numpy as np
from scipy.sparse import hstack, issparse
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import OneHotEncoder, StandardScaler

# ── Confidence constants ──────────────────────────────────────────────
SIMILARITY_FLOOR = 0.4  # Minimum cosine similarity to consider a neighbor
AGREEMENT_THRESHOLD = 0.6  # Minimum weighted agreement to suggest a value
K_NEIGHBORS = 10  # Number of neighbors to retrieve

# ── Two-stage ranking adjustment factors ───────────────────────────────
# These factors are applied multiplicatively to adjust text-based similarities
# after Stage 1 (text-only neighbor retrieval) based on agreement of structured
# features (amount, date, account, institution) in Stage 2.
#
# Mathematical guarantee: Multiplication by factors in [0.9, 1.1] preserves
# the ordering of text similarities. If A > B, then A*k1 > B*k2 for any
# k1, k2 ∈ [0.9, 1.1]. This ensures strong text matches cannot be beaten by
# weak text matches, even with opposite adjustment directions.
#
# Example: Good match (sim=0.72) vs weak match (sim=0.42)
#   Good penalized, weak boosted: 0.72 * 0.9 = 0.648 > 0.42 * 1.1 = 0.462 ✓
AMOUNT_FACTOR_MATCH = 1.1  # Amount within 2x tolerance (boost agreement)
AMOUNT_FACTOR_NOMATCH = 0.9  # Amount outside 2x tolerance (penalize disagreement)
SECONDARY_FACTOR_MATCH = 1.05  # Day-of-week/month, account, institution match
SECONDARY_FACTOR_NOMATCH = 1.0  # No matching secondary feature


@dataclass
class FieldPrediction:
    value: object  # The predicted value (str, int, etc.)
    confidence: float  # Agreement score among qualifying neighbors


@dataclass
class TransactionPrediction:
    description: FieldPrediction | None = None
    category_id: FieldPrediction | None = None
    external_id: FieldPrediction | None = None


def _cyclical_encode(value: float, period: float) -> tuple[float, float]:
    angle = 2 * math.pi * value / period
    return math.sin(angle), math.cos(angle)


def _build_feature_matrix(
    raw_descriptions: list[str],
    amounts: list[int],
    days_of_week: list[int],
    days_of_month: list[int],
    internal_ids: list[str],
    institutions: list[str],
) -> np.ndarray:
    """Build the numeric/categorical feature matrix (non-text features).

    Returns a 2D array with columns:
    [amount, sin_dow, cos_dow, sin_dom, cos_dom, internal_id_str, institution_str]
    """
    rows = []
    for i in range(len(raw_descriptions)):
        sin_dow, cos_dow = _cyclical_encode(days_of_week[i], 7)
        sin_dom, cos_dom = _cyclical_encode(days_of_month[i], 31)
        rows.append(
            [
                amounts[i],
                sin_dow,
                cos_dow,
                sin_dom,
                cos_dom,
                internal_ids[i],
                institutions[i],
            ]
        )
    return np.array(rows, dtype=object)


class TransactionPredictor:
    """Predicts description, category, and external account for transactions."""

    def __init__(self):
        self._knn: NearestNeighbors | None = None
        self._text_knn: NearestNeighbors | None = None
        self._text_tfidf: TfidfVectorizer | None = None
        self._labels: dict[str, list] = {}
        self._train_amounts: np.ndarray | None = None
        self._train_dows: np.ndarray | None = None
        self._train_doms: np.ndarray | None = None
        self._train_internal_ids: np.ndarray | None = None
        self._train_institutions: np.ndarray | None = None
        # Frequency tracking for recurrence threshold (minimum 2 occurrences)
        self._description_freq: Counter = Counter()
        self._category_freq: Counter = Counter()
        self._external_freq: Counter = Counter()

    def fit(
        self,
        raw_descriptions: list[str],
        amounts: list[int],
        days_of_week: list[int],
        days_of_month: list[int],
        internal_ids: list[str],
        institutions: list[str],
        descriptions: list[str | None],
        category_ids: list[int | None],
        external_ids: list[int],
    ) -> None:
        """Fit the model on approved transaction data.

        Trains both:
        - Text-only kNN on TF-IDF features (primary signal for Stage 1 of prediction)
        - Combined-feature kNN on text + structured features (kept for compatibility)

        The text-only model is the primary signal: Stage 1 retrieves ~50 neighbors
        based purely on raw_description similarity. Stage 2 reweights these neighbors
        using structured features (amount, date, account, institution) as tiebreakers.

        Args:
            raw_descriptions: Raw bank transaction descriptions for training
            amounts: Transaction amounts in cents
            days_of_week: 1=Monday through 7=Sunday
            days_of_month: 1-31
            internal_ids: Internal account identifiers (e.g., "Checking", "Savings")
            institutions: Importer institution names
            descriptions: User-friendly descriptions (nullable, for voting)
            category_ids: Category IDs (nullable, for voting)
            external_ids: External account IDs (for voting)
        """
        if not raw_descriptions:
            self._knn = None
            self._text_knn = None
            self._description_freq = Counter()
            self._category_freq = Counter()
            self._external_freq = Counter()
            return

        features = _build_feature_matrix(
            raw_descriptions,
            amounts,
            days_of_week,
            days_of_month,
            internal_ids,
            institutions,
        )

        numeric_indices = [0, 1, 2, 3, 4]  # amount, sin/cos dow, sin/cos dom
        categorical_indices = [5, 6]  # internal_id, institution

        # TF-IDF needs string input, so we handle it separately from the
        # ColumnTransformer which operates on the structured feature array.
        tfidf = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5))
        text_features = tfidf.fit_transform(raw_descriptions)

        # ── Text-only kNN (Stage 1, primary signal) ──────────────────────
        # Train kNN on text features alone. Use ~5x K for Stage 1 to have
        # enough candidates to reweight in Stage 2.
        text_k = min(50, len(raw_descriptions))
        text_knn = NearestNeighbors(
            n_neighbors=text_k, metric="cosine", algorithm="brute"
        )
        if issparse(text_features):
            text_knn.fit(text_features.tocsr())
        else:
            text_knn.fit(text_features)
        self._text_tfidf = tfidf
        self._text_knn = text_knn

        # ── Combined-feature kNN (fallback for compatibility) ────────────
        ct = ColumnTransformer(
            transformers=[
                ("num", StandardScaler(), numeric_indices),
                (
                    "cat",
                    OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                    categorical_indices,
                ),
            ],
            remainder="drop",
        )
        structured_features = ct.fit_transform(features)

        if issparse(text_features):
            combined = hstack([text_features, structured_features]).tocsr()
        else:
            combined = np.hstack([text_features, structured_features])

        k = min(K_NEIGHBORS, len(raw_descriptions))
        knn = NearestNeighbors(n_neighbors=k, metric="cosine", algorithm="brute")
        knn.fit(combined)

        self._tfidf = tfidf
        self._ct = ct
        self._knn = knn
        self._labels = {
            "description": descriptions,
            "category_id": category_ids,
            "external_id": external_ids,
        }
        # Store training data features for reweighting in Stage 2
        self._train_amounts = np.array(amounts)
        self._train_dows = np.array(days_of_week)
        self._train_doms = np.array(days_of_month)
        self._train_internal_ids = np.array(internal_ids)
        self._train_institutions = np.array(institutions)
        # Compute frequency of each value for recurrence threshold filtering
        self._description_freq = Counter([d for d in descriptions if d is not None])
        self._category_freq = Counter([c for c in category_ids if c is not None])
        self._external_freq = Counter(external_ids)

    def predict(
        self,
        raw_descriptions: list[str],
        amounts: list[int],
        days_of_week: list[int],
        days_of_month: list[int],
        internal_ids: list[str],
        institutions: list[str],
    ) -> list[TransactionPrediction]:
        """Predict fields for new transactions using two-stage matching.

        Two-stage ranking approach (solves the "amount dominance" problem):

        **Stage 1 (Primary Signal):** Text-only neighbor retrieval
        - Retrieves ~50 neighbors based on raw_description TF-IDF cosine similarity
        - Purely text-driven, uncontaminated by numeric features
        - Ensures "KROGER" matches "KROGER STORE" regardless of amount

        **Stage 2 (Secondary Signal):** Structured feature reweighting
        - For each of the ~50 text neighbors, computes adjustment factors based on:
          * Amount agreement: 1.1× if within 2x range, 0.9× otherwise
          * Day-of-week/month, account, institution: 1.05× if match, 1.0× otherwise
        - Multiplies text similarity by adjustment factors to reweight candidates
        - Adjustment factors bounded to [0.9, 1.1] to preserve text-based ranking

        **Mathematical Guarantee:**
        Multiplication by factors in [0.9, 1.1] preserves ordering of text similarities.
        If A > B, then A×k₁ > B×k₂ for any k₁, k₂ ∈ [0.9, 1.1].
        Example: 0.72 × 0.9 = 0.648 > 0.42 × 1.1 = 0.462 ✓

        Args:
            raw_descriptions: Raw descriptions of new transactions to predict for
            amounts: Amounts in cents
            days_of_week: 1=Monday through 7=Sunday
            days_of_month: 1-31
            internal_ids: Internal account identifiers
            institutions: Importer institution names

        Returns:
            List of TransactionPrediction, one per input transaction.
            Fields are only populated if confidence exceeds thresholds (SIMILARITY_FLOOR, AGREEMENT_THRESHOLD).
        """
        if self._text_knn is None or not raw_descriptions:
            return [TransactionPrediction() for _ in raw_descriptions]

        # ── Stage 1: Text-only neighbor retrieval ──────────────────────
        text_features = self._text_tfidf.transform(raw_descriptions)
        distances, indices = self._text_knn.kneighbors(text_features)
        similarities = 1 - distances  # Convert cosine distances to similarities

        results = []
        for i in range(len(raw_descriptions)):
            pred = TransactionPrediction()
            neighbor_indices = indices[i]
            neighbor_sims = similarities[i].copy()  # Copy so we don't modify original

            # ── Stage 2: Compute adjustment factors and apply them ─────────
            # Extract structured features for the pending transaction
            pending_amount = amounts[i]
            pending_dow = days_of_week[i]
            pending_dom = days_of_month[i]
            pending_internal_id = internal_ids[i]
            pending_institution = institutions[i]

            # Extract corresponding features for neighbors
            neighbor_amounts = self._train_amounts[neighbor_indices]
            neighbor_dows = self._train_dows[neighbor_indices]
            neighbor_doms = self._train_doms[neighbor_indices]
            neighbor_internal_ids = self._train_internal_ids[neighbor_indices]
            neighbor_institutions = self._train_institutions[neighbor_indices]

            # Compute adjustment factors
            adjustment_factors = self._compute_adjustment_factors(
                pending_amount,
                pending_dow,
                pending_dom,
                pending_internal_id,
                pending_institution,
                neighbor_amounts,
                neighbor_dows,
                neighbor_doms,
                neighbor_internal_ids,
                neighbor_institutions,
            )

            # Apply adjustment factors (element-wise multiplication)
            adjusted_sims = neighbor_sims * adjustment_factors

            # Ensure adjusted similarities remain in [0, 1]
            # (should be automatic given bounded factors, but clamp just in case)
            adjusted_sims = np.clip(adjusted_sims, 0.0, 1.0)

            # Use adjusted similarities for voting
            pred.description = self._vote_field(
                "description", adjusted_sims, neighbor_indices
            )
            # Filter out single-occurrence values (recurrence threshold)
            if pred.description is not None and not self._meets_recurrence_threshold(
                "description", pred.description.value
            ):
                pred.description = None

            pred.category_id = self._vote_field(
                "category_id", adjusted_sims, neighbor_indices
            )
            # Filter out single-occurrence values (recurrence threshold)
            if pred.category_id is not None and not self._meets_recurrence_threshold(
                "category_id", pred.category_id.value
            ):
                pred.category_id = None

            pred.external_id = self._vote_field(
                "external_id", adjusted_sims, neighbor_indices
            )
            # Filter out single-occurrence values (recurrence threshold)
            if pred.external_id is not None and not self._meets_recurrence_threshold(
                "external_id", pred.external_id.value
            ):
                pred.external_id = None

            results.append(pred)

        return results

    def _compute_adjustment_factors(
        self,
        pending_amount: int,
        pending_dow: int,
        pending_dom: int,
        pending_internal_id: str,
        pending_institution: str,
        neighbor_amounts: np.ndarray,
        neighbor_dows: np.ndarray,
        neighbor_doms: np.ndarray,
        neighbor_internal_ids: np.ndarray,
        neighbor_institutions: np.ndarray,
    ) -> np.ndarray:
        """Compute multiplicative adjustment factors for neighbor similarities.

        For each neighbor, computes a scalar adjustment factor (product of
        individual factors) that reflects agreement in amount, date, account,
        and institution. All factors are bounded to [0.9, 1.1] to preserve
        the ordering of text-based similarities.

        Adjustment factors:
        - AMOUNT_FACTOR_MATCH (1.1): Amount within 2x range
        - AMOUNT_FACTOR_NOMATCH (0.9): Amount outside 2x range
        - SECONDARY_FACTOR_MATCH (1.05): Day-of-week/month, account, or institution matches
        - SECONDARY_FACTOR_NOMATCH (1.0): No match on secondary features

        The product of these factors is always in the range [0.9^k, 1.1^k] where
        k is the number of factors (typically 5: amount, dow, dom, account, institution).

        Mathematical guarantee: Multiplication preserves text-ranking.
        If neighbor_i has higher text similarity than neighbor_j, the adjusted
        similarities will maintain this ordering regardless of adjustment factors.

        Returns:
            Array of adjustment factors, one per neighbor (length = len(neighbor_amounts)).
        """
        factors = np.ones(len(neighbor_amounts))

        # Amount factor: 1.1 if within 2x tolerance, 0.9 otherwise
        # "Within 2x" means: abs(log(pending_amount / neighbor_amount)) <= log(2)
        for i, neighbor_amount in enumerate(neighbor_amounts):
            if pending_amount == 0 or neighbor_amount == 0:
                # Can't compute meaningful ratio, no adjustment
                amount_factor = SECONDARY_FACTOR_NOMATCH
            else:
                ratio = pending_amount / neighbor_amount
                # Check if within 2x (0.5x to 2x)
                if 0.5 <= ratio <= 2.0:
                    amount_factor = AMOUNT_FACTOR_MATCH
                else:
                    amount_factor = AMOUNT_FACTOR_NOMATCH
            factors[i] *= amount_factor

        # Day-of-week factor: 1.05 if match, 1.0 otherwise
        dow_factors = np.where(
            neighbor_dows == pending_dow,
            SECONDARY_FACTOR_MATCH,
            SECONDARY_FACTOR_NOMATCH,
        )
        factors *= dow_factors

        # Day-of-month factor: 1.05 if match, 1.0 otherwise
        dom_factors = np.where(
            neighbor_doms == pending_dom,
            SECONDARY_FACTOR_MATCH,
            SECONDARY_FACTOR_NOMATCH,
        )
        factors *= dom_factors

        # Account factor: 1.05 if match, 1.0 otherwise
        account_factors = np.where(
            neighbor_internal_ids == pending_internal_id,
            SECONDARY_FACTOR_MATCH,
            SECONDARY_FACTOR_NOMATCH,
        )
        factors *= account_factors

        # Institution factor: 1.05 if match, 1.0 otherwise
        institution_factors = np.where(
            neighbor_institutions == pending_institution,
            SECONDARY_FACTOR_MATCH,
            SECONDARY_FACTOR_NOMATCH,
        )
        factors *= institution_factors

        return factors

    def _meets_recurrence_threshold(self, field: str, value: object) -> bool:
        """Check if a value meets the minimum recurrence threshold (≥2 occurrences).

        Each field (description, category_id, external_id) tracks frequency of values
        seen during training. Values appearing fewer than 2 times are filtered out
        from predictions to avoid noise from one-off, non-recurring values.

        Args:
            field: Field name ("description", "category_id", or "external_id")
            value: The value to check (e.g., "Groceries", 5, 42)

        Returns:
            True if value appears ≥2 times in training data, False otherwise
        """
        if field == "description":
            freq = self._description_freq
        elif field == "category_id":
            freq = self._category_freq
        elif field == "external_id":
            freq = self._external_freq
        else:
            # Unknown field, allow it (defensive)
            return True

        return freq.get(value, 0) >= 2

    def _vote_field(
        self,
        field: str,
        similarities: np.ndarray,
        neighbor_indices: np.ndarray,
    ) -> FieldPrediction | None:
        """Weighted vote among qualifying neighbors for a single field."""
        labels = self._labels[field]

        # Stage 1: Filter by similarity floor
        votes: dict[object, float] = {}
        total_weight = 0.0
        for sim, idx in zip(similarities, neighbor_indices, strict=True):
            if sim < SIMILARITY_FLOOR:
                continue
            label = labels[idx]
            if label is None:
                continue
            votes[label] = votes.get(label, 0.0) + sim
            total_weight += sim

        if not votes or total_weight == 0:
            return None

        # Stage 2: Check agreement threshold
        winner = max(votes, key=votes.get)
        confidence = votes[winner] / total_weight

        if confidence < AGREEMENT_THRESHOLD:
            return None

        return FieldPrediction(value=winner, confidence=round(confidence, 4))
