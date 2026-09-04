"""Tests for the out-of-sample hedge engine (Phase 4).

These tests define the contract for the Phase 4 additions to
src/copper_hedge/hedge.py. Do not edit them — implement the module until
they pass. All expected values are hand-computed (the arithmetic is in the
comments); sample moments use ddof=1 (the pandas default).

The fact this file exists to enforce: NO LOOKAHEAD. A hedge ratio applied
at date t may be estimated from data strictly before t — never the
observation at t itself, never anything after it. Three tests attack that
rule directly: perturbing future data must leave past estimates bitwise
unchanged, perturbing date t's own observation must leave the estimate AT t
unchanged, and a rolling window must forget observations that fell out of
it. A fourth runs the engine on synthetic data whose true beta shifts
mid-sample and checks each window tracks it as theory says.
"""

import numpy as np
import pandas as pd
import pytest

from copper_hedge.hedge import (
    apply_hedge_path,
    one_step_ahead_hedge_ratios,
    out_of_sample_report,
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


def _regime_shift_pair(n_first=200, n_second=200, beta_first=0.5,
                       beta_second=1.5, noise=0.1, seed=7):
    """Synthetic changes whose TRUE beta jumps mid-sample (fixed seed)."""
    n = n_first + n_second
    rng = np.random.default_rng(seed)
    df_ = _series(rng.normal(0.0, 1.0, n), name="dF")
    beta = np.concatenate(
        [np.full(n_first, beta_first), np.full(n_second, beta_second)]
    )
    ds = _series(beta * df_.to_numpy() + rng.normal(0.0, noise, n), name="dS")
    return ds, df_


# Shared hand-computed example, used across classes (ddof=1 throughout):
#   dF = [1, 2, 3, 4, 5],  dS = [2, 3, 5, 9, 8]
#
# Rolling window=3 — the ratio at position t uses positions t-3..t-1:
#   t=3 uses obs 0..2: dF=[1,2,3] mean 2, devs [-1,0,1], VarF = (1+0+1)/2 = 1
#                      dS=[2,3,5] mean 10/3, devs [-4/3, -1/3, 5/3]
#                      Cov = ((-1)(-4/3) + 0 + (1)(5/3)) / 2 = (9/3)/2 = 1.5
#                      h = 1.5 / 1 = 1.5
#   t=4 uses obs 1..3: dF=[2,3,4] mean 3, devs [-1,0,1], VarF = 1
#                      dS=[3,5,9] mean 17/3, devs [-8/3, -2/3, 10/3]
#                      Cov = ((-1)(-8/3) + 0 + (1)(10/3)) / 2 = (18/3)/2 = 3
#                      h = 3.0
#   expected: [NaN, NaN, NaN, 1.5, 3.0]
#
# Expanding min_obs=3 — the ratio at position t uses ALL positions < t:
#   t=3: same three obs as above -> 1.5
#   t=4 uses obs 0..3: dF=[1,2,3,4] mean 2.5, devs [-1.5,-0.5,0.5,1.5],
#                      VarF = (2.25+0.25+0.25+2.25)/3 = 5/3
#                      dS=[2,3,5,9] mean 4.75, devs [-2.75,-1.75,0.25,4.25]
#                      Cov = (4.125+0.875+0.125+6.375)/3 = 11.5/3
#                      h = (11.5/3)/(5/3) = 11.5/5 = 2.3
#   expected: [NaN, NaN, NaN, 1.5, 2.3]
HAND_DF = [1.0, 2.0, 3.0, 4.0, 5.0]
HAND_DS = [2.0, 3.0, 5.0, 9.0, 8.0]


class TestOneStepAheadHedgeRatios:
    def test_rolling_hand_computed(self):
        # See the arithmetic above: [NaN, NaN, NaN, 1.5, 3.0].
        ds, df_ = _series(HAND_DS), _series(HAND_DF)
        h = one_step_ahead_hedge_ratios(ds, df_, window=3)
        assert h.index.equals(ds.index)
        assert h.iloc[:3].isna().all()
        assert h.iloc[3] == pytest.approx(1.5)
        assert h.iloc[4] == pytest.approx(3.0)

    def test_expanding_hand_computed(self):
        # See the arithmetic above: [NaN, NaN, NaN, 1.5, 2.3].
        ds, df_ = _series(HAND_DS), _series(HAND_DF)
        h = one_step_ahead_hedge_ratios(ds, df_, window=None, min_obs=3)
        assert h.iloc[:3].isna().all()
        assert h.iloc[3] == pytest.approx(1.5)
        assert h.iloc[4] == pytest.approx(2.3)

    def test_rolling_warmup_is_exactly_window_nans(self):
        # The first defined estimate sits at position `window` — it is the
        # first date with a full window of PRIOR observations.
        ds, df_ = _noisy_pair(n=100)
        h = one_step_ahead_hedge_ratios(ds, df_, window=20)
        assert h.iloc[:20].isna().all()
        assert h.iloc[20:].notna().all()

    def test_expanding_warmup_respects_min_obs(self):
        ds, df_ = _noisy_pair(n=100)
        h = one_step_ahead_hedge_ratios(ds, df_, window=None, min_obs=30)
        assert h.iloc[:30].isna().all()
        assert h.iloc[30:].notna().all()

    def test_constant_true_beta_is_recovered_everywhere(self):
        # Noise-free dS = 0.7 * dF: every window, at every date, must
        # estimate exactly 0.7 — rolling and expanding alike.
        rng = np.random.default_rng(3)
        df_ = _series(rng.normal(0.0, 1.0, 80), name="dF")
        ds = 0.7 * df_
        rolling = one_step_ahead_hedge_ratios(ds, df_, window=10)
        expanding = one_step_ahead_hedge_ratios(ds, df_, window=None, min_obs=10)
        assert np.allclose(rolling.dropna(), 0.7)
        assert np.allclose(expanding.dropna(), 0.7)

    def test_no_lookahead_perturbing_the_future_leaves_the_past_unchanged(self):
        # THE Phase 4 rule. Blow up the last 50 observations of both series;
        # every estimate up to and including the first perturbed date must be
        # bitwise unchanged (the estimate AT the first perturbed date uses
        # only data before it, so even it may not move). This test is run for
        # all three window schemes.
        ds, df_ = _noisy_pair(n=200)
        ds_pert, df_pert = ds.copy(), df_.copy()
        ds_pert.iloc[150:] *= 10.0
        df_pert.iloc[150:] *= -7.0
        for window in [60, 120, None]:
            before = one_step_ahead_hedge_ratios(ds, df_, window=window)
            after = one_step_ahead_hedge_ratios(ds_pert, df_pert, window=window)
            pd.testing.assert_series_equal(before.iloc[:151], after.iloc[:151])

    def test_estimate_at_t_ignores_the_observation_at_t(self):
        # "Strictly before t" means date t's OWN move is out of bounds too:
        # a desk sets its hedge before the day trades. Changing only the
        # observation at position 100 must leave the estimate at 100
        # untouched — and must show up in the estimate at 101.
        ds, df_ = _noisy_pair(n=150)
        ds_pert = ds.copy()
        ds_pert.iloc[100] += 50.0
        before = one_step_ahead_hedge_ratios(ds, df_, window=60)
        after = one_step_ahead_hedge_ratios(ds_pert, df_, window=60)
        assert after.iloc[100] == before.iloc[100]
        assert after.iloc[101] != before.iloc[101]

    def test_rolling_window_forgets_observations_that_fell_out_of_it(self):
        # The estimate at position t uses positions t-w..t-1 and nothing
        # older: with w=60, perturbing position 39 must leave the estimate
        # at position 100 (window = positions 40..99) unchanged, while
        # perturbing position 40 — the oldest observation still inside the
        # window — must move it.
        ds, df_ = _noisy_pair(n=150)
        base = one_step_ahead_hedge_ratios(ds, df_, window=60)
        outside = ds.copy()
        outside.iloc[39] += 50.0
        inside = ds.copy()
        inside.iloc[40] += 50.0
        h_outside = one_step_ahead_hedge_ratios(outside, df_, window=60)
        h_inside = one_step_ahead_hedge_ratios(inside, df_, window=60)
        assert h_outside.iloc[100] == base.iloc[100]
        assert h_inside.iloc[100] != base.iloc[100]

    def test_time_varying_beta_is_tracked_as_theory_predicts(self):
        # True beta jumps 0.5 -> 1.5 at position 200 (noise sd 0.1, so a
        # 60-obs estimate has a standard error of roughly 0.1/sqrt(60) —
        # tiny). Once a rolling window lies entirely inside one regime, its
        # estimate must sit on that regime's beta; the expanding window,
        # which never forgets, must land in between — that is the
        # bias/variance tradeoff the phase exists to demonstrate.
        ds, df_ = _regime_shift_pair()
        rolling = one_step_ahead_hedge_ratios(ds, df_, window=60)
        expanding = one_step_ahead_hedge_ratios(ds, df_, window=None, min_obs=60)
        # position 199: window = positions 139..198, all regime one.
        assert rolling.iloc[199] == pytest.approx(0.5, abs=0.1)
        # position 399: window = positions 339..398, all regime two.
        assert rolling.iloc[399] == pytest.approx(1.5, abs=0.1)
        # expanding at the end has seen ~200 obs of each regime: in between.
        assert 0.8 < expanding.iloc[399] < 1.2


class TestApplyHedgePath:
    def test_hand_computed_hedged_path(self):
        # Ratios from the shared example: [NaN, NaN, NaN, 1.5, 3.0].
        #   position 3: 9 - 1.5*4 = 3.0
        #   position 4: 8 - 3.0*5 = -7.0
        ds, df_ = _series(HAND_DS), _series(HAND_DF)
        ratios = one_step_ahead_hedge_ratios(ds, df_, window=3)
        hedged = apply_hedge_path(ds, df_, ratios)
        assert hedged.tolist() == pytest.approx([3.0, -7.0])
        assert list(hedged.index) == [ds.index[3], ds.index[4]]

    def test_warmup_days_are_dropped(self):
        ds, df_ = _noisy_pair(n=100)
        ratios = one_step_ahead_hedge_ratios(ds, df_, window=20)
        hedged = apply_hedge_path(ds, df_, ratios)
        assert len(hedged) == 80
        assert hedged.notna().all()

    def test_all_nan_path_gives_an_empty_series(self):
        ds, df_ = _series([1.0, 2.0, 3.0]), _series([1.0, 1.0, 1.0])
        ratios = pd.Series(float("nan"), index=ds.index)
        assert len(apply_hedge_path(ds, df_, ratios)) == 0

    def test_correct_constant_path_zeroes_the_pnl(self):
        # If the path always equals the true beta of a noise-free pair,
        # the hedged changes are identically zero.
        df_ = _series([1.0, -2.0, 3.0, -1.0, 2.0])
        ds = 0.5 * df_
        ratios = pd.Series(0.5, index=ds.index)
        hedged = apply_hedge_path(ds, df_, ratios)
        assert np.allclose(hedged, 0.0)


class TestOutOfSampleReport:
    def test_report_has_exactly_the_documented_keys_as_floats(self):
        ds, df_ = _noisy_pair()
        report = out_of_sample_report(ds, df_, window=60)
        assert set(report) == {
            "n_days",
            "unhedged_variance",
            "hedged_variance",
            "oos_effectiveness",
            "naive_effectiveness",
        }
        assert all(isinstance(v, float) for v in report.values())

    def test_hand_computed_report(self):
        # Window=3 on the shared example evaluates on positions 3 and 4:
        #   eval dS = [9, 8]           -> Var = ((0.5)^2 + (0.5)^2)/1 = 0.5
        #   hedged  = [3.0, -7.0]      -> mean -2, Var = (25 + 25)/1 = 50
        #   oos_effectiveness   = 1 - 50/0.5   = -99.0  (2-day toy data —
        #     the engine is honest about a terrible hedge, not flattering)
        #   naive   = [9-4, 8-5] = [5, 3] -> Var = (1 + 1)/1 = 2
        #   naive_effectiveness = 1 - 2/0.5    = -3.0
        ds, df_ = _series(HAND_DS), _series(HAND_DF)
        report = out_of_sample_report(ds, df_, window=3)
        assert report["n_days"] == pytest.approx(2.0)
        assert report["unhedged_variance"] == pytest.approx(0.5)
        assert report["hedged_variance"] == pytest.approx(50.0)
        assert report["oos_effectiveness"] == pytest.approx(-99.0)
        assert report["naive_effectiveness"] == pytest.approx(-3.0)

    def test_report_is_consistent_with_its_building_blocks(self):
        # The report must be exactly the composition of the two functions
        # above, evaluated on the defined-ratio days — no hidden extras.
        ds, df_ = _noisy_pair()
        report = out_of_sample_report(ds, df_, window=60)
        ratios = one_step_ahead_hedge_ratios(ds, df_, window=60)
        hedged = apply_hedge_path(ds, df_, ratios)
        eval_spot = ds.loc[hedged.index]
        assert report["n_days"] == pytest.approx(float(len(hedged)))
        assert report["unhedged_variance"] == pytest.approx(eval_spot.var())
        assert report["hedged_variance"] == pytest.approx(hedged.var())
        assert report["oos_effectiveness"] == pytest.approx(
            variance_reduction(eval_spot, hedged)
        )

    def test_evaluation_counts_only_days_with_a_defined_ratio(self):
        ds, df_ = _noisy_pair(n=250)
        assert out_of_sample_report(ds, df_, window=60)["n_days"] == 190.0
        assert (
            out_of_sample_report(ds, df_, window=None, min_obs=80)["n_days"]
            == 170.0
        )

    def test_strong_stable_relationship_scores_near_one_out_of_sample(self):
        # dS = 0.8*dF + tiny noise, beta constant: even estimated purely
        # from the past, the hedge should remove nearly all the variance.
        ds, df_ = _noisy_pair(n=250, beta=0.8, noise=0.02)
        report = out_of_sample_report(ds, df_, window=60)
        assert report["oos_effectiveness"] > 0.95
