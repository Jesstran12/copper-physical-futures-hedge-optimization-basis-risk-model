"""Tests for the robustness checks (Phase 5): weekly re-run + sub-periods.

These tests define the contract for the Phase 5 additions to
src/copper_hedge/hedge.py. Do not edit them — implement the module until
they pass. All expected values are hand-computed (the arithmetic is in the
comments); sample moments use ddof=1 (the pandas default).

The two facts this file exists to enforce:

1. WEEKLY means Friday-anchored calendar weeks on the common trading days —
   each week contributes its last common trading day's price (Thursday when
   Friday is missing), weeks with no common days are dropped, and a week
   containing any roll-flagged day is excluded from the weekly regression,
   carrying Phases 2-4's convention to the weekly frequency. One test
   builds synthetic "async close" data (the spot leg reacts to the futures
   leg half a day late) and checks the weekly R-squared beats the daily one
   — the exact mechanism the phase exists to demonstrate on real data.

2. SUB-PERIODS are fitted in isolation: each regime's h* and effectiveness
   use that regime's observations only, so perturbing data outside a period
   must leave its row bitwise unchanged.
"""

import numpy as np
import pandas as pd
import pytest

from copper_hedge.hedge import (
    SUB_PERIODS,
    exclude_roll_days,
    in_sample_r_squared,
    optimal_hedge_report,
    price_changes,
    resample_weekly_last,
    sub_period_report,
    weekly_hedge_report,
    weekly_roll_flags,
)


def _daily(values, start="2024-01-01"):
    """A float Series on consecutive business days (2024-01-01 is a Monday)."""
    dates = pd.bdate_range(start, periods=len(values))
    return pd.Series(values, index=dates, dtype=float)


def _async_close_pair(n=750, lag_weight=0.5, noise=0.05, seed=11):
    """Daily PRICE series where the spot leg reacts to futures half a day late.

    dS_t = (1 - lag_weight) * dF_t + lag_weight * dF_{t-1} + tiny noise —
    the stylized async-close effect: part of each futures move only shows up
    in the next day's spot print. Daily correlation is capped well below 1,
    but weekly sums recover almost all of it (adjacent-day leakage stays
    inside the same week 4 days out of 5).
    """
    rng = np.random.default_rng(seed)
    df_daily = rng.normal(0.0, 1.0, n)
    df_lagged = np.concatenate([[0.0], df_daily[:-1]])
    ds_daily = (
        (1.0 - lag_weight) * df_daily
        + lag_weight * df_lagged
        + rng.normal(0.0, noise, n)
    )
    futures = _daily(100.0 + np.cumsum(df_daily), start="2019-01-01")
    spot = _daily(100.0 + np.cumsum(ds_daily), start="2019-01-01")
    return spot, futures


class TestSubPeriodsConstant:
    def test_the_five_regimes_in_chronological_order(self):
        labels = [label for label, _, _ in SUB_PERIODS]
        assert labels == [
            "2019 calm",
            "2020 COVID",
            "2021-23 tightness",
            "2024 squeeze era",
            "2025+ tariff era",
        ]
        starts = [pd.Timestamp(start) for _, start, _ in SUB_PERIODS]
        assert starts == sorted(starts)
        for _, start, end in SUB_PERIODS:
            assert pd.Timestamp(start) <= pd.Timestamp(end)


