"""Tests for the basis analysis (Phase 6): the spot-futures gap and its risk.

These tests define the contract for src/copper_hedge/basis.py. Do not edit
them — implement the module until they pass. All expected values are
hand-computed (the arithmetic is in the comments); sample moments use
ddof=1 (the pandas default).

The two facts this file exists to enforce:

1. THE IDENTITY: a 1:1 hedger's residual P&L is the basis change,
   identically. db = dS - dF is the same series as hedged_changes at
   hedge_ratio 1, and window_pnl at hedge_ratio 1 must return a hedged
   P&L equal to the basis move to the last bit. "Basis risk is the risk
   a hedge cannot remove" is an equation, not a slogan, and the tests
   treat it as one.

2. THE CONVENTIONS CARRY OVER: basis-change statistics exclude
   roll-flagged days (a splice jump pollutes db exactly as it pollutes
   dF), while basis LEVEL statistics use every day — the level is a real
   price difference on every date. Nothing in this phase is rolling or
   expanding, so there is no lookahead surface; the identity tests above
   are the corresponding guard.
"""

import numpy as np
import pandas as pd
import pytest

from copper_hedge.basis import (
    basis_report,
    basis_series,
    residual_risk_report,
    window_pnl,
)
from copper_hedge.hedge import (
    hedged_changes,
    in_sample_r_squared,
    price_changes,
)


def _daily(values, start="2024-01-01"):
    """A float Series on consecutive business days (2024-01-01 is a Monday)."""
    dates = pd.bdate_range(start, periods=len(values))
    return pd.Series(values, index=dates, dtype=float)


def _random_walk_pair(n=300, seed=7):
    """Two loosely related random-walk price series on business days."""
    rng = np.random.default_rng(seed)
    df_daily = rng.normal(0.0, 1.0, n)
    ds_daily = 0.6 * df_daily + rng.normal(0.0, 0.5, n)
    futures = _daily(50.0 + np.cumsum(df_daily))
    spot = _daily(50.0 + np.cumsum(ds_daily))
    return spot, futures


class TestBasisSeries:
    def test_hand_computed_subtraction_on_the_shared_index(self):
        # b = S - F elementwise: [5-4, 8-5, 9-7, 13-7] = [1, 3, 2, 6].
        spot = _daily([5.0, 8.0, 9.0, 13.0])
        futures = _daily([4.0, 5.0, 7.0, 7.0])
        basis = basis_series(spot, futures)
        assert basis.tolist() == [1.0, 3.0, 2.0, 6.0]
        assert list(basis.index) == list(spot.index)

    def test_futures_above_spot_gives_negative_basis(self):
        # The squeeze/tariff signature: COMEX above LME cash means b < 0.
        spot = _daily([4.0, 4.1])
        futures = _daily([5.0, 5.3])
        basis = basis_series(spot, futures)
        assert basis.tolist() == [-1.0, pytest.approx(-1.2)]

    def test_basis_changes_are_the_naive_hedgers_pnl_identically(self):
        # THE identity: db = dS - dF = hedged_changes(dS, dF, 1.0). Same
        # series, same index, same values to the last bit.
        spot, futures = _random_walk_pair()
        db = price_changes(basis_series(spot, futures))
        naive = hedged_changes(
            price_changes(spot), price_changes(futures), hedge_ratio=1.0
        )
        pd.testing.assert_series_equal(db, naive)


# Shared hand-computed example (ddof=1 throughout):
#   S = [5, 8, 9, 13]   F = [4, 5, 7, 7]   ->   b = [1, 3, 2, 6]
#
#   Level stats (all 4 days):
#     mean = 3; devs [-2, 0, -1, 3]; sum sq = 14; Var = 14/3
#     std = sqrt(14/3); min = 1; max = 6
#   Changes: db = [2, -1, 4] (labeled days 2, 3, 4)
#     mean = 5/3; devs [1/3, -8/3, 7/3]; sum sq = 114/9 = 38/3
#     Var = (38/3)/2 = 19/3; std = sqrt(19/3)
HAND_S = [5.0, 8.0, 9.0, 13.0]
HAND_F = [4.0, 5.0, 7.0, 7.0]


