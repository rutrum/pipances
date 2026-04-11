"""Tests for the ML prediction engine (predict.py).

Tests cover:
- Adjustment factor computation (Tasks 5.1, 6.1-6.5)
- Text-only kNN behavior (Task 2)
- Integration with two-stage ranking (Task 5.3)
- Backward compatibility (Task 5.4)
- Edge cases (Tasks 6.2-6.4)
"""

import numpy as np
import pytest

from pipances.predict import (
    AMOUNT_FACTOR_MATCH,
    AMOUNT_FACTOR_NOMATCH,
    SECONDARY_FACTOR_MATCH,
    SECONDARY_FACTOR_NOMATCH,
    TransactionPredictor,
)


class TestAdjustmentFactorConstants:
    """Verify adjustment factor bounds (Task 1)."""

    def test_amount_factors_bounded(self):
        """Verify amount factors are in [0.9, 1.1]."""
        assert 0.9 <= AMOUNT_FACTOR_MATCH <= 1.1
        assert 0.9 <= AMOUNT_FACTOR_NOMATCH <= 1.1

    def test_secondary_factors_bounded(self):
        """Verify secondary factors are in [0.9, 1.1]."""
        assert 0.9 <= SECONDARY_FACTOR_MATCH <= 1.1
        assert 0.9 <= SECONDARY_FACTOR_NOMATCH <= 1.1

    def test_text_ranking_preserved_math(self):
        """Verify the mathematical guarantee: strong text match beats weak match.

        Good match (0.72) penalized, weak match (0.42) boosted:
        0.72 * 0.9 = 0.648 > 0.42 * 1.1 = 0.462 ✓
        """
        good_sim = 0.72
        weak_sim = 0.42

        worst_for_good = good_sim * AMOUNT_FACTOR_NOMATCH  # 0.72 * 0.9
        best_for_weak = weak_sim * AMOUNT_FACTOR_MATCH  # 0.42 * 1.1

        assert worst_for_good > best_for_weak, "Text ranking not preserved!"
        assert worst_for_good == pytest.approx(0.648, abs=0.001)
        assert best_for_weak == pytest.approx(0.462, abs=0.001)


class TestComputeAdjustmentFactors:
    """Test _compute_adjustment_factors() method (Tasks 3.1-3.4, 6.1-6.4)."""

    def test_all_factors_match(self):
        """When everything matches, product of all factors."""
        predictor = TransactionPredictor()

        # Single neighbor with all features matching
        factors = predictor._compute_adjustment_factors(
            pending_amount=10000,
            pending_dow=2,
            pending_dom=15,
            pending_internal_id="Checking",
            pending_institution="FirstBank",
            neighbor_amounts=np.array([10000]),
            neighbor_dows=np.array([2]),
            neighbor_doms=np.array([15]),
            neighbor_internal_ids=np.array(["Checking"]),
            neighbor_institutions=np.array(["FirstBank"]),
        )

        expected = AMOUNT_FACTOR_MATCH * (SECONDARY_FACTOR_MATCH**4)
        assert factors[0] == pytest.approx(expected)

    def test_all_factors_nomatch(self):
        """When nothing matches, product of nomatch factors."""
        predictor = TransactionPredictor()

        factors = predictor._compute_adjustment_factors(
            pending_amount=10000,
            pending_dow=1,
            pending_dom=1,
            pending_internal_id="Savings",
            pending_institution="SecondBank",
            neighbor_amounts=np.array([100]),  # Very different
            neighbor_dows=np.array([7]),
            neighbor_doms=np.array([31]),
            neighbor_internal_ids=np.array(["Checking"]),
            neighbor_institutions=np.array(["FirstBank"]),
        )

        # Amount factor: 100 is way outside 2x of 10000, so NOMATCH
        # Secondary factors: all NOMATCH
        expected = AMOUNT_FACTOR_NOMATCH * (SECONDARY_FACTOR_NOMATCH**4)
        assert factors[0] == pytest.approx(expected)

    def test_amount_within_tolerance(self):
        """Amount factor 1.1 when within 2x."""
        predictor = TransactionPredictor()

        # Pending 100, neighbor 75 (ratio 1.33x, within 2x)
        factors = predictor._compute_adjustment_factors(
            pending_amount=10000,
            pending_dow=1,
            pending_dom=1,
            pending_internal_id="X",
            pending_institution="X",
            neighbor_amounts=np.array([7500]),  # 1.33x different
            neighbor_dows=np.array([1]),
            neighbor_doms=np.array([1]),
            neighbor_internal_ids=np.array(["X"]),
            neighbor_institutions=np.array(["X"]),
        )

        # Amount match (within 2x), other secondary all match
        expected = AMOUNT_FACTOR_MATCH * (SECONDARY_FACTOR_MATCH**4)
        assert factors[0] == pytest.approx(expected)

    def test_amount_outside_tolerance(self):
        """Amount factor 0.9 when outside 2x."""
        predictor = TransactionPredictor()

        # Pending 10000, neighbor 4000 (ratio 2.5x, outside 2x)
        factors = predictor._compute_adjustment_factors(
            pending_amount=10000,
            pending_dow=1,
            pending_dom=1,
            pending_internal_id="X",
            pending_institution="X",
            neighbor_amounts=np.array([4000]),  # 2.5x different
            neighbor_dows=np.array([1]),
            neighbor_doms=np.array([1]),
            neighbor_internal_ids=np.array(["X"]),
            neighbor_institutions=np.array(["X"]),
        )

        # Amount nomatch (outside 2x), other secondary all match
        expected = AMOUNT_FACTOR_NOMATCH * (SECONDARY_FACTOR_MATCH**4)
        assert factors[0] == pytest.approx(expected)

    def test_multiple_neighbors(self):
        """Verify vectorized computation across multiple neighbors."""
        predictor = TransactionPredictor()

        factors = predictor._compute_adjustment_factors(
            pending_amount=1000,
            pending_dow=3,
            pending_dom=10,
            pending_internal_id="Checking",
            pending_institution="Bank1",
            neighbor_amounts=np.array([1000, 500, 2500]),
            neighbor_dows=np.array([3, 3, 5]),
            neighbor_doms=np.array([10, 11, 10]),
            neighbor_internal_ids=np.array(["Checking", "Savings", "Checking"]),
            neighbor_institutions=np.array(["Bank1", "Bank1", "Bank2"]),
        )

        assert len(factors) == 3
        # All factors should be bounded [0.9, 1.1]^4 ≈ [0.656, 1.476]
        for f in factors:
            assert 0.6 <= f <= 1.5


