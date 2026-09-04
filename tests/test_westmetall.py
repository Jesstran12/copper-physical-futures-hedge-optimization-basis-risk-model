"""Tests for parsing the Westmetall LME copper cash-settlement table."""

import pandas as pd
import pytest

from copper_hedge.data import parse_westmetall_table

# Mirrors the real page structure: header row, "DD. Month YYYY" dates,
# comma-thousands prices, and a stocks column we must ignore.
FIXTURE_HTML = """
<html><body>
<table>
<tr class="shaded"><th class="text">date</th><th class="text">LME Copper Cash-Settlement</th><th class="text">LME Copper 3-month</th><th class="text last">LME Copper stock</th></tr>
<tr> <td >12. August 2026</td> <td >14,376.00</td> <td >14,201.00</td> <td class="last">212,125</td> </tr>
<tr> <td >11. August 2026</td> <td >14,424.50</td> <td >14,217.00</td> <td class="last">214,550</td> </tr>
<tr> <td >07. August 2026</td> <td >-</td> <td >-</td> <td class="last">-</td> </tr>
<tr> <td >06. January 2026</td> <td >13,269.50</td> <td >13,230.00</td> <td class="last">146,075</td> </tr>
</table>
</body></html>
"""


class TestParseWestmetall:
    def test_parses_dates_and_cash_settlement_in_usd_per_tonne(self):
        s = parse_westmetall_table(FIXTURE_HTML)
        assert s.loc[pd.Timestamp("2026-08-12")] == pytest.approx(14376.00)
        assert s.loc[pd.Timestamp("2026-08-11")] == pytest.approx(14424.50)
        assert s.loc[pd.Timestamp("2026-01-06")] == pytest.approx(13269.50)

    def test_skips_rows_without_a_numeric_price(self):
        s = parse_westmetall_table(FIXTURE_HTML)
        assert pd.Timestamp("2026-08-07") not in s.index
        assert len(s) == 3

    def test_result_sorted_ascending_and_named(self):
        s = parse_westmetall_table(FIXTURE_HTML)
        assert s.index.is_monotonic_increasing
        assert s.name == "lme_cash_usd_per_tonne"