class TestBasisReport:
    def _hand_inputs(self):
        spot = _daily(HAND_S)
        futures = _daily(HAND_F)
        no_flags = pd.Series(False, index=spot.index)
        return spot, futures, no_flags

    def test_report_has_exactly_the_documented_keys_as_floats(self):
        spot, futures, flags = self._hand_inputs()
        report = basis_report(spot, futures, flags)
        assert set(report) == {
            "n_days",
            "mean_basis",
            "std_basis",
            "min_basis",
            "max_basis",
            "n_delta_obs",
            "std_delta_basis",
        }
        assert all(isinstance(v, float) for v in report.values())

    def test_hand_computed_level_and_change_stats(self):
        # See the arithmetic above the class.
        spot, futures, flags = self._hand_inputs()
        report = basis_report(spot, futures, flags)
        assert report["n_days"] == pytest.approx(4.0)
        assert report["mean_basis"] == pytest.approx(3.0)
        assert report["std_basis"] == pytest.approx((14.0 / 3.0) ** 0.5)
        assert report["min_basis"] == pytest.approx(1.0)
        assert report["max_basis"] == pytest.approx(6.0)
        assert report["n_delta_obs"] == pytest.approx(3.0)
        assert report["std_delta_basis"] == pytest.approx((19.0 / 3.0) ** 0.5)

    def test_roll_flagged_days_leave_the_change_stats_only(self):
        # Flag day 3 (Wednesday 2024-01-03): the db observation labeled
        # that day (2 - 3 = -1) drops, leaving db = [2, 4]:
        #   mean = 3; devs [-1, 1]; Var = 2/1 = 2; std = sqrt(2).
        spot, futures, flags = self._hand_inputs()
        flags.loc["2024-01-03"] = True
        report = basis_report(spot, futures, flags)
        assert report["n_delta_obs"] == pytest.approx(2.0)
        assert report["std_delta_basis"] == pytest.approx(2.0**0.5)

    def test_level_stats_use_every_day_even_when_flags_exist(self):
        # Same flagged input: the LEVEL statistics must not move — a roll
        # splice pollutes the change, not the validity of the day's basis.
        spot, futures, flags = self._hand_inputs()
        flags.loc["2024-01-03"] = True
        report = basis_report(spot, futures, flags)
        assert report["n_days"] == pytest.approx(4.0)
        assert report["mean_basis"] == pytest.approx(3.0)
        assert report["std_basis"] == pytest.approx((14.0 / 3.0) ** 0.5)

    def test_report_is_consistent_with_its_building_blocks(self):
        # The report must be exactly: basis_series, then level stats on all
        # days and std of the roll-excluded price_changes — no hidden extras.
        spot, futures = _random_walk_pair(n=200, seed=3)
        flags = pd.Series(False, index=spot.index)
        flags.iloc[[40, 90, 150]] = True
        report = basis_report(spot, futures, flags)

        basis = basis_series(spot, futures)
        db = price_changes(basis)
        db_kept = db[~flags.reindex(db.index).fillna(False).astype(bool)]
        assert report["n_days"] == pytest.approx(float(len(basis)))
        assert report["mean_basis"] == pytest.approx(basis.mean())
        assert report["std_basis"] == pytest.approx(basis.std())
        assert report["min_basis"] == pytest.approx(basis.min())
        assert report["max_basis"] == pytest.approx(basis.max())
        assert report["n_delta_obs"] == pytest.approx(float(len(db_kept)))
        assert report["std_delta_basis"] == pytest.approx(db_kept.std())


