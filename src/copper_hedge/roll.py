"""Roll-date detection for the spliced HG=F front-month series.

HG=F stitches successive futures contracts into one price history. On the day
the series switches contracts ("roll" day), the price can jump even though no
one trading actually experienced that move — the jump is the price difference
between the old and new contract, not a market move. Left in, these fake jumps
pollute any statistic computed from day-to-day price changes.

Detection heuristic (calendar window + price gap):
- COMEX copper's liquid ("active") delivery months are Mar, May, Jul, Sep, Dec.
  Rolls happen in or just before those months, so a day is a *roll candidate*
  only if it falls inside that calendar window.
- A candidate day is *flagged* only if its absolute price change is abnormally
  large versus recent history (a multiple of the trailing median absolute
  change) — strictly using data from before that day, never after.
"""

from __future__ import annotations

import pandas as pd

# COMEX copper active delivery months: Mar, May, Jul, Sep, Dec.
ACTIVE_MONTHS: tuple[int, ...] = (3, 5, 7, 9, 12)


def is_roll_candidate(
    dates: pd.DatetimeIndex,
    active_months: tuple[int, ...] = ACTIVE_MONTHS,
    pre_days: int = 7,
) -> pd.Series:
    """Mark dates that fall inside a plausible roll window.

    A date is a roll candidate if:
    - its month is an active delivery month (the front contract expires and
      rolls somewhere inside that month), OR
    - it falls in the last `pre_days` calendar days of the month immediately
      *before* an active month (early rolls as volume migrates).

    Returns a boolean Series indexed by `dates`.
    """
    idx = pd.DatetimeIndex(dates)
    in_active_month = idx.month.isin(active_months)
    next_month = (idx.month % 12) + 1            # Dec (12) wraps around to Jan (1)
    before_active = next_month.isin(active_months)
    last_days = idx.day > (idx.days_in_month - pre_days)
    candidate = in_active_month | (before_active & last_days)
    return pd.Series(candidate, index=dates)


def flag_roll_days(
    prices: pd.Series,
    gap_mult: float = 4.0,
    lookback: int = 60,
    min_history: int = 20,
    active_months: tuple[int, ...] = ACTIVE_MONTHS,
    pre_days: int = 7,
) -> pd.Series:
    """Flag price-change days that look like contract rolls.

    A day t is flagged iff all of the following hold:
    1. t is a roll candidate per `is_roll_candidate`;
    2. at least `min_history` price changes exist strictly before t;
    3. |change at t| > gap_mult x median(|change|) over the `lookback` most
       recent changes strictly before t (no lookahead: the day's own change
       must not enter its threshold).

    Returns a boolean Series indexed like `prices.diff().dropna()`.
    """
    changes = prices.diff().dropna()
    abs_changes = changes.abs()

    # shift(1) keeps the day's own change out of its threshold — no lookahead.
    threshold = (
        abs_changes.shift(1)
        .rolling(lookback, min_periods=min_history)
        .median()
    )

    in_window = is_roll_candidate(changes.index, active_months=active_months)
    big_jump = abs_changes > (gap_mult * threshold)

    flags = in_window & big_jump
    return flags.fillna(False)
