# Python Backtest Engine

A compact, event-driven backtesting engine designed to demonstrate production-minded quantitative software design: clear domain models, deterministic execution assumptions, transaction costs, portfolio accounting, and test coverage.

> Educational software only. It is not investment advice and should not be used for live trading without substantially more validation, controls, and market-data handling.

## What it demonstrates

- Explicit `MarketEvent`, `SignalEvent`, `OrderEvent`, and `FillEvent` models
- Long-only portfolio accounting with cash, positions, equity and realised costs
- Pluggable strategies; the included example is a moving-average crossover
- A deterministic next-bar execution model with configurable commission and slippage
- Core analytics: total return, annualised volatility, Sharpe ratio and maximum drawdown
- Unit tests for costs, execution and portfolio behaviour

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
python examples/run_moving_average.py
pytest
```

## Architecture

```text
CSV bars -> strategy -> signal -> order -> simulated broker -> fill -> portfolio -> analytics
```

The project deliberately keeps its first version dependency-light. Future milestones: multi-asset calendars, corporate actions, order types, risk constraints, market-data adapters, parameter studies and performance reporting.

## Repository roadmap

1. Harden the engine and examples around reproducible data fixtures.
2. Add execution and risk controls appropriate for research backtests.
3. Add a separate research layer rather than mixing notebook logic into the engine.

