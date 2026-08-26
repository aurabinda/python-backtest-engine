"""Run the moving-average crossover strategy across a configurable stock universe.

Edit TICKERS to change the research universe. The script runs each ticker independently
using a fresh strategy and portfolio, then writes a summary CSV and per-symbol equity curves.
"""

from __future__ import annotations

import argparse
import csv
from datetime import date
from pathlib import Path
from typing import cast

from backtest_engine.data import download_daily_bars
from backtest_engine.engine import run_backtest
from backtest_engine.research import (
    buy_and_hold,
    parameter_sweep,
    performance_metrics,
    relative_metrics,
    walk_forward,
)
from backtest_engine.strategy import MovingAverageCrossStrategy

# Easy-to-change research universe.
# Update this list when you want to test a different set of symbols.
TICKERS = ["NVDA", "MSFT", "AAPL", "AMZN", "META", "GOOGL", "AVGO", "GOOG", "TSLA", "BRK-B"]

START_DATE = date(2023, 8, 26)
END_DATE = date(2026, 8, 26)
INITIAL_CASH = 100_000.0
FAST_WINDOW = 3
SLOW_WINDOW = 200
TARGET_QUANTITY = 100
PARAMETER_GRID = {"fast_window": [3, 5, 10], "slow_window": [50, 100, 200]}
TRAIN_DAYS = 252
TEST_DAYS = 63

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "research" / "sp500_ma"


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

            def factory(**parameters: object) -> MovingAverageCrossStrategy:
                return MovingAverageCrossStrategy(
                    fast_window=cast(int, parameters["fast_window"]),
                    slow_window=cast(int, parameters["slow_window"]),
                    target_quantity=TARGET_QUANTITY,
                )

            result = run_backtest(
                bars,
                lambda: factory(fast_window=FAST_WINDOW, slow_window=SLOW_WINDOW),
                initial_cash=INITIAL_CASH,
            )
            benchmark_curve = buy_and_hold(bars, INITIAL_CASH)
            metrics = {
                **performance_metrics(result.equity_curve, result.trades),
                **{f"benchmark_{key}": value for key, value in performance_metrics(benchmark_curve).items()},
                **relative_metrics(result.equity_curve, benchmark_curve),
            }
            summary_rows.append({"ticker": ticker, "status": "OK", **metrics})

            with (OUTPUT_DIR / f"{ticker}_equity_curve.csv").open("w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(["date", "strategy_equity", "benchmark_equity"])
                writer.writerows(
                    (timestamp, strategy_value, benchmark_value)
                    for (timestamp, strategy_value), (_, benchmark_value) in zip(
                        result.equity_curve, benchmark_curve
                    )
                )

            with (OUTPUT_DIR / f"{ticker}_trades.csv").open("w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(
                    [
                        "symbol", "entry_date", "exit_date", "quantity", "entry_price",
                        "exit_price", "entry_commission", "exit_commission", "net_profit",
                    ]
                )
                writer.writerows(
                    (
                        trade.symbol, trade.entry_timestamp, trade.exit_timestamp, trade.quantity,
                        trade.entry_price, trade.exit_price, trade.entry_commission,
                        trade.exit_commission, trade.net_profit,
                    )
                    for trade in result.trades
                )

            sweep_rows = parameter_sweep(bars, factory, PARAMETER_GRID, INITIAL_CASH)
            with (OUTPUT_DIR / f"{ticker}_parameter_sweep.csv").open("w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(["fast_window", "slow_window", "total_return", "sharpe_ratio", "max_drawdown"])
                writer.writerows(
                    (
                        row.parameters["fast_window"], row.parameters["slow_window"],
                        row.metrics["total_return"], row.metrics["sharpe_ratio"],
                        row.metrics["max_drawdown"],
                    )
                    for row in sweep_rows
                )

            walk_forward_rows = walk_forward(
                bars, factory, PARAMETER_GRID, TRAIN_DAYS, TEST_DAYS, INITIAL_CASH
            )
            with (OUTPUT_DIR / f"{ticker}_walk_forward.csv").open("w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(
                    ["train_start", "train_end", "test_start", "test_end", "fast_window",
                     "slow_window", "train_return", "test_return", "test_sharpe_ratio"]
                )
                writer.writerows(
                    (
                        row.train_start, row.train_end, row.test_start, row.test_end,
                        row.parameters["fast_window"], row.parameters["slow_window"],
                        row.train_metrics["total_return"], row.test_metrics["total_return"],
                        row.test_metrics["sharpe_ratio"],
                    )
                    for row in walk_forward_rows
                )
        except Exception as error:
            print(f"  FAILED: {error}")
            summary_rows.append({"ticker": ticker, "status": f"FAILED: {error}"})

    fields = [
        "ticker",
        "status",
        "total_return", "annualised_volatility", "sharpe_ratio", "max_drawdown", "cagr",
        "downside_deviation", "sortino_ratio", "calmar_ratio", "trade_count", "win_rate",
        "profit_factor", "average_trade_return", "total_commissions", "benchmark_total_return",
        "benchmark_annualised_volatility", "benchmark_sharpe_ratio", "benchmark_max_drawdown",
        "benchmark_cagr", "benchmark_downside_deviation", "benchmark_sortino_ratio",
        "benchmark_calmar_ratio", "benchmark_trade_count", "benchmark_win_rate",
        "benchmark_profit_factor", "benchmark_average_trade_return", "benchmark_total_commissions",
        "excess_return", "beta", "tracking_error", "information_ratio",
    ]
    with (OUTPUT_DIR / "summary.csv").open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(summary_rows)

    print(f"Results written to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
