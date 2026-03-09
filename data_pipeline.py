"""
Data Pipeline — Pulls macro indicator data from FRED and Yahoo Finance.
Stores results in a unified DataFrame with current values and trend calculations.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from fredapi import Fred
import yfinance as yf
from config import INDICATORS, FRED_API_KEY


def get_fred_client() -> Fred:
    """Initialize FRED API client."""
    return Fred(api_key=FRED_API_KEY)


def fetch_fred_series(fred: Fred, series_id: str, lookback_years: int = 6) -> pd.Series:
    """Fetch a single FRED time series going back `lookback_years`."""
    start = datetime.now() - timedelta(days=lookback_years * 365)
    data = fred.get_series(series_id, observation_start=start)
    data = data.dropna()
    data.index = pd.to_datetime(data.index)
    return data


def fetch_yahoo_series(ticker: str, lookback_years: int = 6) -> pd.Series:
    """Fetch closing prices from Yahoo Finance going back `lookback_years`."""
    start = (datetime.now() - timedelta(days=lookback_years * 365)).strftime("%Y-%m-%d")
    df = yf.download(ticker, start=start, progress=False)
    if df.empty:
        return pd.Series(dtype=float)
    # Handle multi-level columns from yfinance
    if isinstance(df.columns, pd.MultiIndex):
        close = df["Close"].iloc[:, 0]
    else:
        close = df["Close"]
    close.index = pd.to_datetime(close.index)
    return close.dropna()


def compute_cpi_yoy(cpi_series: pd.Series) -> pd.Series:
    """Convert CPI level to year-over-year percent change."""
    return cpi_series.pct_change(periods=12) * 100


def fetch_all_indicators() -> dict[str, pd.Series]:
    """
    Pull all indicator time series. Returns dict mapping indicator key -> pd.Series.
    CPI is converted to YoY % change.
    """
    fred = get_fred_client()
    raw_data = {}

    for key, meta in INDICATORS.items():
        try:
            if meta["source"] == "fred":
                series = fetch_fred_series(fred, meta["ticker"])
            elif meta["source"] == "yahoo":
                series = fetch_yahoo_series(meta["ticker"])
            else:
                continue

            # Special handling: convert CPI level to YoY rate
            if key == "cpi":
                series = compute_cpi_yoy(series)

            raw_data[key] = series
            print(f"  [OK] {meta['name']} — {len(series)} observations")
        except Exception as e:
            print(f"  [FAIL] {meta['name']}: {e}")
            raw_data[key] = pd.Series(dtype=float)

    return raw_data


# ── Trend Calculations ───────────────────────────────────────────────────────

def resample_monthly(series: pd.Series) -> pd.Series:
    """Resample to month-end, taking the last observation."""
    if series.empty:
        return series
    return series.resample("ME").last().dropna()


def calculate_trends(series: pd.Series) -> dict:
    """
    For a given indicator time series, compute:
      - current value
      - 3-month change (momentum)
      - 12-month change (cycle)
      - 5-year trend (structural — 60-month change or long MA delta)
    Returns a dict of computed values.
    """
    monthly = resample_monthly(series)
    if monthly.empty or len(monthly) < 2:
        return {
            "current": np.nan,
            "change_3m": np.nan,
            "change_12m": np.nan,
            "trend_5y": np.nan,
        }

    current = monthly.iloc[-1]

    # 3-month change
    change_3m = current - monthly.iloc[-4] if len(monthly) >= 4 else np.nan

    # 12-month change
    change_12m = current - monthly.iloc[-13] if len(monthly) >= 13 else np.nan

    # 5-year trend (60-month change)
    change_5y = current - monthly.iloc[-61] if len(monthly) >= 61 else np.nan

    return {
        "current": round(current, 2),
        "change_3m": round(change_3m, 2) if not np.isnan(change_3m) else np.nan,
        "change_12m": round(change_12m, 2) if not np.isnan(change_12m) else np.nan,
        "trend_5y": round(change_5y, 2) if not np.isnan(change_5y) else np.nan,
    }


def build_indicator_table(raw_data: dict[str, pd.Series]) -> pd.DataFrame:
    """
    Combine all indicators into a summary DataFrame with columns:
    indicator | pillar | current | change_3m | change_12m | trend_5y
    """
    rows = []
    for key, series in raw_data.items():
        meta = INDICATORS[key]
        trends = calculate_trends(series)
        rows.append(
            {
                "key": key,
                "indicator": meta["name"],
                "pillar": meta["pillar"],
                "source": meta["source"].upper(),
                "current": trends["current"],
                "change_3m": trends["change_3m"],
                "change_12m": trends["change_12m"],
                "trend_5y": trends["trend_5y"],
            }
        )

    df = pd.DataFrame(rows)
    return df


# ── Main convenience function ────────────────────────────────────────────────

def run_pipeline() -> tuple[pd.DataFrame, dict[str, pd.Series]]:
    """
    Full pipeline: fetch data → compute trends → return summary table + raw series.
    """
    print("Fetching macro data...")
    raw = fetch_all_indicators()
    print("\nBuilding indicator table...")
    table = build_indicator_table(raw)
    print("Pipeline complete.\n")
    return table, raw
