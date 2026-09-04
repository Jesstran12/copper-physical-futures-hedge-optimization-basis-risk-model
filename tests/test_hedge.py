"""Tests for the hedge-math baselines (Phase 2).

These tests define the contract for src/copper_hedge/hedge.py. Do not edit
them — implement the module until they pass. All expected values are
hand-computed; sample variance uses ddof=1 (the pandas default).
"""

import pandas as pd
import pytest

from copper_hedge.hedge import (
    hedged_changes,
    naive_hedge_report,
    price_changes,
    variance_reduction,
)


def _series(values, name="s"):
    dates = pd.bdate_range("2024-01-01", periods=len(values))
    return pd.Series(values, index=dates, name=name, dtype=float)


class TestPriceChanges:
    def test_simple_differences(self):
        prices = _series([1.0, 2.0, 4.0, 7.0])
        assert price_changes(prices).tolist() == [1.0, 2.0, 3.0]

    def test_first_day_is_dropped(self):
        prices = _series([1.0, 2.0, 4.0])
        changes = price_changes(prices)
        assert len(changes) == 2
        assert list(changes.index) == list(prices.index[1:])

    def test_changes_are_dollars_not_returns(self):
        # A move from 100 to 110 is +10 dollars, not +0.10 (10%).
        prices = _series([100.0, 110.0])
        assert price_changes(prices).iloc[0] == pytest.approx(10.0)


class TestHedgedChanges:
    def test_perfect_one_to_one_hedge_nets_to_zero(self):
        ds = _series([1.0, -2.0, 0.5])
        assert hedged_changes(ds, ds, 1.0).tolist() == [0.0, 0.0, 0.0]

    def test_hedge_ratio_scales_the_futures_leg(self):
        ds = _series([1.0, 2.0])
        df_ = _series([0.5, 1.0])
        assert hedged_changes(ds, df_, 2.0).tolist() == [0.0, 0.0]

    def test_zero_ratio_is_just_the_unhedged_position(self):
        ds = _series([1.0, -1.0])
        df_ = _series([5.0, 5.0])
        assert hedged_changes(ds, df_, 0.0).tolist() == [1.0, -1.0]


class TestVarianceReduction:
    def test_perfect_hedge_removes_all_variance(self):
        unhedged = _series([1.0, -1.0, 2.0, -2.0])
        hedged = _series([0.0, 0.0, 0.0, 0.0])
        assert variance_reduction(unhedged, hedged) == pytest.approx(1.0)

    def test_useless_hedge_removes_nothing(self):
        unhedged = _series([1.0, -1.0, 1.0, -1.0])
        assert variance_reduction(unhedged, unhedged) == pytest.approx(0.0)

    def test_hand_computed_reduction(self):
        # Var([1,-1,1,-1]) = 4/3 and Var([.5,-.5,.5,-.5]) = 1/3 -> 75% reduction.
        unhedged = _series([1.0, -1.0, 1.0, -1.0])
        hedged = _series([0.5, -0.5, 0.5, -0.5])
        assert variance_reduction(unhedged, hedged) == pytest.approx(0.75)

    def test_bad_hedge_gives_negative_reduction(self):
        # Hedged swings twice as big: Var goes 4/3 -> 16/3, reduction = -3.
        unhedged = _series([1.0, -1.0, 1.0, -1.0])
        hedged = _series([2.0, -2.0, 2.0, -2.0])
        assert variance_reduction(unhedged, hedged) == pytest.approx(-3.0)

    def test_variance_is_around_the_mean_not_raw_magnitude(self):
        # A constant drift has zero variance even though every change is 2.0.
        unhedged = _series([3.0, -3.0, 3.0, -3.0])
        hedged = _series([2.0, 2.0, 2.0, 2.0])
        assert variance_reduction(unhedged, hedged) == pytest.approx(1.0)


class TestNaiveHedgeReport:
    def test_hand_computed_report(self):
        ds = _series([1.0, -1.0, 1.0, -1.0])
        df_ = _series([0.5, -0.5, 0.5, -0.5])
        report = naive_hedge_report(ds, df_)
        # ddof=1: Var(ds) = 4/3 (not 1.0 — that would be ddof=0).
        assert report["unhedged_variance"] == pytest.approx(4.0 / 3.0)
        assert report["hedged_variance"] == pytest.approx(1.0 / 3.0)
        assert report["variance_reduction"] == pytest.approx(0.75)
