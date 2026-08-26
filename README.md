# Python Backtest Engine

A compact, event-driven backtesting engine designed to demonstrate production-minded quantitative software design: clear domain models, deterministic execution assumptions, transaction costs, portfolio accounting, pluggable strategies, research parameterisation, and testable analytics.

> Educational software only. It is not investment advice and should not be used for live trading without substantially more validation, controls, and market-data handling.

## What it demonstrates

- Explicit `MarketEvent`, `SignalEvent`, `OrderEvent`, and `FillEvent` models
- Long-only portfolio accounting with cash, positions, equity and realised costs
- Pluggable strategy interface
- Moving-average crossover strategy
- Three-moving-average trend filter inspired by the EPAT backtesting exercise
- RSI mean-reversion strategy with overbought/oversold, take-profit and stop-loss exits
- Donchian breakout strategy using prior high/low channels
- Deterministic next-bar execution with configurable commission and slippage
- Core analytics: total return, annualised volatility, Sharpe ratio and maximum drawdown
- A research-oriented `run_strategy` helper for isolated strategy runs

## Strategy suite

The `feature/epat-strategy-suite` branch extends the original moving-average example with four reusable strategy implementations:

| Strategy | Core idea | Parameters |
|---|---|---|
| `MovingAverageCrossStrategy` | Fast/slow trend crossover | fast/slow windows |
| `ThreeMovingAverageStrategy` | Price above short/medium/long averages | 3 windows |
| `RSIMeanReversionStrategy` | Buy oversold, exit on overbought/target/stop | RSI period, thresholds, TP, SL |
| `DonchianBreakoutStrategy` | Break previous high channel, exit below low channel | entry/exit windows |

The strategy layer is deliberately separated from the engine. A strategy emits a target position; the engine turns that into an order, applies the simulated execution model, and updates the portfolio.

## EPAT alignment

The strategy suite captures the main reusable ideas from the supplied backtesting material without copying the notebook structure directly:

- multi-moving-average signal generation
- RSI entry/exit logic
- percentage take-profit and stop-loss controls
- breakout channels based on prior observations
- strategy return evaluation and parameter research

The implementation uses pure Python for the indicators so that the core package does not require TA-Lib. Yahoo Finance remains an optional research-data source through the existing data adapter.

## Architecture

```text
market-data adapter
        |
        v
     Strategy
        |
        v
      Signal
        |
        v
      Order
        |
        v
 simulated broker
        |
        v
       Fill
        |
        v
    Portfolio
        |
        v
    Analytics
```

The engine uses next-bar execution assumptions. Strategy signals are generated from information available on the current bar and are passed to the broker using the engine's deterministic execution model. This keeps the research design explicit and provides a foundation for later work on order types, intrabar execution and more realistic market microstructure.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
python examples/run_moving_average.py TSLA
pytest
```

## Roadmap

1. Add strategy-specific tests and deterministic fixtures.
2. Add a reusable parameter-grid research layer and visual parameter surfaces.
3. Add richer execution models: spread, market/limit orders and partial fills.
4. Add risk controls and position sizing.
5. Add multi-asset portfolios.
6. Add event-driven research and performance reporting.
