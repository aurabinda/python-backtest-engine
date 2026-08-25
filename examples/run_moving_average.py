from pathlib import Path

from backtest_engine.analytics import summary
from backtest_engine.data import load_daily_bars
from backtest_engine.engine import BacktestEngine
from backtest_engine.portfolio import Portfolio
from backtest_engine.strategy import MovingAverageCrossStrategy


bars = load_daily_bars(Path(__file__).with_name("sample_prices.csv"), "DEMO")
engine = BacktestEngine(MovingAverageCrossStrategy(), Portfolio(initial_cash=100_000))
engine.run(bars)

for metric, value in summary(engine.equity_curve).items():
    print(f"{metric:>24}: {value: .2%}" if "ratio" not in metric else f"{metric:>24}: {value: .2f}")

