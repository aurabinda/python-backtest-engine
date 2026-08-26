"""Generate PNG charts from a backtest summary CSV.

Usage:
    python examples/plot_summary.py research/sp500_ma/summary.csv

The script reads only the summary CSV so it can be reused for future universes.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import TypeAlias, Union

import matplotlib.pyplot as plt  # type: ignore[import-not-found]


Row: TypeAlias = dict[str, Union[float, str]]
REQUIRED_COLUMNS = {
    "ticker",
    "total_return",
    "annualised_volatility",
    "sharpe_ratio",
    "max_drawdown",
    "benchmark_total_return",
    "benchmark_sharpe_ratio",
}

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = PROJECT_ROOT / "research" / "sp500_ma" / "summary.csv"


def load_summary(path: Path) -> list[Row]:
    with path.open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    if not rows:
        raise ValueError(f"Summary file contains no rows: {path}")
    missing = REQUIRED_COLUMNS - set(rows[0])
    if missing:
        raise ValueError(f"Summary file is missing columns: {sorted(missing)}")

    parsed: list[Row] = []
    for row in rows:
        if row.get("status", "OK") != "OK":
            continue
        parsed.append(
            {
                "ticker": row["ticker"],
                "total_return": float(row["total_return"]),
                "annualised_volatility": float(row["annualised_volatility"]),
                "sharpe_ratio": float(row["sharpe_ratio"]),
                "max_drawdown": float(row["max_drawdown"]),
                "benchmark_total_return": float(row["benchmark_total_return"]),
                "benchmark_sharpe_ratio": float(row["benchmark_sharpe_ratio"]),
            }
        )
    if not parsed:
        raise ValueError("No successful backtest rows found in summary file")
    return parsed


def save_bar_chart(
    tickers: list[str],
    values: list[float],
    title: str,
    ylabel: str,
    output: Path,
    value_format: str,
) -> None:
    figure, axis = plt.subplots(figsize=(11, 6))
    bars = axis.bar(tickers, values, color="#176b87")
    axis.axhline(0, color="#333333", linewidth=0.8)
    axis.set_title(title)
    axis.set_ylabel(ylabel)
    axis.grid(axis="y", alpha=0.25)
    for bar, value in zip(bars, values):
        axis.annotate(
            value_format.format(value),
            (bar.get_x() + bar.get_width() / 2, value),
            ha="center",
            va="bottom" if value >= 0 else "top",
            xytext=(0, 4 if value >= 0 else -14),
            textcoords="offset points",
        )
    figure.tight_layout()
    figure.savefig(str(output), dpi=160, bbox_inches="tight")
    plt.close(figure)


def save_risk_return_chart(rows: list[Row], output: Path) -> None:
    figure, axis = plt.subplots(figsize=(11, 7))
    for row in rows:
        volatility = float(row["annualised_volatility"]) * 100
        total_return = float(row["total_return"]) * 100
        axis.scatter(volatility, total_return, s=70, color="#e76f51")
        axis.annotate(str(row["ticker"]), (volatility, total_return), xytext=(6, 5), textcoords="offset points")
    axis.axhline(0, color="#333333", linewidth=0.8)
    axis.set_title("Strategy Risk vs Return")
    axis.set_xlabel("Annualised Volatility (%)")
    axis.set_ylabel("Total Return (%)")
    axis.grid(alpha=0.25)
    figure.tight_layout()
    figure.savefig(str(output), dpi=160, bbox_inches="tight")
    plt.close(figure)


def save_dashboard(rows: list[Row], output: Path) -> None:
    rows = sorted(rows, key=lambda row: float(row["total_return"]), reverse=True)
    tickers = [str(row["ticker"]) for row in rows]
    positions = list(range(len(tickers)))
    width = 0.38
    figure, axes = plt.subplots(2, 2, figsize=(14, 10), constrained_layout=True)
    figure.suptitle("Moving Average Crossover Backtest Summary", fontsize=16, fontweight="bold")

    strategy_returns = [float(row["total_return"]) * 100 for row in rows]
    benchmark_returns = [float(row["benchmark_total_return"]) * 100 for row in rows]
    axes[0, 0].bar([position - width / 2 for position in positions], strategy_returns, width, label="Strategy", color="#176b87")
    axes[0, 0].bar([position + width / 2 for position in positions], benchmark_returns, width, label="Buy and hold", color="#f4a261")
    axes[0, 0].set_title("Total Return Comparison")
    axes[0, 0].set_ylabel("Return (%)")
    axes[0, 0].set_xticks(positions, tickers, rotation=45)
    axes[0, 0].legend(frameon=False)

    drawdown = [float(row["max_drawdown"]) * 100 for row in rows]
    axes[0, 1].bar(tickers, drawdown, color="#e76f51")
    axes[0, 1].set_title("Strategy Maximum Drawdown")
    axes[0, 1].set_ylabel("Drawdown (%)")
    axes[0, 1].tick_params(axis="x", rotation=45)

    strategy_sharpe = [float(row["sharpe_ratio"]) for row in rows]
    benchmark_sharpe = [float(row["benchmark_sharpe_ratio"]) for row in rows]
    axes[1, 0].bar([position - width / 2 for position in positions], strategy_sharpe, width, label="Strategy", color="#2a9d8f")
    axes[1, 0].bar([position + width / 2 for position in positions], benchmark_sharpe, width, label="Buy and hold", color="#e9c46a")
    axes[1, 0].set_title("Sharpe Ratio Comparison")
    axes[1, 0].set_ylabel("Sharpe ratio")
    axes[1, 0].set_xticks(positions, tickers, rotation=45)
    axes[1, 0].legend(frameon=False)

    for row in rows:
        volatility = float(row["annualised_volatility"]) * 100
        total_return = float(row["total_return"]) * 100
        axes[1, 1].scatter(volatility, total_return, s=70, color="#176b87")
        axes[1, 1].annotate(str(row["ticker"]), (volatility, total_return), xytext=(5, 4), textcoords="offset points")
    axes[1, 1].set_title("Strategy Risk vs Return")
    axes[1, 1].set_xlabel("Annualised Volatility (%)")
    axes[1, 1].set_ylabel("Total Return (%)")
    axes[1, 1].grid(alpha=0.25)
    figure.savefig(str(output), dpi=160, bbox_inches="tight")
    plt.close(figure)


def main() -> None:
    parser = argparse.ArgumentParser(description="Plot charts from a backtest summary CSV.")
    parser.add_argument("summary_csv", nargs="?", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=None)
    arguments = parser.parse_args()
    rows = load_summary(arguments.summary_csv)
    output_dir = arguments.output_dir or arguments.summary_csv.parent / "charts"
    output_dir.mkdir(parents=True, exist_ok=True)
    by_return = sorted(rows, key=lambda row: float(row["total_return"]), reverse=True)
    tickers = [str(row["ticker"]) for row in by_return]
    save_bar_chart(tickers, [float(row["total_return"]) * 100 for row in by_return], "Total Return by Stock", "Total Return (%)", output_dir / "total_return_by_stock.png", "{:.2f}%")
    save_bar_chart(tickers, [float(row["max_drawdown"]) * 100 for row in by_return], "Maximum Drawdown by Stock", "Maximum Drawdown (%)", output_dir / "max_drawdown_by_stock.png", "{:.2f}%")
    save_bar_chart(tickers, [float(row["sharpe_ratio"]) for row in by_return], "Sharpe Ratio by Stock", "Sharpe Ratio", output_dir / "sharpe_by_stock.png", "{:.2f}")
    save_risk_return_chart(rows, output_dir / "risk_return_scatter.png")
    save_dashboard(rows, output_dir / "summary_dashboard.png")
    print(f"Charts written to: {output_dir}")


if __name__ == "__main__":
    main()
