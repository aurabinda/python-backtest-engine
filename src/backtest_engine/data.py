from __future__ import annotations

import csv
from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING

from .models import Bar

if TYPE_CHECKING:
    import pandas as pd


def load_daily_bars(path: str | Path, symbol: str) -> list[Bar]:
    """Load OHLCV data from a CSV with ISO date, open, high, low, close and volume columns."""
    with Path(path).open(newline="") as handle:
        rows = csv.DictReader(handle)
        bars = [
            Bar(
                timestamp=date.fromisoformat(row["date"]),
                symbol=symbol,
                open=float(row["open"]),
                high=float(row["high"]),
                low=float(row["low"]),
                close=float(row["close"]),
                volume=int(row["volume"]),
            )
            for row in rows
        ]
    if not bars:
        raise ValueError("Market data file contains no bars")
    return bars


def download_daily_bars(symbol: str, start: str | date, end: str | date | None = None) -> list[Bar]:
    """Download daily OHLCV bars from Yahoo Finance for use in a backtest."""
    try:
        import yfinance as yf
    except ImportError as error:
        raise ImportError(
            "yfinance is required to download market data. Install the project dependencies first."
        ) from error

    history: pd.DataFrame = yf.Ticker(symbol).history(
        start=start,
        end=end,
        auto_adjust=False,
        actions=False,
    )
    if history.empty:
        raise ValueError(f"Yahoo Finance returned no daily bars for {symbol!r}")

    return [
        Bar(
            timestamp=timestamp.date() if hasattr(timestamp, "date") else timestamp,
            symbol=symbol,
            open=float(row["Open"]),
            high=float(row["High"]),
            low=float(row["Low"]),
            close=float(row["Close"]),
            volume=int(row["Volume"]),
        )
        for timestamp, row in history.iterrows()
    ]

