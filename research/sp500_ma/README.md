# S&P 500 Moving-Average Research

This folder contains reproducible research outputs from the configurable multi-stock moving-average crossover example.

## Default universe

The runner currently uses these ten large-cap S&P 500 constituents:

- NVDA
- MSFT
- AAPL
- AMZN
- META
- GOOGL
- AVGO
- GOOG
- TSLA
- BRK-B

The universe is deliberately defined in one place in `examples/run_sp500_moving_average.py` so it can be changed without changing the backtest engine.

## Default experiment

- Daily OHLCV data
- 26-Aug-2023 to 26-Aug-2026
- Initial capital: $100,000 per stock
- Fast moving average: 20 days
- Slow moving average: 50 days
- Target position: 100 shares
- Existing engine commission and slippage assumptions
- Each stock is backtested independently with a fresh strategy and portfolio

## Run

```bash
python examples/run_sp500_moving_average.py
```

Or select a different universe/date range:

```bash
python examples/run_sp500_moving_average.py --tickers NVDA MSFT AAPL --start 2024-01-01 --end 2026-01-01
```

Results are written to this directory as `summary.csv` plus one equity-curve CSV per ticker.

> Research only. Historical backtest results do not imply future performance. The current experiment is not a portfolio allocation model and should not be interpreted as investment advice.
