"""Tests for the in-sample optimal hedge (Phase 3).

These tests define the contract for the Phase 3 additions to
src/copper_hedge/hedge.py. Do not edit them — implement the module until
they pass. All expected values are hand-computed (the arithmetic is in the
comments); sample moments use ddof=1 (the pandas default).

The two facts this file exists to enforce:
1. h* is exactly Cov(dS, dF) / Var(dF) — the OLS slope;
2. the effectiveness achieved at h* is exactly the regression R-squared.
"""

import numpy as np
import pandas as pd
import pytest

from copper_hedge.hedge import (
    exclude_roll_days,
    hedged_changes,
    in_sample_r_squared,
    optimal_hedge_ratio,
    optimal_hedge_report,
    variance_reduction,
)


def _series(values, name="s"):
    dates = pd.bdate_range("2024-01-01", periods=len(values))
    return pd.Series(values, index=dates, name=name, dtype=float)


def _noisy_pair(n=250, beta=0.8, noise=0.5, seed=42):
    """Correlated synthetic changes: dS = beta * dF + noise (fixed seed)."""
    rng = np.random.default_rng(seed)
    df_ = _series(rng.normal(0.0, 1.0, n), name="dF")
    ds = _series(beta * df_.to_numpy() + rng.normal(0.0, noise, n), name="dS")
    return ds, df_


# Shared hand-computed example, used across classes:
#   dF = [1, 2, 3, 4]   mean 2.5, deviations [-1.5, -0.5, 0.5, 1.5]
#   dS = [2, 4, 5, 9]   mean 5.0, deviations [-3, -1, 0, 4]
#   Cov  = (4.5 + 0.5 + 0 + 6) / 3            = 11/3
#   VarF = (2.25 + 0.25 + 0.25 + 2.25) / 3    = 5/3
#   VarS = (9 + 1 + 0 + 16) / 3               = 26/3
#   h*   = Cov/VarF = 11/5                    = 2.2
#   R^2  = Cov^2/(VarS*VarF) = (121/9)/(130/9) = 121/130
HAND_DF = [1.0, 2.0, 3.0, 4.0]
HAND_DS = [2.0, 4.0, 5.0, 9.0]


class TestOptimalHedgeRatio:
    def test_hand_computed_cov_over_var(self):
        # See the arithmetic above: h* = (11/3) / (5/3) = 2.2 exactly.
        ds, df_ = _series(HAND_DS), _series(HAND_DF)
        assert optimal_hedge_ratio(ds, df_) == pytest.approx(2.2)

    def test_perfectly_proportional_changes_recover_the_slope(self):
        df_ = _series([1.0, -2.0, 3.0, -1.0])
        ds = 0.5 * df_
        assert optimal_hedge_ratio(ds, df_) == pytest.approx(0.5)

    def test_uncorrelated_changes_give_zero(self):
        # Both series have mean 0 and the cross-products cancel:
        # (1)(1) + (-1)(1) + (1)(-1) + (-1)(-1) = 0 -> Cov = 0 -> h* = 0.
        ds = _series([1.0, 1.0, -1.0, -1.0])
        df_ = _series([1.0, -1.0, 1.0, -1.0])
        assert optimal_hedge_ratio(ds, df_) == pytest.approx(0.0)

    def test_constant_added_to_spot_changes_does_not_move_h(self):
        # A constant drift in dS shifts the mean, not the covariance —
        # that is what the OLS intercept absorbs.
        ds, df_ = _series(HAND_DS), _series(HAND_DF)
        drifted = ds + 0.7
        assert optimal_hedge_ratio(drifted, df_) == pytest.approx(2.2)

    def test_returns_a_plain_float(self):
        ds, df_ = _noisy_pair()
        assert isinstance(optimal_hedge_ratio(ds, df_), float)


class TestInSampleRSquared:
    def test_perfectly_proportional_changes_score_one(self):
        df_ = _series([1.0, -2.0, 3.0, -1.0])
        assert in_sample_r_squared(2.0 * df_, df_) == pytest.approx(1.0)

    def test_hand_computed_r_squared(self):
        # See the arithmetic above: R^2 = 121/130.
        ds, df_ = _series(HAND_DS), _series(HAND_DF)
        assert in_sample_r_squared(ds, df_) == pytest.approx(121.0 / 130.0)

    def test_uncorrelated_changes_score_zero(self):
        ds = _series([1.0, 1.0, -1.0, -1.0])
        df_ = _series([1.0, -1.0, 1.0, -1.0])
        assert in_sample_r_squared(ds, df_) == pytest.approx(0.0)

    def test_inverse_relationship_still_scores_one(self):
        # R^2 measures co-movement, not direction: a perfectly inverse
        # pair is perfectly hedgeable too (h* just comes out negative).
        df_ = _series([1.0, -2.0, 3.0, -1.0])
        assert in_sample_r_squared(-1.0 * df_, df_) == pytest.approx(1.0)