class TestResampleWeeklyLast:
    def test_friday_labels_take_the_last_price_of_each_week(self):
        # Ten business days = two full Mon-Fri weeks; each week's Friday
        # price (5.0, then 10.0) survives, labeled with that Friday.
        prices = _daily([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        weekly = resample_weekly_last(prices)
        assert list(weekly.index) == [
            pd.Timestamp("2024-01-05"),
            pd.Timestamp("2024-01-12"),
        ]
        assert weekly.tolist() == [5.0, 10.0]

    def test_missing_friday_falls_back_to_thursday(self):
        # Week one is Mon-Thu only (Friday missing, as on a holiday or an
        # inner-join drop): Thursday's 4.0 becomes the week's price, still
        # labeled with the Friday date.
        dates = pd.to_datetime(
            ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04",
             "2024-01-08", "2024-01-09", "2024-01-10", "2024-01-11",
             "2024-01-12"]
        )
        prices = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0],
                           index=dates)
        weekly = resample_weekly_last(prices)
        assert list(weekly.index) == [
            pd.Timestamp("2024-01-05"),
            pd.Timestamp("2024-01-12"),
        ]
        assert weekly.tolist() == [4.0, 9.0]

    def test_weeks_with_no_observations_are_dropped(self):
        # Data in the weeks of Jan 5 and Jan 19, nothing in between: the
        # empty middle week must vanish, not appear as NaN.
        dates = pd.to_datetime(
            ["2024-01-03", "2024-01-04", "2024-01-05",
             "2024-01-17", "2024-01-18", "2024-01-19"]
        )
        prices = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0, 6.0], index=dates)
        weekly = resample_weekly_last(prices)
        assert list(weekly.index) == [
            pd.Timestamp("2024-01-05"),
            pd.Timestamp("2024-01-19"),
        ]
        assert weekly.notna().all()

    def test_every_label_is_a_friday(self):
        rng = np.random.default_rng(1)
        prices = _daily(rng.normal(4.0, 0.1, 130))
        weekly = resample_weekly_last(prices)
        assert (weekly.index.weekday == 4).all()

    def test_a_single_observation_makes_a_one_week_series(self):
        # 2024-01-10 is a Wednesday; its week ends Friday 2024-01-12.
        prices = pd.Series([3.5], index=pd.to_datetime(["2024-01-10"]))
        weekly = resample_weekly_last(prices)
        assert list(weekly.index) == [pd.Timestamp("2024-01-12")]
        assert weekly.tolist() == [3.5]


class TestWeeklyRollFlags:
    def test_a_flagged_day_flags_its_own_week_only(self):
        # Two full weeks of daily flags, one True on Wednesday 2024-01-03:
        # week Fri 2024-01-05 -> True, week Fri 2024-01-12 -> False.
        flags = pd.Series(False, index=pd.bdate_range("2024-01-01", periods=10))
        flags.loc["2024-01-03"] = True
        weekly = weekly_roll_flags(flags)
        assert weekly.loc[pd.Timestamp("2024-01-05")] == True  # noqa: E712
        assert weekly.loc[pd.Timestamp("2024-01-12")] == False  # noqa: E712

    def test_a_monday_flag_lands_in_the_week_ending_that_friday(self):
        # A weekly change labeled Friday t spans the days AFTER the previous
        # Friday through t — so a Monday 2024-01-08 flag contaminates the
        # week ending 2024-01-12, not the week ending 2024-01-05.
        flags = pd.Series(False, index=pd.bdate_range("2024-01-01", periods=10))
        flags.loc["2024-01-08"] = True
        weekly = weekly_roll_flags(flags)
        assert weekly.loc[pd.Timestamp("2024-01-05")] == False  # noqa: E712
        assert weekly.loc[pd.Timestamp("2024-01-12")] == True  # noqa: E712

    def test_result_is_boolean_and_friday_labeled(self):
        flags = pd.Series(False, index=pd.bdate_range("2024-01-01", periods=30))
        weekly = weekly_roll_flags(flags)
        assert weekly.dtype == bool
        assert (weekly.index.weekday == 4).all()

    def test_weeks_with_no_flag_rows_come_back_false(self):
        # Flag rows exist only in the first and third weeks; the empty
        # middle week must come back False, not NaN — an unflagged week is
        # a keepable week.
        dates = pd.to_datetime(["2024-01-03", "2024-01-17"])
        flags = pd.Series([True, False], index=dates)
        weekly = weekly_roll_flags(flags)
        assert weekly.loc[pd.Timestamp("2024-01-12")] == False  # noqa: E712
        assert weekly.dtype == bool


