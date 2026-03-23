"""ML prediction engine for transaction field suggestions.

Uses TF-IDF character n-grams on raw_description combined with numeric
and categorical features via a ColumnTransformer + kNN pipeline.
"""

from __future__ import annotations

import math
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
        self._labels: dict[str, list] = {}

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
        """Fit the model on approved transaction data."""
        if not raw_descriptions:
            self._knn = None
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

    def predict(
        self,
        raw_descriptions: list[str],
        amounts: list[int],
        days_of_week: list[int],
        days_of_month: list[int],
        internal_ids: list[str],
        institutions: list[str],
    ) -> list[TransactionPrediction]:
        """Predict fields for new transactions. Returns one prediction per input."""
        if self._knn is None or not raw_descriptions:
            return [TransactionPrediction() for _ in raw_descriptions]

        features = _build_feature_matrix(
            raw_descriptions,
            amounts,
            days_of_week,
            days_of_month,
            internal_ids,
            institutions,
        )

        text_features = self._tfidf.transform(raw_descriptions)
        structured_features = self._ct.transform(features)

        if issparse(text_features):
            combined = hstack([text_features, structured_features]).tocsr()
        else:
            combined = np.hstack([text_features, structured_features])

        distances, indices = self._knn.kneighbors(combined)

        results = []
        for i in range(len(raw_descriptions)):
            pred = TransactionPrediction()
            # Convert cosine distances to similarities
            similarities = 1 - distances[i]
            neighbor_indices = indices[i]

            pred.description = self._vote_field(
                "description", similarities, neighbor_indices
            )
            pred.category_id = self._vote_field(
                "category_id", similarities, neighbor_indices
            )
            pred.external_id = self._vote_field(
                "external_id", similarities, neighbor_indices
            )
            results.append(pred)

        return results

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