class TestExcludeRollDays:
    def test_flagged_days_are_dropped_and_the_rest_survive_in_order(self):
        changes = _series([0.1, 0.2, 0.3, 0.4, 0.5])
        flags = pd.Series(
            [False, True, False, True, False], index=changes.index
        )
        kept = exclude_roll_days(changes, flags)
        assert kept.tolist() == [0.1, 0.3, 0.5]
        assert list(kept.index) == [
            changes.index[0], changes.index[2], changes.index[4]
        ]

    def test_no_flags_set_returns_everything(self):
        changes = _series([0.1, 0.2, 0.3])
        flags = pd.Series(False, index=changes.index)
        assert exclude_roll_days(changes, flags).equals(changes)

    def test_flags_on_a_superset_of_dates_are_looked_up_by_date(self):
        # Flags computed on the full history must still apply to a subset
        # of it (e.g. changes restricted to one year).
        full = _series([0.1, 0.2, 0.3, 0.4, 0.5, 0.6])
        flags = pd.Series(
            [False, False, True, False, True, False], index=full.index
        )
        subset = full.iloc[2:5]  # dates 3..5, flags True/False/True
        kept = exclude_roll_days(subset, flags)
        assert kept.tolist() == [0.4]

    def test_dates_missing_from_flags_are_kept(self):
        # A date the flag series has never heard of is not a roll day.
        changes = _series([0.1, 0.2, 0.3, 0.4])
        flags = pd.Series([True], index=[changes.index[1]])
        kept = exclude_roll_days(changes, flags)
        assert kept.tolist() == [0.1, 0.3, 0.4]


class TestOptimalHedgeReport:
    def test_report_has_exactly_the_documented_keys_as_floats(self):
        ds, df_ = _noisy_pair()
        report = optimal_hedge_report(ds, df_)
        assert set(report) == {
            "hedge_ratio",
            "r_squared",
            "unhedged_variance",
            "hedged_variance",
            "effectiveness",
        }
        assert all(isinstance(v, float) for v in report.values())

    def test_hand_computed_report(self):
        # From the shared example: h* = 2.2, R^2 = 121/130, VarS = 26/3.
        # Hedged changes at h*: [2-2.2, 4-4.4, 5-6.6, 9-8.8]
        #                     = [-0.2, -0.4, -1.6, 0.2], mean -0.5,
        # deviations [0.3, 0.1, -1.1, 0.7], sum of squares 1.8 -> Var 0.6.
        ds, df_ = _series(HAND_DS), _series(HAND_DF)
        report = optimal_hedge_report(ds, df_)
        assert report["hedge_ratio"] == pytest.approx(2.2)
        assert report["r_squared"] == pytest.approx(121.0 / 130.0)
        assert report["unhedged_variance"] == pytest.approx(26.0 / 3.0)
        assert report["hedged_variance"] == pytest.approx(0.6)
        assert report["effectiveness"] == pytest.approx(121.0 / 130.0)

    def test_effectiveness_equals_r_squared_identity(self):
        # THE Phase 3 identity: in-sample effectiveness at h* IS the
        # regression R^2. One is computed from variances, the other from a
        # correlation — if they diverge, the math is wrong.
        ds, df_ = _noisy_pair()
        report = optimal_hedge_report(ds, df_)
        assert report["effectiveness"] == pytest.approx(
            report["r_squared"], rel=1e-12
        )

    def test_no_other_ratio_beats_h_star(self):
        # "Minimum-variance" is a promise: any other ratio must hedge
        # no better than h*.
        ds, df_ = _noisy_pair()
        h_star = optimal_hedge_ratio(ds, df_)
        best = optimal_hedge_report(ds, df_)["effectiveness"]
        for h in [0.0, 0.5 * h_star, h_star - 0.1, h_star + 0.1, 1.0]:
            rival = variance_reduction(ds, hedged_changes(ds, df_, h))
            assert best >= rival - 1e-12

    def test_perfectly_hedgeable_pair_reports_full_effectiveness(self):
        df_ = _series([1.0, -2.0, 3.0, -1.0])
        report = optimal_hedge_report(0.5 * df_, df_)
        assert report["effectiveness"] == pytest.approx(1.0)
        assert report["hedged_variance"] == pytest.approx(0.0, abs=1e-15)