# Shared hand-computed weekly example (ddof=1 throughout):
# Four full Mon-Fri weeks of daily prices, constant within each week, so the
# weekly (Friday) prices are exactly:
#   S = [10, 11, 13, 12]     F = [4, 6, 10, 8]
# and the weekly changes (labeled by the later Friday) are:
#   dS = [1, 2, -1]          dF = [2, 4, -2]      (dF = 2 * dS exactly)
#
#   Var(dS): mean 2/3, devs [1/3, 4/3, -5/3],  Var = (1+16+25)/9 / 2 = 7/3
#   Var(dF): mean 4/3, devs [2/3, 8/3, -10/3], Var = (4+64+100)/9 / 2 = 28/3
#   Cov:     [(1/3)(2/3) + (4/3)(8/3) + (-5/3)(-10/3)] / 2 = (84/9)/2 = 14/3
#   h* = (14/3) / (28/3) = 0.5      R^2 = corr^2 = 1 (dF is 2*dS exactly)
#   hedged at h*: dS - 0.5*dF = [0, 0, 0]  -> variance 0 -> effectiveness 1
#   naive 1:1:    dS - dF = [-1, -2, 1]    -> variance 7/3
#                 naive_effectiveness = 1 - (7/3)/(7/3) = 0
HAND_WEEKLY_S = np.repeat([10.0, 11.0, 13.0, 12.0], 5)
HAND_WEEKLY_F = np.repeat([4.0, 6.0, 10.0, 8.0], 5)


class TestWeeklyHedgeReport:
    def _hand_inputs(self):
        spot = _daily(HAND_WEEKLY_S)
        futures = _daily(HAND_WEEKLY_F)
        no_flags = pd.Series(False, index=spot.index)
        return spot, futures, no_flags

    def test_report_has_exactly_the_documented_keys_as_floats(self):
        spot, futures, flags = self._hand_inputs()
        report = weekly_hedge_report(spot, futures, flags)
        assert set(report) == {
            "n_weeks",
            "hedge_ratio",
            "r_squared",
            "unhedged_variance",
            "hedged_variance",
            "effectiveness",
            "naive_effectiveness",
        }
        assert all(isinstance(v, float) for v in report.values())

    def test_hand_computed_weekly_numbers(self):
        # See the arithmetic above the class.
        spot, futures, flags = self._hand_inputs()
        report = weekly_hedge_report(spot, futures, flags)
        assert report["n_weeks"] == pytest.approx(3.0)
        assert report["hedge_ratio"] == pytest.approx(0.5)
        assert report["r_squared"] == pytest.approx(1.0)
        assert report["unhedged_variance"] == pytest.approx(7.0 / 3.0)
        assert report["hedged_variance"] == pytest.approx(0.0)
        assert report["effectiveness"] == pytest.approx(1.0)
        assert report["naive_effectiveness"] == pytest.approx(0.0)

    def test_roll_contaminated_weeks_are_excluded(self):
        # Flag one day (Wednesday 2024-01-17) inside the week ending Friday
        # 2024-01-19: the weekly change labeled 2024-01-19 (dS=2, dF=4) must
        # drop out, leaving dS = [1, -1], dF = [2, -2] -> n_weeks 2, and the
        # exact relationship (h* = 0.5, effectiveness 1) still holds.
        spot, futures, flags = self._hand_inputs()
        flags.loc["2024-01-17"] = True
        report = weekly_hedge_report(spot, futures, flags)
        assert report["n_weeks"] == pytest.approx(2.0)
        assert report["hedge_ratio"] == pytest.approx(0.5)
        assert report["effectiveness"] == pytest.approx(1.0)

    def test_weekly_beats_daily_under_async_closes(self):
        # The phase's whole point. The spot leg reacts to the futures leg
        # half a day late, so daily R^2 is capped near 0.5 — but the missing
        # half shows up the NEXT day, which lands in the same week 4 times
        # out of 5, so weekly R^2 recovers most of the true relationship.
        # The weekly number must beat the daily one by a wide margin.
        spot, futures = _async_close_pair()
        no_flags = pd.Series(False, index=spot.index)
        weekly = weekly_hedge_report(spot, futures, no_flags)
        daily_r2 = in_sample_r_squared(
            price_changes(spot), price_changes(futures)
        )
        assert daily_r2 < 0.65
        assert weekly["r_squared"] > daily_r2 + 0.2

    def test_report_is_consistent_with_its_building_blocks(self):
        # The report must be exactly: resample both legs, difference, drop
        # flagged weeks, then optimal_hedge_report — no hidden extras.
        spot, futures = _async_close_pair(n=300)
        flags = pd.Series(False, index=spot.index)
        flags.iloc[[50, 130]] = True
        report = weekly_hedge_report(spot, futures, flags)

        wflags = weekly_roll_flags(flags)
        ds = exclude_roll_days(price_changes(resample_weekly_last(spot)), wflags)
        df_ = exclude_roll_days(
            price_changes(resample_weekly_last(futures)), wflags
        )
        expected = optimal_hedge_report(ds, df_)
        assert report["n_weeks"] == pytest.approx(float(len(ds)))
        for key in expected:
            assert report[key] == pytest.approx(expected[key])


