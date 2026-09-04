"""Hedge math: price changes, hedged P&L changes, baselines, and the optimal hedge.

All inputs are prices or price changes in $/lb (see data.py for conventions).
Variances are sample variances (ddof=1, the pandas `.var()` default).

The finance in one paragraph: you are long physical copper (its value moves
with the spot price S) and short h futures contracts (which move with the
futures price F). Your daily P&L per lb is dS - h*dF. Hedging "works" when
that combined series varies less than dS alone; the fraction of variance
removed is the standard effectiveness measure. Phase 2 built the baselines
(no hedge at all, and the naive h = 1); Phase 3 finds the *optimal* h — the
one that minimizes the hedged variance — and measures how good it is.

The key identity (Phase 3): the variance-minimizing ratio is
h* = Cov(dS, dF) / Var(dF), which is exactly the slope of the OLS regression
of dS on dF, and the effectiveness achieved at h* equals that regression's
R-squared. The tests enforce both facts.

Phase 4 makes the number honest: instead of fitting h* on the full sample
and grading it on the same data, the out-of-sample engine re-estimates h*
each day using only data strictly before that day (a rolling 60- or 120-
observation window, or an expanding all-history window), applies it to the
next day's move, and measures effectiveness on those never-seen days. The
one iron rule is NO LOOKAHEAD: an estimate applied at time t may use data
from before t only — never t itself, never later. The tests enforce this by
perturbing future data and asserting past estimates do not move.

Phase 5 stress-tests the story from two angles. First, timing: LME fixes at
~1pm London, COMEX settles ~1pm New York, so "same-day" prices are hours
apart and daily correlation is artificially depressed. Measured on WEEKLY
changes (last common trading day of each Friday-anchored week), that timing
noise mostly washes out and effectiveness should rise — the async-close
robustness check. Second, regimes: the same in-sample h* and effectiveness
recomputed inside five sub-periods (2019 calm, 2020 COVID, 2021-23
tightness, 2024 squeeze, 2025+ tariff era) show how the hedge behaves in
calm vs. crisis markets.
"""

from __future__ import annotations

import pandas as pd


def price_changes(prices: pd.Series) -> pd.Series:
    """Day-over-day price changes (differences, not returns).

    The first observation has no prior day, so the result is one element
    shorter than the input.
    """
    return prices.diff().dropna()


def hedged_changes(
    delta_spot: pd.Series,
    delta_futures: pd.Series,
    hedge_ratio: float,
) -> pd.Series:
    """Daily change of a hedged position: delta_spot - hedge_ratio * delta_futures.

    Long spot, short `hedge_ratio` units of futures. Inputs must share an index.
    """
    return delta_spot - hedge_ratio * delta_futures


def variance_reduction(delta_unhedged: pd.Series, delta_hedged: pd.Series) -> float:
    """Fraction of variance the hedge removed: 1 - Var(hedged)/Var(unhedged).

    1.0 = perfect hedge, 0.0 = useless, negative = the hedge added risk.
    Uses sample variance (ddof=1).
    """
    return 1 - delta_hedged.var() / delta_unhedged.var()


def naive_hedge_report(delta_spot: pd.Series, delta_futures: pd.Series) -> dict[str, float]:
    """The Phase 2 baseline numbers, for a naive 1:1 hedge (hedge_ratio = 1).

    Returns a dict with keys "unhedged_variance", "hedged_variance", and
    "variance_reduction" (all floats, variances in ($/lb)^2 per day).
    """
    delta_hedged = hedged_changes(delta_spot, delta_futures, hedge_ratio=1.0)
    return {
        "unhedged_variance": float(delta_spot.var()),
        "hedged_variance": float(delta_hedged.var()),
        "variance_reduction": variance_reduction(delta_spot, delta_hedged),
    }


def optimal_hedge_ratio(delta_spot: pd.Series, delta_futures: pd.Series) -> float:
    """Minimum-variance hedge ratio: h* = Cov(delta_spot, delta_futures) / Var(delta_futures).

    Sample covariance over sample variance (both ddof=1 — the pandas
    defaults; any common ddof gives the same ratio). This is identical to
    the slope of an OLS regression of delta_spot on delta_futures with an
    intercept. Inputs must share an index. Returns a plain float.
    """
    return float(delta_spot.cov(delta_futures) / delta_futures.var())


def in_sample_r_squared(delta_spot: pd.Series, delta_futures: pd.Series) -> float:
    """R-squared of the OLS regression of delta_spot on delta_futures.

    Equals the squared sample correlation of the two series — direction-
    blind (a perfectly inversely-related pair still scores 1.0). This is
    the in-sample hedge effectiveness achieved at h = h*, an identity the
    tests check explicitly. Returns a plain float in [0, 1].
    """
    return float(delta_spot.corr(delta_futures) ** 2)