class TestResidualRiskReport:
    # Shared hand-computed example (ddof=1 throughout):
    #   dS = [2, 1, 4, 3]   dF = [1, 2, 3, 4]
    #   means 2.5 / 2.5; devs S [-.5, -1.5, 1.5, .5], F [-1.5, -.5, .5, 1.5]
    #   Cov = (.75 + .75 + .75 + .75)/3 = 1;  Var(dF) = Var(dS) = 5/3
    #   h* = 1 / (5/3) = 0.6;  corr = 1 / (5/3) = 3/5, so R^2 = 9/25 = 0.36
    #   residual = dS - 0.6*dF = [1.4, -0.2, 2.2, 0.6]; mean 1.0
    #     devs [.4, -1.2, 1.2, -.4]; sum sq 3.2; Var = 3.2/3 = 16/15
    #     (check: (1 - R^2) * Var(dS) = (16/25)(5/3) = 16/15)
    #   db = dS - dF = [1, -1, 1, -1]; mean 0; Var = 4/3
    #   share = (4/3) / (16/15) = 20/16 = 1.25
    def _hand_changes(self):
        return _daily([2.0, 1.0, 4.0, 3.0]), _daily([1.0, 2.0, 3.0, 4.0])

    def test_report_has_exactly_the_documented_keys_as_floats(self):
        ds, df_ = self._hand_changes()
        report = residual_risk_report(ds, df_)
        assert set(report) == {
            "hedge_ratio",
            "unhedged_variance",
            "residual_variance",
            "residual_std",
            "basis_change_variance",
            "basis_change_std",
            "basis_share_of_residual",
        }
        assert all(isinstance(v, float) for v in report.values())

    def test_hand_computed_linkage_numbers(self):
        # See the arithmetic above.
        ds, df_ = self._hand_changes()
        report = residual_risk_report(ds, df_)
        assert report["hedge_ratio"] == pytest.approx(0.6)
        assert report["unhedged_variance"] == pytest.approx(5.0 / 3.0)
        assert report["residual_variance"] == pytest.approx(16.0 / 15.0)
        assert report["residual_std"] == pytest.approx((16.0 / 15.0) ** 0.5)
        assert report["basis_change_variance"] == pytest.approx(4.0 / 3.0)
        assert report["basis_change_std"] == pytest.approx((4.0 / 3.0) ** 0.5)
        assert report["basis_share_of_residual"] == pytest.approx(1.25)

    def test_basis_change_variance_equals_the_naive_hedged_variance(self):
        # The identity again, through the report: the basis-change numbers
        # must equal the variance/std of a 1:1 hedge computed independently.
        spot, futures = _random_walk_pair(seed=19)
        ds, df_ = price_changes(spot), price_changes(futures)
        report = residual_risk_report(ds, df_)
        naive = hedged_changes(ds, df_, hedge_ratio=1.0)
        assert report["basis_change_variance"] == pytest.approx(
            float(naive.var()), rel=1e-12
        )
        assert report["basis_change_std"] == pytest.approx(
            float(naive.std()), rel=1e-12
        )

    def test_residual_variance_obeys_the_one_minus_r_squared_identity(self):
        # At h = h*, Var(residual) = (1 - R^2) * Var(dS) — the same algebra
        # behind Phase 3's e = R^2 identity, seen from the leftover side.
        spot, futures = _random_walk_pair(seed=23)
        ds, df_ = price_changes(spot), price_changes(futures)
        report = residual_risk_report(ds, df_)
        expected = (1.0 - in_sample_r_squared(ds, df_)) * float(ds.var())
        assert report["residual_variance"] == pytest.approx(expected, rel=1e-12)

    def test_attenuated_hedge_leaves_less_than_the_full_basis_wiggle(self):
        # dS = 0.5*dF + small noise: the fitted h* ~ 0.5, the optimal
        # residual is ~ the noise, but the 1:1 basis wiggle keeps the
        # unhedged half of dF — so the share comes out far above 1. This is
        # the daily attenuation story the report exists to quantify.
        rng = np.random.default_rng(31)
        df_ = _daily(rng.normal(0.0, 1.0, 500))
        ds = 0.5 * df_ + _daily(rng.normal(0.0, 0.1, 500))
        report = residual_risk_report(ds, df_)
        assert report["hedge_ratio"] == pytest.approx(0.5, abs=0.05)
        assert report["basis_share_of_residual"] > 5.0