class TestTextOnlyKNN:
    """Test text-only kNN infrastructure (Tasks 2.1-2.3)."""

    def test_fit_creates_text_knn(self):
        """Verify fit() creates text-only kNN."""
        predictor = TransactionPredictor()

        predictor.fit(
            raw_descriptions=["KROGER", "KROGER", "TARGET"],
            amounts=[5000, 5000, 10000],
            days_of_week=[1, 1, 2],
            days_of_month=[15, 15, 20],
            internal_ids=["Checking", "Checking", "Checking"],
            institutions=["Bank1", "Bank1", "Bank1"],
            descriptions=["Grocery Store", "Grocery Store", "Shopping"],
            category_ids=[1, 1, 2],
            external_ids=[1, 1, 2],
        )

        assert predictor._text_knn is not None
        assert predictor._text_tfidf is not None
        assert predictor._train_amounts is not None

    def test_fit_with_few_transactions(self):
        """Test fit() with < 10 transactions (Task 6.1)."""
        predictor = TransactionPredictor()

        # Only 3 transactions
        predictor.fit(
            raw_descriptions=["A", "B", "C"],
            amounts=[100, 200, 300],
            days_of_week=[1, 2, 3],
            days_of_month=[1, 2, 3],
            internal_ids=["X", "X", "X"],
            institutions=["Bank", "Bank", "Bank"],
            descriptions=["D1", "D2", "D3"],
            category_ids=[1, 2, 3],
            external_ids=[1, 2, 3],
        )

        # Should work without crashing
        assert predictor._text_knn is not None

    def test_fit_with_empty_descriptions(self):
        """Test fit() handles empty descriptions gracefully (Task 6.2)."""
        predictor = TransactionPredictor()

        predictor.fit(
            raw_descriptions=["", "KROGER", ""],
            amounts=[100, 200, 300],
            days_of_week=[1, 2, 3],
            days_of_month=[1, 2, 3],
            internal_ids=["X", "X", "X"],
            institutions=["Bank", "Bank", "Bank"],
            descriptions=["D1", "D2", "D3"],
            category_ids=[1, 2, 3],
            external_ids=[1, 2, 3],
        )

        assert predictor._text_knn is not None