def exclude_roll_days(changes: pd.Series, roll_flags: pd.Series) -> pd.Series:
    """Drop observations whose date is roll-flagged.

    `roll_flags` is a boolean Series indexed by date (True = roll day, as
    produced by roll.flag_roll_days or loaded from data/hg_roll_flags.csv).
    Its index need not match `changes`: flags are looked up by date, and a
    date missing from `roll_flags` counts as not flagged (the observation
    is kept). Returns the surviving subset of `changes`, order preserved.
    """
    aligned_flags = roll_flags.reindex(changes.index).fillna(False).astype(bool)
    return changes[~aligned_flags]


def optimal_hedge_report(delta_spot: pd.Series, delta_futures: pd.Series) -> dict[str, float]:
    """The Phase 3 in-sample numbers for the optimal hedge.

    Fits h* on the full inputs and evaluates it on the same inputs (that is
    what "in-sample" means — Phase 4 does the honest out-of-sample version).
    Returns a dict with keys "hedge_ratio", "r_squared",
    "unhedged_variance", "hedged_variance", and "effectiveness" (all plain
    floats; variances in ($/lb)^2 per day). By construction "effectiveness"
    equals "r_squared" up to floating-point noise.
    """
    h = optimal_hedge_ratio(delta_spot, delta_futures)
    delta_hedged = hedged_changes(delta_spot, delta_futures, hedge_ratio=h)
    return {
        "hedge_ratio": h,
        "r_squared": in_sample_r_squared(delta_spot, delta_futures),
        "unhedged_variance": float(delta_spot.var()),
        "hedged_variance": float(delta_hedged.var()),
        "effectiveness": variance_reduction(delta_spot, delta_hedged),
    }


def one_step_ahead_hedge_ratios(
    delta_spot: pd.Series,
    delta_futures: pd.Series,
    window: int | None,
    min_obs: int = 60,
) -> pd.Series:
    """One-step-ahead hedge ratios: at each date t, h* fitted on data strictly before t.

    The estimate for date t is Cov(delta_spot, delta_futures) / Var(delta_futures)
    (both ddof=1, exactly `optimal_hedge_ratio`) computed over past observations
    only — never the observation at t itself, never anything after it:

    - `window` an int w: the w most recent observations before t (dates t-w .. t-1
      by position). The ratio is NaN until a full window of prior observations
      exists, i.e. the first w entries are NaN. `min_obs` is ignored.
    - `window` None: an expanding window — ALL observations strictly before t.
      The ratio is NaN until at least `min_obs` prior observations exist, i.e.
      the first `min_obs` entries are NaN.

    Inputs must share an index. Returns a float Series on that same index
    (same length as the inputs, NaN during the warm-up).
    """
    if window is None:
        cov = delta_spot.expanding(min_periods=min_obs).cov(delta_futures)
        var = delta_futures.expanding(min_periods=min_obs).var()
    else:
        cov = delta_spot.rolling(window).cov(delta_futures)
        var = delta_futures.rolling(window).var()

    # shift(1) makes date t's ratio a function of data through t-1 only —
    # this single shift is the entire no-lookahead guarantee.
    return (cov / var).shift(1)


def apply_hedge_path(
    delta_spot: pd.Series,
    delta_futures: pd.Series,
    hedge_ratios: pd.Series,
) -> pd.Series:
    """Hedged daily changes under a time-varying hedge-ratio path.

    For each date where `hedge_ratios` is defined (not NaN), returns
    delta_spot - hedge_ratios * delta_futures on that date; dates where the
    ratio is undefined (the warm-up) are dropped from the result entirely.
    All inputs share an index; the result's index is the defined-ratio subset,
    order preserved. An all-NaN path returns an empty Series.
    """
    h = hedge_ratios.dropna()
    return delta_spot.loc[h.index] - h * delta_futures.loc[h.index]


def out_of_sample_report(
    delta_spot: pd.Series,
    delta_futures: pd.Series,
    window: int | None,
    min_obs: int = 60,
) -> dict[str, float]:
    """The Phase 4 out-of-sample numbers for one estimation scheme.

    Runs the one-step-ahead engine (`window` / `min_obs` as in
    one_step_ahead_hedge_ratios), evaluates on the days where a ratio is
    defined, and compares against a naive 1:1 hedge on those SAME days.
    Returns a dict with keys "n_days", "unhedged_variance",
    "hedged_variance", "oos_effectiveness", and "naive_effectiveness"
    (all plain floats; variances over the evaluation days only).
    """
    ratios = one_step_ahead_hedge_ratios(
        delta_spot, delta_futures, window=window, min_obs=min_obs
    )
    hedged = apply_hedge_path(delta_spot, delta_futures, ratios)

    eval_dates = hedged.index
    ds = delta_spot.loc[eval_dates]
    df = delta_futures.loc[eval_dates]

    naive = hedged_changes(ds, df, hedge_ratio=1.0)

    return {
        "n_days": float(len(hedged)),
        "unhedged_variance": float(ds.var()),
        "hedged_variance": float(hedged.var()),
        "oos_effectiveness": variance_reduction(ds, hedged),
        "naive_effectiveness": variance_reduction(ds, naive),
    }


