"""Tests for the data layer: unit conversion and calendar alignment."""

import numpy as np
import pandas as pd
import pytest

from copper_hedge.data import (
    LB_PER_TONNE,
    align_daily,
    usd_per_tonne_to_usd_per_lb,
)


class TestUnitConversion:
    def test_lb_per_tonne_constant(self):
        assert LB_PER_TONNE == pytest.approx(2204.62)

    def test_one_tonne_price_converts_to_one_lb_price(self):
        assert usd_per_tonne_to_usd_per_lb(2204.62) == pytest.approx(1.0)

    def test_series_conversion_is_vectorized(self):
        prices_tonne = pd.Series([8818.48, 11023.10], name="lme")
        result = usd_per_tonne_to_usd_per_lb(prices_tonne)
        expected = pd.Series([4.0, 5.0], name="lme")
        pd.testing.assert_series_equal(result, expected)

    def test_realistic_lme_price_lands_in_dollars_per_lb_range(self):
        # ~$9,000/tonne copper should be ~$4.08/lb, not $9,000 or $0.004
        assert usd_per_tonne_to_usd_per_lb(9000.0) == pytest.approx(4.0823, abs=1e-3)


def _series(dates: list[str], values: list[float], name: str) -> pd.Series:
    return pd.Series(values, index=pd.to_datetime(dates), name=name)


class TestAlignment:
    def test_inner_join_keeps_only_common_days(self):
        a = _series(["2024-01-01", "2024-01-02", "2024-01-03"], [1.0, 2.0, 3.0], "a")
        b = _series(["2024-01-02", "2024-01-03", "2024-01-04"], [10.0, 20.0, 30.0], "b")
        aligned, dropped = align_daily({"a": a, "b": b})
        assert list(aligned.index) == list(pd.to_datetime(["2024-01-02", "2024-01-03"]))
        assert list(aligned.columns) == ["a", "b"]
        assert aligned["a"].tolist() == [2.0, 3.0]
        assert aligned["b"].tolist() == [10.0, 20.0]

    def test_reports_dropped_row_count_per_series(self):
        # a has 3 rows (1 unique to it), b has 4 rows (2 unique to it)
        a = _series(["2024-01-01", "2024-01-02", "2024-01-03"], [1.0, 2.0, 3.0], "a")
        b = _series(
            ["2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"],
            [10.0, 20.0, 30.0, 40.0],
            "b",
        )
        _, dropped = align_daily({"a": a, "b": b})
        assert dropped == {"a": 1, "b": 2}

    def test_nan_values_are_dropped_not_filled(self):
        # A NaN on a common day must remove that day entirely — no forward-fill.
        a = _series(["2024-01-01", "2024-01-02", "2024-01-03"], [1.0, np.nan, 3.0], "a")
        b = _series(["2024-01-01", "2024-01-02", "2024-01-03"], [10.0, 20.0, 30.0], "b")
        aligned, dropped = align_daily({"a": a, "b": b})
        assert list(aligned.index) == list(pd.to_datetime(["2024-01-01", "2024-01-03"]))
        assert not aligned.isna().any().any()
        # b lost 2024-01-02 because a had no usable value there
        assert dropped["b"] == 1

    def test_three_way_alignment(self):
        a = _series(["2024-01-01", "2024-01-02", "2024-01-03"], [1.0, 2.0, 3.0], "a")
        b = _series(["2024-01-02", "2024-01-03", "2024-01-04"], [10.0, 20.0, 30.0], "b")
        c = _series(["2024-01-03", "2024-01-04", "2024-01-05"], [7.0, 8.0, 9.0], "c")
        aligned, dropped = align_daily({"a": a, "b": b, "c": c})
        assert list(aligned.index) == list(pd.to_datetime(["2024-01-03"]))
        assert dropped == {"a": 2, "b": 2, "c": 2}

    def test_result_is_sorted_by_date(self):
        a = _series(["2024-01-03", "2024-01-01", "2024-01-02"], [3.0, 1.0, 2.0], "a")
        b = _series(["2024-01-02", "2024-01-03", "2024-01-01"], [20.0, 30.0, 10.0], "b")
        aligned, _ = align_daily({"a": a, "b": b})
        assert aligned.index.is_monotonic_increasing
        assert aligned["a"].tolist() == [1.0, 2.0, 3.0]


class TestLoadAligned:
    def _write_csvs(self, d):
        pd.DataFrame(
            {
                "date": ["2024-01-01", "2024-01-02", "2024-01-03"],
                "lme_cash_usd_per_tonne": [8818.48, 8818.48, 8818.48],
                "lme_cash_usd_per_lb": [4.0, 4.0, 4.0],
            }
        ).to_csv(d / "lme_cash_settlement.csv", index=False)
        pd.DataFrame(
            {
                "date": ["2024-01-02", "2024-01-03", "2024-01-04"],
                "hg_usd_per_lb": [3.9, 3.95, 4.0],
            }
        ).to_csv(d / "hg_front_month.csv", index=False)
        pd.DataFrame(
            {
                "date": ["2024-01-02", "2024-01-03"],
                "cper_usd_per_share": [25.0, 25.5],
            }
        ).to_csv(d / "cper.csv", index=False)

    def test_loads_and_aligns_three_committed_csvs(self, tmp_path):
        from copper_hedge.data import load_aligned

        self._write_csvs(tmp_path)
        aligned, dropped = load_aligned(tmp_path)
        assert list(aligned.columns) == [
            "lme_usd_per_lb",
            "hg_usd_per_lb",
            "cper_usd_per_share",
        ]
        assert len(aligned) == 2
        assert dropped == {"lme_usd_per_lb": 1, "hg_usd_per_lb": 1, "cper_usd_per_share": 0}
        assert aligned["lme_usd_per_lb"].iloc[0] == pytest.approx(4.0)


class TestNormalizeToStart:
    def test_each_column_starts_at_one(self):
        from copper_hedge.data import normalize_to_start

        df = pd.DataFrame(
            {"a": [2.0, 4.0, 6.0], "b": [10.0, 5.0, 20.0]},
            index=pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"]),
        )
        norm = normalize_to_start(df)
        assert norm.iloc[0].tolist() == [1.0, 1.0]
        assert norm["a"].tolist() == [1.0, 2.0, 3.0]
        assert norm["b"].tolist() == [1.0, 0.5, 2.0]