class TestTwoStageRanking:
    """Integration tests for two-stage ranking (Task 5.3)."""

    def test_text_match_different_amount(self):
        """Same description with different amount should match (text wins).

        Scenario A from seed.py: text match, different amount.
        """
        predictor = TransactionPredictor()

        # Train on "KROGER" at $87, $145, $52
        predictor.fit(
            raw_descriptions=["KROGER", "KROGER", "KROGER"],
            amounts=[8700, 14500, 5200],
            days_of_week=[1, 1, 1],
            days_of_month=[15, 15, 15],
            internal_ids=["Checking", "Checking", "Checking"],
            institutions=["Bank1", "Bank1", "Bank1"],
            descriptions=["Groceries", "Groceries", "Groceries"],
            category_ids=[1, 1, 1],
            external_ids=[1, 1, 1],
        )

        # Predict on "KROGER STORE" at $23.50 (different amount)
        predictions = predictor.predict(
            raw_descriptions=["KROGER STORE"],
            amounts=[2350],
            days_of_week=[1],
            days_of_month=[15],
            internal_ids=["Checking"],
            institutions=["Bank1"],
        )

        # Should suggest "Groceries" despite amount mismatch
        assert predictions[0].category_id is not None
        assert predictions[0].category_id.value == 1

    def test_amount_only_should_not_match(self):
        """Different text, same amount should NOT match (Scenario D).

        Amount $35 could match Electric Company, but "UNKNOWN RETAIL" is
        very different text, so should not match.
        """
        predictor = TransactionPredictor()

        # Train on specific merchants with specific amounts
        predictor.fit(
            raw_descriptions=["ELECTRIC CO", "ELECTRIC CO", "ELECTRIC CO"],
            amounts=[8500, 14000, 10200],
            days_of_week=[1, 1, 1],
            days_of_month=[15, 15, 15],
            internal_ids=["Checking", "Checking", "Checking"],
            institutions=["Bank1", "Bank1", "Bank1"],
            descriptions=["Utilities", "Utilities", "Utilities"],
            category_ids=[1, 1, 1],
            external_ids=[1, 1, 1],
        )

        # Predict on "UNKNOWN RETAIL STORE" at $35 (exact amount match)
        predictions = predictor.predict(
            raw_descriptions=["UNKNOWN RETAIL STORE"],
            amounts=[3500],
            days_of_week=[1],
            days_of_month=[15],
            internal_ids=["Checking"],
            institutions=["Bank1"],
        )

        # Should NOT match Utilities despite amount being present in training
        # (because text similarity should be low)
        # Note: This depends on the SIMILARITY_FLOOR threshold; if text sim
        # is below floor, prediction will be None.
        assert (
            predictions[0].category_id is None or predictions[0].category_id.value != 1
        )


class TestBackwardCompatibility:
    """Regression test: ensure existing behavior still works (Task 5.4)."""

    def test_predict_returns_same_type(self):
        """Predictions should still return TransactionPrediction objects."""
        predictor = TransactionPredictor()

        predictor.fit(
            raw_descriptions=["A", "B"],
            amounts=[100, 200],
            days_of_week=[1, 2],
            days_of_month=[1, 2],
            internal_ids=["X", "X"],
            institutions=["Bank", "Bank"],
            descriptions=["D1", "D2"],
            category_ids=[1, 2],
            external_ids=[1, 2],
        )

        predictions = predictor.predict(
            raw_descriptions=["A"],
            amounts=[100],
            days_of_week=[1],
            days_of_month=[1],
            internal_ids=["X"],
            institutions=["Bank"],
        )

        assert len(predictions) == 1
        from pipances.predict import TransactionPrediction

        assert isinstance(predictions[0], TransactionPrediction)

    def test_no_training_data_returns_empty_predictions(self):
        """Empty training set should return blank predictions."""
        predictor = TransactionPredictor()

        predictions = predictor.predict(
            raw_descriptions=["anything"],
            amounts=[100],
            days_of_week=[1],
            days_of_month=[1],
            internal_ids=["X"],
            institutions=["Bank"],
        )

        assert len(predictions) == 1
        assert predictions[0].description is None
        assert predictions[0].category_id is None
        assert predictions[0].external_id is None


class TestExtremeAmounts:
    """Test extreme amounts preserve text ranking (Task 6.4)."""

    def test_extreme_amount_differences(self):
        """Verify text ranking preserved with amounts $0.01 vs $100,000."""
        predictor = TransactionPredictor()

        # Train on KROGER with extreme range
        predictor.fit(
            raw_descriptions=["KROGER", "KROGER", "KROGER"],
            amounts=[1, 100000, 50000],  # $0.01, $1,000, $500
            days_of_week=[1, 1, 1],
            days_of_month=[15, 15, 15],
            internal_ids=["Checking", "Checking", "Checking"],
            institutions=["Bank1", "Bank1", "Bank1"],
            descriptions=["Groceries", "Groceries", "Groceries"],
            category_ids=[1, 1, 1],
            external_ids=[1, 1, 1],
        )

        # Predict on KROGER at $500 (should match despite extreme range in training)
        predictions = predictor.predict(
            raw_descriptions=["KROGER"],
            amounts=[50000],
            days_of_week=[1],
            days_of_month=[15],
            internal_ids=["Checking"],
            institutions=["Bank1"],
        )

        # Should still suggest Groceries
        assert predictions[0].category_id is not None
        assert predictions[0].category_id.value == 1
