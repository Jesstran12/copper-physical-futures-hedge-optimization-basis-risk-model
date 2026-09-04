"""Basis math: the spot-futures gap, its risk, and what it does to a hedger.

All inputs are prices or price changes in $/lb (see data.py for conventions).
Variances are sample variances (ddof=1, the pandas `.var()` default).

The finance in one paragraph: the BASIS is b = S - F, the spot price minus
the futures price, in the same units. It is the part of a hedged position
the hedge cannot touch: a hedger long physical copper and short one futures
contract per lb has daily P&L dS - dF, which is EXACTLY the daily change in
the basis, db. So "basis risk" — the volatility of db — is not an abstract
statistic; for the dollar-for-dollar (1:1) hedger it IS the residual risk,
identically, and the tests enforce that identity. Phases 2-5 measured how
much variance a hedge removes; Phase 6 names and measures what is left.

The story chapter: most of the time the LME-COMEX basis wiggles inside a
modest band, but twice in this sample it broke loose — the May 2024 COMEX
squeeze (shorts forced to buy back, COMEX spiking far above LME) and the
2025 US tariff dislocation (COMEX carrying a tariff premium LME never had).
A "safe" hedged position bleeds real money through exactly this gap, and
`window_pnl` computes what a hedger experienced through any such window.
"""

from __future__ import annotations

import pandas as pd

from copper_hedge.hedge import (
    exclude_roll_days,
    hedged_changes,
    optimal_hedge_ratio,
    price_changes,
)


def basis_series(spot_prices: pd.Series, futures_prices: pd.Series) -> pd.Series:
    """The basis: spot minus futures, elementwise, in $/lb.

    Both inputs are price series in $/lb sharing an index (columns of the
    aligned frame). Positive basis = spot above futures (backwardation
    flavor); negative = futures above spot — during the 2024 squeeze and
    the 2025 tariff dislocation COMEX traded far ABOVE LME cash, so those
    episodes show up as deeply NEGATIVE basis. Returns a Series on the
    same index.
    """
    return spot_prices - futures_prices


def basis_report(
    spot_prices: pd.Series,
    futures_prices: pd.Series,
    roll_flags: pd.Series,
) -> dict[str, float]:
    """Descriptive statistics of the basis level and of its daily changes.

    Takes daily PRICE series in $/lb on a shared index plus the daily roll
    flags. Level statistics use every day: the basis level is a real price
    difference on every date (each day's futures price is a real quote of
    the current front contract). Change statistics exclude roll-flagged
    days: a splice jump in F pollutes that day's db exactly as it pollutes
    dF, so the standing Phase 2-5 exclusion convention applies to db too.

    Returns a dict with keys "n_days", "mean_basis", "std_basis",
    "min_basis", "max_basis" (level stats over all days, $/lb),
    "n_delta_obs", and "std_delta_basis" (change stats over the
    roll-excluded db observations, $/lb per day) — all plain floats.
    """
    basis = basis_series(spot_prices, futures_prices)
    delta_basis = exclude_roll_days(price_changes(basis), roll_flags)
    return {
        "n_days": float(basis.count()),
        "mean_basis": float(basis.mean()),
        "std_basis": float(basis.std()),
        "min_basis": float(basis.min()),
        "max_basis": float(basis.max()),
        "n_delta_obs": float(delta_basis.count()),
        "std_delta_basis": float(delta_basis.std()),
    }


def residual_risk_report(
    delta_spot: pd.Series,
    delta_futures: pd.Series,
) -> dict[str, float]:
    """Link the risk a hedge leaves behind to the risk of the basis.

    Takes change series in $/lb (already roll-excluded, as in Phase 3) on a
    shared index. Two facts this report puts side by side:

    - For the naive 1:1 hedger, residual P&L is db = dS - dF IDENTICALLY,
      so "basis_change_variance" (computed from the basis-change series)
      must equal the naive hedged variance to the last bit.
    - The optimal hedge leaves residual variance (1 - R^2) * Var(dS) — on
      daily data h* is attenuated well below 1 by async-close timing noise,
      so the optimal residual is SMALLER than the full basis wiggle:
      "basis_share_of_residual" (basis-change variance over the optimal
      residual variance) comes out above 1.

    Returns a dict with keys "hedge_ratio", "unhedged_variance",
    "residual_variance", "residual_std" (the optimal hedge's leftover),
    "basis_change_variance", "basis_change_std", and
    "basis_share_of_residual" — all plain floats; variances in ($/lb)^2
    per day, stds in $/lb per day.
    """
    h = optimal_hedge_ratio(delta_spot, delta_futures)
    residual = hedged_changes(delta_spot, delta_futures, h)
    basis_change = delta_spot - delta_futures          # built directly, per the contract

    residual_var = float(residual.var())
    basis_var = float(basis_change.var())
    return {
        "hedge_ratio": h,
        "unhedged_variance": float(delta_spot.var()),
        "residual_variance": residual_var,
        "residual_std": float(residual.std()),
        "basis_change_variance": basis_var,
        "basis_change_std": float(basis_change.std()),
        "basis_share_of_residual": basis_var / residual_var,
    }


def window_pnl(
    spot_prices: pd.Series,
    futures_prices: pd.Series,
    hedge_ratio: float,
    start: str,
    end: str,
) -> dict[str, float]:
    """A hedger's P&L per lb through one date window — the case-study engine.

    Takes daily PRICE series in $/lb on a shared index, the hedge ratio the
    hedger was running, and a date window (both endpoints inclusive, pandas
    `.loc[start:end]` slicing). The position is the project's standing one:
    long 1 lb of physical copper, short `hedge_ratio` lb of futures, held
    from the window's first observation to its last. Moves are last minus
    first (a single-observation window has zero moves); a window containing
    no observations of either series raises ValueError — a case study over
    an empty window is a caller mistake, not a statistic.

    Returns a dict with keys "n_days" (observations in the window),
    "spot_start", "spot_end", "futures_start", "futures_end" (price levels,
    $/lb), "spot_move", "futures_move", "basis_move" (last-minus-first,
    $/lb; basis_move = spot_move - futures_move), "unhedged_pnl_per_lb"
    (= spot_move), "futures_leg_pnl_per_lb" (= -hedge_ratio * futures_move;
    a short GAINS when futures fall), and "hedged_pnl_per_lb" (their sum) —
    all plain floats. With hedge_ratio = 1 the hedged P&L equals the basis
    move identically: that identity IS the case study's punchline.
    """
    s = spot_prices.loc[start:end]
    f = futures_prices.loc[start:end]
    if len(s) == 0:
        raise ValueError(f"empty window: {start} to {end}")

    spot_start, spot_end = float(s.iloc[0]), float(s.iloc[-1])
    futures_start, futures_end = float(f.iloc[0]), float(f.iloc[-1])
    spot_move = spot_end - spot_start
    futures_move = futures_end - futures_start

    long_pnl = spot_move                       # long 1 lb physical
    short_pnl = -hedge_ratio * futures_move    # short h lb futures — negative exposure
    hedged_pnl = long_pnl + short_pnl

    return {
        "n_days": float(len(s)),
        "spot_start": spot_start,
        "spot_end": spot_end,
        "spot_move": spot_move,
        "futures_start": futures_start,
        "futures_end": futures_end,
        "futures_move": futures_move,
        "basis_move": spot_move - futures_move,
        "unhedged_pnl_per_lb": long_pnl,
        "futures_leg_pnl_per_lb": short_pnl,
        "hedged_pnl_per_lb": hedged_pnl,
    }
