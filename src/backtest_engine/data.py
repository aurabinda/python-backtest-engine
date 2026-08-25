from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

from .models import Bar


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