# The five market regimes of the sample (label, first date, last date; both
# endpoints inclusive). The last period's end date is deliberately far in the
# future so it always means "through the end of whatever sample is loaded".
SUB_PERIODS: list[tuple[str, str, str]] = [
    ("2019 calm", "2019-01-01", "2019-12-31"),
    ("2020 COVID", "2020-01-01", "2020-12-31"),
    ("2021-23 tightness", "2021-01-01", "2023-12-31"),
    ("2024 squeeze era", "2024-01-01", "2024-12-31"),
    ("2025+ tariff era", "2025-01-01", "2099-12-31"),
]


def resample_weekly_last(prices: pd.Series) -> pd.Series:
    """Weekly price series: the last observation of each Friday-anchored week.

    Weeks run Saturday..Friday and are labeled by their Friday (the pandas
    "W-FRI" convention), so consecutive values are Friday-to-Friday prices on
    the common trading calendar. If the Friday itself is missing (holiday, or
    dropped by the calendar inner-join), the last common trading day of that
    week — typically Thursday — supplies the value, still labeled with the
    Friday. Weeks containing no observations at all are dropped entirely
    (never NaN-filled). Input is a daily price series on a DatetimeIndex;
    the result is a shorter series on Friday-stamped dates.
    """
    return prices.resample("W-FRI").last().dropna()


def weekly_roll_flags(roll_flags: pd.Series) -> pd.Series:
    """Aggregate daily roll flags to weeks: a week is flagged iff any day in it is.

    `roll_flags` is the daily boolean Series (True = roll-flagged ΔF
    observation, as in data/hg_roll_flags.csv). A weekly price change labeled
    Friday t spans the days after the previous Friday through t, so a splice
    jump on ANY of those days contaminates that weekly change — the week gets
    True. Returns a boolean Series labeled by Friday ("W-FRI", matching
    resample_weekly_last); weeks whose days carry no flags come back False.
    """
    return roll_flags.resample("W-FRI").max().fillna(False).astype(bool)


def weekly_hedge_report(
    spot_prices: pd.Series,
    futures_prices: pd.Series,
    roll_flags: pd.Series,
) -> dict[str, float]:
    """The Phase 5 weekly re-run of the core in-sample numbers.

    Takes daily PRICE series (not changes — resampling must happen on price
    levels; pass columns of the aligned frame so both legs cover the same
    weeks) plus the daily roll flags. Resamples both legs to Friday-anchored
    weekly prices, differences them into weekly changes, drops roll-
    contaminated weeks (any week containing a flagged day), and reports the
    in-sample optimal hedge on what survives. Returns a dict with keys
    "n_weeks", "hedge_ratio", "r_squared", "unhedged_variance",
    "hedged_variance", "effectiveness", and "naive_effectiveness" (all plain
    floats; variances in ($/lb)^2 per week; "naive_effectiveness" is the
    variance reduction of a 1:1 hedge on the same weekly changes).
    """
    s_w = resample_weekly_last(spot_prices)
    f_w = resample_weekly_last(futures_prices)
    weekly_flags = weekly_roll_flags(roll_flags)

    delta_s = exclude_roll_days(price_changes(s_w), weekly_flags)
    delta_f = exclude_roll_days(price_changes(f_w), weekly_flags)

    rep = optimal_hedge_report(delta_s, delta_f)
    naive_effectiveness = variance_reduction(
        delta_s, hedged_changes(delta_s, delta_f, 1.0)
    )
    return {
        "n_weeks": float(len(delta_s)),
        "hedge_ratio": rep["hedge_ratio"],
        "r_squared": rep["r_squared"],
        "unhedged_variance": rep["unhedged_variance"],
        "hedged_variance": rep["hedged_variance"],
        "effectiveness": rep["effectiveness"],
        "naive_effectiveness": naive_effectiveness,
    }


def sub_period_report(
    delta_spot: pd.Series,
    delta_futures: pd.Series,
    periods: list[tuple[str, str, str]] = SUB_PERIODS,
) -> pd.DataFrame:
    """In-sample h* and effectiveness inside each sub-period.

    `periods` is a list of (label, start, end) with both endpoints inclusive;
    each period's rows are selected from the inputs by date (dates outside
    every period are simply unused, and a period reaching beyond the data just
    gets what exists). h* and effectiveness are fitted and measured WITHIN
    each period independently, exactly as optimal_hedge_report does on the
    full sample — observations outside a period can never influence its row.

    Returns a DataFrame indexed by the labels (in the given order) with
    columns "n_obs" (int), "hedge_ratio", and "effectiveness" (floats).
    A period with fewer than two observations has no defined variance:
    its stats come back NaN, with its true n_obs.
    """
    rows = {}
    for label, start, end in periods:
        s = delta_spot.loc[start:end]
        f = delta_futures.loc[start:end]
        rep = optimal_hedge_report(s, f)
        rows[label] = {
            "n_obs": int(len(s)),
            "hedge_ratio": rep["hedge_ratio"],
            "effectiveness": rep["effectiveness"],
        }
    return pd.DataFrame.from_dict(rows, orient="index")[
        ["n_obs", "hedge_ratio", "effectiveness"]
    ]