class TestSubPeriodReport:
    def _two_regime_pair(self):
        """Noise-free changes whose true beta is 0.5 for 100 days, then 2.0."""
        rng = np.random.default_rng(5)
        df_ = _daily(rng.normal(0.0, 1.0, 200))
        beta = np.concatenate([np.full(100, 0.5), np.full(100, 2.0)])
        ds = pd.Series(beta * df_.to_numpy(), index=df_.index)
        return ds, df_

    def _two_periods(self, ds):
        first = ("first", str(ds.index[0].date()), str(ds.index[99].date()))
        second = ("second", str(ds.index[100].date()), str(ds.index[-1].date()))
        return [first, second]

    def test_row_per_period_with_documented_columns(self):
        ds, df_ = self._two_regime_pair()
        table = sub_period_report(ds, df_, self._two_periods(ds))
        assert list(table.index) == ["first", "second"]
        assert list(table.columns) == ["n_obs", "hedge_ratio", "effectiveness"]

    def test_recovers_each_regimes_beta_exactly(self):
        # Noise-free dS = beta * dF within each regime: the fitted h* must
        # equal that regime's beta and the effectiveness must be 1.0.
        ds, df_ = self._two_regime_pair()
        table = sub_period_report(ds, df_, self._two_periods(ds))
        assert table.loc["first", "n_obs"] == 100
        assert table.loc["second", "n_obs"] == 100
        assert table.loc["first", "hedge_ratio"] == pytest.approx(0.5)
        assert table.loc["second", "hedge_ratio"] == pytest.approx(2.0)
        assert table.loc["first", "effectiveness"] == pytest.approx(1.0)
        assert table.loc["second", "effectiveness"] == pytest.approx(1.0)

    def test_period_endpoints_are_inclusive(self):
        ds, df_ = self._two_regime_pair()
        whole = ("all", str(ds.index[0].date()), str(ds.index[-1].date()))
        clipped = ("clipped", str(ds.index[0].date()), str(ds.index[-2].date()))
        table = sub_period_report(ds, df_, [whole, clipped])
        assert table.loc["all", "n_obs"] == 200
        assert table.loc["clipped", "n_obs"] == 199

    def test_periods_are_isolated_from_outside_data(self):
        # The sub-period analog of the no-lookahead rule: blowing up every
        # observation outside a period must leave its row bitwise unchanged.
        ds, df_ = self._two_regime_pair()
        periods = self._two_periods(ds)
        before = sub_period_report(ds, df_, periods)
        ds_pert, df_pert = ds.copy(), df_.copy()
        ds_pert.iloc[100:] += 100.0
        df_pert.iloc[100:] *= -3.0
        after = sub_period_report(ds_pert, df_pert, periods)
        pd.testing.assert_series_equal(before.loc["first"], after.loc["first"])
        assert after.loc["second", "hedge_ratio"] != pytest.approx(
            before.loc["second", "hedge_ratio"]
        )

    def test_a_period_beyond_the_data_gets_nan_stats(self):
        # No observations -> no variance to fit; the row reports its true
        # (zero) count and NaN statistics rather than crashing.
        ds, df_ = self._two_regime_pair()
        table = sub_period_report(
            ds, df_, [("future", "2030-01-01", "2030-12-31")]
        )
        assert table.loc["future", "n_obs"] == 0
        assert np.isnan(table.loc["future", "hedge_ratio"])
        assert np.isnan(table.loc["future", "effectiveness"])
