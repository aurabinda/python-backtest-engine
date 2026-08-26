"""Generate PNG charts from a backtest summary CSV.

Usage:
    python examples/plot_summary.py research/sp500_ma/summary.csv

The script intentionally reads only the summary CSV, so it can be reused for
future stock universes and experiments without changing the plotting code.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt


REQUIRED_COLUMNS = {
    "ticker",
    "total_return",
    "annualised_volatility",
    "sharpe_ratio",
    "max_drawdown",
}


def load_summary(path: Path) -> list[dict[str, float | str]]:
    with path.open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))

    if not rows:
        raise ValueError(f"Summary file contains no rows: {path}")

    missing = REQUIRED_COLUMNS - set(rows[0])
    if missing:
        raise ValueError(f"Summary file is missing columns: {sorted(missing)}")

    parsed: list[dict[str, float | str]] = []
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
    value_format: str = "{:.2f}",
) -> None:
    fig, ax = plt.subplots(figsize=(11, 6))
    bars = ax.bar(tickers, values)
    ax.axhline(0, linewidth=0.8)
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.grid(axis="y", alpha=0.25)

    for bar, value in zip(bars, values):
        offset = 4 if value >= 0 else -14
        ax.annotate(
            value_format.format(value),
            (bar.get_x() + bar.get_width() / 2, value),
            ha="center",
            va="bottom" if value >= 0 else "top",
            xytext=(0, offset),
            textcoords="offset points",
        )

    fig.tight_layout()
    fig.savefig(output, dpi=160, bbox_inches="tight")
    plt.close(fig)


def save_risk_return_chart(rows: list[dict[str, float | str]], output: Path) -> None:
    fig, ax = plt.subplots(figsize=(11, 7))

    for row in rows:
        x = float(row["annualised_volatility"]) * 100
        y = float(row["total_return"]) * 100
        ax.scatter(x, y, s=70)
        ax.annotate(str(row["ticker"]), (x, y), xytext=(6, 5), textcoords="offset points")

    ax.axhline(0, linewidth=0.8)
    ax.set_title("Risk vs Return")
    ax.set_xlabel("Annualised Volatility (%)")
    ax.set_ylabel("Total Return (%)")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(output, dpi=160, bbox_inches="tight")
    plt.close(fig)


def save_dashboard(rows: list[dict[str, float | str]], output: Path) -> None:
    rows = sorted(rows, key=lambda row: float(row["total_return"]), reverse=True)
    tickers = [str(row["ticker"]) for row in rows]
    returns = [float(row["total_return"]) * 100 for row in rows]
    sharpe = [float(row["sharpe_ratio"]) for row in rows]
    drawdown = [float(row["max_drawdown"]) * 100 for row in rows]

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("Moving Average Crossover Backtest Summary", fontsize=16)

    axes[0, 0].bar(tickers, returns)
    axes[0, 0].set_title("Total Return")
    axes[0, 0].set_ylabel("Return (%)")
    axes[0, 0].axhline(0, linewidth=0.8)
    axes[0, 0].tick_params(axis="x", rotation=45)

    axes[0, 1].bar(tickers, drawdown)
    axes[0, 1].set_title("Maximum Drawdown")
    axes[0, 1].set_ylabel("Drawdown (%)")
    axes[0, 1].tick_params(axis="x", rotation=45)

    axes[1, 0].bar(tickers, sharpe)
    axes[1, 0].set_title("Sharpe Ratio")
    axes[1, 0].set_ylabel("Sharpe")
    axes[1, 0].axhline(0, linewidth=0.8)
    axes[1, 0].tick_params(axis="x", rotation=45)

    for row in rows:
        x = float(row["annualised_volatility"]) * 100
        y = float(row["total_return"]) * 100
        axes[1, 1].scatter(x, y, s=70)
        axes[1, 1].annotate(str(row["ticker"]), (x, y), xytext=(5, 4), textcoords="offset points")
    axes[1, 1].set_title("Risk vs Return")
    axes[1, 1].set_xlabel("Annualised Volatility (%)")
    axes[1, 1].set_ylabel("Total Return (%)")
    axes[1, 1].grid(alpha=0.25)

    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(output, dpi=160, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description="Plot charts from a backtest summary CSV.")
    parser.add_argument("summary_csv", type=Path)
    parser.add_argument("--output-dir", type=Path, default=None)
    args = parser.parse_args()

    rows = load_summary(args.summary_csv)
    output_dir = args.output_dir or args.summary_csv.parent / "charts"
    output_dir.mkdir(parents=True, exist_ok=True)

    by_return = sorted(rows, key=lambda row: float(row["total_return"]), reverse=True)
    tickers = [str(row["ticker"]) for row in by_return]

    save_bar_chart(
        tickers,
        [float(row["total_return"]) * 100 for row in by_return],
        "Total Return by Stock",
        "Total Return (%)",
        output_dir / "total_return_by_stock.png",
        "{:.2f}%",
    )
    save_bar_chart(
        tickers,
        [float(row["max_drawdown"]) * 100 for row in by_return],
        "Maximum Drawdown by Stock",
        "Maximum Drawdown (%)",
        output_dir / "max_drawdown_by_stock.png",
        "{:.2f}%",
    )
    save_bar_chart(
        tickers,
        [float(row["sharpe_ratio"]) for row in by_return],
        "Sharpe Ratio by Stock",
        "Sharpe Ratio",
        output_dir / "sharpe_by_stock.png",
        "{:.2f}",
    )
    save_risk_return_chart(rows, output_dir / "risk_return_scatter.png")
    save_dashboard(rows, output_dir / "summary_dashboard.png")

    print(f"Charts written to: {output_dir}")


if __name__ == "__main__":
    main()
