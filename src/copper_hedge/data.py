"""Data layer: fetching, cleaning, unit conversion, and calendar alignment.

Unit conventions (see SPEC.md):
- All hedging math runs in USD per pound ($/lb).
- LME prices arrive in $/tonne and are divided by LB_PER_TONNE (2,204.62 lb).
- CPER stays in $/share (user decision, 2026-08-13): no physical $/lb exists
  for an ETF share, and effectiveness numbers are scale-invariant.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup

LB_PER_TONNE: float = 2204.62
COMEX_CONTRACT_LB: int = 25_000


def usd_per_tonne_to_usd_per_lb(price_usd_per_tonne):
    """Convert a price (scalar or Series) from $/tonne to $/lb."""
    return price_usd_per_tonne / LB_PER_TONNE


def align_daily(
    series_map: dict[str, pd.Series],
) -> tuple[pd.DataFrame, dict[str, int]]:
    """Inner-join daily series on common trading days.

    NaN values are dropped from each series before joining, so a missing value
    on one leg removes that day from the aligned dataset — never forward-filled.

    Returns the aligned DataFrame (sorted by date, one column per input name)
    and a per-series count of rows dropped by the join.
    """
    cleaned = {name: s.dropna().sort_index() for name, s in series_map.items()}

    common = None
    for s in cleaned.values():
        common = s.index if common is None else common.intersection(s.index)
    if common is None:
        raise ValueError("align_daily needs at least one series")

    aligned = pd.DataFrame({name: s.loc[common] for name, s in cleaned.items()})
    aligned = aligned.sort_index()

    dropped = {name: len(s) - len(common) for name, s in cleaned.items()}
    return aligned, dropped


def parse_westmetall_table(html: str) -> pd.Series:
    """Parse a Westmetall market-data year page into a daily price series.

    Extracts the date and LME Copper Cash-Settlement columns ($/tonne).
    Rows whose price cell is not a number (holidays shown as "-") are skipped.
    """
    soup = BeautifulSoup(html, "html.parser")
    records: dict[pd.Timestamp, float] = {}
    for row in soup.find_all("tr"):
        cells = row.find_all("td")
        if len(cells) < 2:
            continue
        date_text = cells[0].get_text(strip=True)
        price_text = cells[1].get_text(strip=True).replace(",", "")
        try:
            date = pd.to_datetime(date_text, format="%d. %B %Y")
            price = float(price_text)
        except ValueError:
            continue
        records[date] = price
    series = pd.Series(records, name="lme_cash_usd_per_tonne").sort_index()
    series.index.name = "date"
    return series


def _read_csv_series(path: Path, column: str) -> pd.Series:
    df = pd.read_csv(path, parse_dates=["date"], index_col="date")
    return df[column]


def load_aligned(data_dir: Path) -> tuple[pd.DataFrame, dict[str, int]]:
    """Load the three committed CSVs and inner-join them on common trading days.

    Columns of the result: lme_usd_per_lb (primary spot leg), hg_usd_per_lb
    (hedge instrument), cper_usd_per_share (secondary spot proxy; stays in
    $/share by logged decision). Returns the aligned frame plus per-series
    dropped-row counts from the calendar join.
    """
    data_dir = Path(data_dir)
    series_map = {
        "lme_usd_per_lb": _read_csv_series(
            data_dir / "lme_cash_settlement.csv", "lme_cash_usd_per_lb"
        ),
        "hg_usd_per_lb": _read_csv_series(data_dir / "hg_front_month.csv", "hg_usd_per_lb"),
        "cper_usd_per_share": _read_csv_series(data_dir / "cper.csv", "cper_usd_per_share"),
    }
    return align_daily(series_map)


def normalize_to_start(df: pd.DataFrame) -> pd.DataFrame:
    """Rescale each column so its first row equals 1.0 (for comparison plots)."""
    return df / df.iloc[0]


def fetch_yfinance_close(ticker: str, start: str) -> pd.Series:
    """Fetch the raw (unadjusted) daily close for a ticker from Yahoo Finance.

    Explicitly passes auto_adjust=False and takes the plain "Close" column:
    HG=F has no dividends/splits so adjustment is a no-op, and CPER has never
    split or distributed, so the raw close is the honest tradable price.
    """
    import yfinance as yf

    df = yf.download(ticker, start=start, auto_adjust=False, progress=False)
    close = df["Close"]
    if isinstance(close, pd.DataFrame):  # yfinance returns MultiIndex columns
        close = close[ticker]
    close.index = pd.to_datetime(close.index).tz_localize(None).normalize()
    close.index.name = "date"
    return close.dropna()
