"""Run the moving-average crossover strategy across a configurable stock universe.

Edit TICKERS to change the research universe. The script runs each ticker independently
using a fresh strategy and portfolio, then writes a summary CSV and per-symbol equity curves.
"""

from __future__ import annotations

import argparse
import csv
from datetime import date
from pathlib import Path

from backtest_engine.analytics import summary
from backtest_engine.data import download_daily_bars
from backtest_engine.engine import run_strategy
from backtest_engine.strategy import MovingAverageCrossStrategy

# Easy-to-change research universe.
# Update this list when you want to test a different set of symbols.
TICKERS = ["NVDA", "MSFT", "AAPL", "AMZN", "META", "GOOGL", "AVGO", "GOOG", "TSLA", "BRK-B"]

START_DATE = date(2023, 8, 26)
END_DATE = date(2026, 8, 26)
INITIAL_CASH = 100_000.0
FAST_WINDOW = 20
SLOW_WINDOW = 50
TARGET_QUANTITY = 100

OUTPUT_DIR = Path("research/sp500_ma")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Backtest moving-average crossover across stocks.")
    parser.add_argument("--start", default=START_DATE.isoformat())
    parser.add_argument("--end", default=END_DATE.isoformat())
    parser.add_argument("--tickers", nargs="+", default=TICKERS)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    start = date.fromisoformat(args.start)
    end = date.fromisoformat(args.end)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    summary_rows: list[dict[str, object]] = []

    for ticker in args.tickers:
        print(f"Running {ticker}: {start} -> {end}")
        try:
            bars = download_daily_bars(ticker, start, end)
            equity_curve = run_strategy(
                bars,
                lambda: MovingAverageCrossStrategy(
                    fast_window=FAST_WINDOW,
                    slow_window=SLOW_WINDOW,
                    target_quantity=TARGET_QUANTITY,
                ),
                initial_cash=INITIAL_CASH,
            )
            metrics = summary(equity_curve)
            summary_rows.append({"ticker": ticker, "status": "OK", **metrics})

            with (OUTPUT_DIR / f"{ticker}_equity_curve.csv").open("w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(["date", "equity"])
                writer.writerows(equity_curve)
        except Exception as error:
            print(f"  FAILED: {error}")
            summary_rows.append({"ticker": ticker, "status": f"FAILED: {error}"})

    fields = [
        "ticker",
        "status",
        "total_return",
        "annualised_volatility",
        "sharpe_ratio",
        "max_drawdown",
    ]
    with (OUTPUT_DIR / "summary.csv").open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(summary_rows)

    print(f"Results written to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
