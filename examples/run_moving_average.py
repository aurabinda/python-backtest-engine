import argparse
from datetime import date, timedelta

from backtest_engine.analytics import summary
from backtest_engine.data import download_daily_bars
from backtest_engine.engine import BacktestEngine
from backtest_engine.portfolio import Portfolio
from backtest_engine.strategy import MovingAverageCrossStrategy


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a moving-average crossover backtest.")
    parser.add_argument("symbol", nargs="?", default="TSLA", help="Yahoo Finance ticker symbol")
    parser.add_argument("--start", type=date.fromisoformat, help="Inclusive start date (YYYY-MM-DD)")
    parser.add_argument("--end", type=date.fromisoformat, help="Exclusive end date (YYYY-MM-DD)")
    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()
    end_date = arguments.end or date.today()
    start_date = arguments.start or end_date - timedelta(days=730)
    bars = download_daily_bars(arguments.symbol, start=start_date, end=end_date)
    engine = BacktestEngine(MovingAverageCrossStrategy(), Portfolio(initial_cash=100_000))
    engine.run(bars)

    for metric, value in summary(engine.equity_curve).items():
        print(
            f"{metric:>24}: {value: .2%}"
            if "ratio" not in metric
            else f"{metric:>24}: {value: .2f}"
        )


if __name__ == "__main__":
    main()