class TestWindowPnl:
    # Five business days 2024-01-01 (Mon) .. 2024-01-05 (Fri):
    #   S = [10, 11, 12, 13, 15]   F = [8, 9, 11, 10, 12]
    def _prices(self):
        return _daily([10.0, 11.0, 12.0, 13.0, 15.0]), _daily(
            [8.0, 9.0, 11.0, 10.0, 12.0]
        )

    def test_report_has_exactly_the_documented_keys_as_floats(self):
        spot, futures = self._prices()
        report = window_pnl(spot, futures, 0.5, "2024-01-01", "2024-01-05")
        assert set(report) == {
            "n_days",
            "spot_start",
            "spot_end",
            "futures_start",
            "futures_end",
            "spot_move",
            "futures_move",
            "basis_move",
            "unhedged_pnl_per_lb",
            "futures_leg_pnl_per_lb",
            "hedged_pnl_per_lb",
        }
        assert all(isinstance(v, float) for v in report.values())

    def test_hand_computed_window_at_half_hedge(self):
        # Window Tue..Fri, h = 0.5: spot 11 -> 15 (move 4), futures 9 -> 12
        # (move 3), basis move 4 - 3 = 1; futures leg -0.5 * 3 = -1.5;
        # hedged P&L 4 - 1.5 = 2.5; 4 observations in the window.
        spot, futures = self._prices()
        report = window_pnl(spot, futures, 0.5, "2024-01-02", "2024-01-05")
        assert report["n_days"] == pytest.approx(4.0)
        assert report["spot_start"] == pytest.approx(11.0)
        assert report["spot_end"] == pytest.approx(15.0)
        assert report["futures_start"] == pytest.approx(9.0)
        assert report["futures_end"] == pytest.approx(12.0)
        assert report["spot_move"] == pytest.approx(4.0)
        assert report["futures_move"] == pytest.approx(3.0)
        assert report["basis_move"] == pytest.approx(1.0)
        assert report["unhedged_pnl_per_lb"] == pytest.approx(4.0)
        assert report["futures_leg_pnl_per_lb"] == pytest.approx(-1.5)
        assert report["hedged_pnl_per_lb"] == pytest.approx(2.5)

    def test_one_to_one_hedged_pnl_is_the_basis_move_identically(self):
        # h = 1 over the whole window: spot move 5, futures move 4, so the
        # hedged P&L must equal the basis move (1.0) to the last bit.
        spot, futures = self._prices()
        report = window_pnl(spot, futures, 1.0, "2024-01-01", "2024-01-05")
        assert report["hedged_pnl_per_lb"] == report["basis_move"]
        assert report["basis_move"] == pytest.approx(1.0)

    def test_window_endpoints_are_inclusive(self):
        spot, futures = self._prices()
        full = window_pnl(spot, futures, 1.0, "2024-01-01", "2024-01-05")
        clipped = window_pnl(spot, futures, 1.0, "2024-01-01", "2024-01-04")
        assert full["n_days"] == pytest.approx(5.0)
        assert clipped["n_days"] == pytest.approx(4.0)
        assert clipped["spot_end"] == pytest.approx(13.0)
        assert clipped["futures_end"] == pytest.approx(10.0)

    def test_a_single_observation_window_has_zero_moves(self):
        spot, futures = self._prices()
        report = window_pnl(spot, futures, 0.7, "2024-01-03", "2024-01-03")
        assert report["n_days"] == pytest.approx(1.0)
        assert report["spot_move"] == pytest.approx(0.0)
        assert report["futures_move"] == pytest.approx(0.0)
        assert report["hedged_pnl_per_lb"] == pytest.approx(0.0)

    def test_an_empty_window_raises_value_error(self):
        spot, futures = self._prices()
        with pytest.raises(ValueError):
            window_pnl(spot, futures, 1.0, "2030-01-01", "2030-12-31")
