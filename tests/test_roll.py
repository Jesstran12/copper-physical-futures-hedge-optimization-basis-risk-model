"""Tests for roll-date detection on the spliced HG=F series (Phase 2).

These tests define the contract for src/copper_hedge/roll.py. Do not edit them
— implement the module until they pass.
"""

import numpy as np
import pandas as pd

from copper_hedge.roll import ACTIVE_MONTHS, flag_roll_days, is_roll_candidate


class TestActiveMonths:
    def test_comex_copper_active_months(self):
        assert ACTIVE_MONTHS == (3, 5, 7, 9, 12)


class TestRollCandidateWindow:
    def _mask(self, dates):
        return is_roll_candidate(pd.DatetimeIndex(pd.to_datetime(dates)))

    def test_any_day_in_active_month_is_candidate(self):
        assert self._mask(["2024-03-01", "2024-03-15", "2024-12-05"]).all()

    def test_last_week_before_active_month_is_candidate(self):
        # Feb 2024 has 29 days, so its last 7 days start on the 23rd; April has
        # 30, so its last 7 start on the 24th. Both precede active months.
        assert self._mask(["2024-02-23", "2024-02-26", "2024-04-28"]).all()

    def test_ordinary_days_are_not_candidates(self):
        mask = self._mask(["2024-01-15", "2024-02-10", "2024-04-15", "2024-10-20"])
        assert not mask.any()

    def test_month_before_inactive_month_is_not_candidate(self):
        # Late January precedes February, which is not an active month.
        assert not self._mask(["2024-01-31"]).any()

    def test_result_is_boolean_and_indexed_by_input_dates(self):
        dates = pd.DatetimeIndex(pd.to_datetime(["2024-03-15", "2024-01-15"]))
        mask = is_roll_candidate(dates)
        assert mask.dtype == bool
        assert list(mask.index) == list(dates)


def _prices_with_jumps(
    start: str = "2024-01-01", periods: int = 90, jumps: dict | None = None
) -> pd.Series:
    """Synthetic price series: +/-0.01 alternating daily noise plus optional
    one-day jumps (a level shift, like a contract splice) on given dates."""
    dates = pd.bdate_range(start, periods=periods)
    changes = pd.Series(
        np.where(np.arange(periods) % 2 == 0, 0.01, -0.01), index=dates
    )
    for day, size in (jumps or {}).items():
        changes.loc[pd.Timestamp(day)] += size
    return pd.Series(4.0 + changes.cumsum(), index=dates, name="hg")


class TestFlagRollDays:
    def test_jump_inside_roll_window_is_flagged(self):
        prices = _prices_with_jumps(jumps={"2024-02-27": 0.30})
        flags = flag_roll_days(prices)
        assert flags.loc[pd.Timestamp("2024-02-27")]
        assert flags.sum() == 1

    def test_same_jump_outside_roll_window_is_not_flagged(self):
        # Feb 15 is a normal mid-month day: a jump there is a real market
        # move (or bad data), not a roll — the calendar filter must hold.
        prices = _prices_with_jumps(jumps={"2024-02-15": 0.30})
        flags = flag_roll_days(prices)
        assert not flags.loc[pd.Timestamp("2024-02-15")]
        assert flags.sum() == 0

    def test_quiet_days_inside_window_are_not_flagged(self):
        prices = _prices_with_jumps()  # no jumps anywhere
        assert flag_roll_days(prices).sum() == 0

    def test_insufficient_history_means_no_flag(self):
        # Series starts ~6 business days before the jump: too little history
        # to call anything abnormal.
        prices = _prices_with_jumps(
            start="2024-02-19", periods=30, jumps={"2024-02-27": 0.30}
        )
        assert flag_roll_days(prices).sum() == 0

    def test_flags_are_indexed_like_price_changes(self):
        prices = _prices_with_jumps()
        flags = flag_roll_days(prices)
        assert list(flags.index) == list(prices.index[1:])
        assert flags.dtype == bool

    def test_no_lookahead_future_data_cannot_change_past_flags(self):
        # Rewriting the future must not change any already-computed flag.
        prices = _prices_with_jumps(jumps={"2024-02-27": 0.30})
        full = flag_roll_days(prices)
        perturbed = prices.copy()
        perturbed.loc[pd.Timestamp("2024-03-20"):] += 5.0  # violent fake future
        cutoff = pd.Timestamp("2024-03-15")
        assert flag_roll_days(perturbed).loc[:cutoff].equals(full.loc[:cutoff])
