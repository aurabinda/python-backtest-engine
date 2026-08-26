from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from math import sqrt
from typing import Callable, Iterable, Mapping

from .analytics import summary
from .engine import BacktestResult, run_backtest
from .models import Bar, TradeRecord
from .strategy import Strategy


def buy_and_hold(
    bars: list[Bar], initial_cash: float = 100_000.0
) -> list[tuple[object, float]]:
    """Create a fully invested, whole-share buy-and-hold equity curve."""
    if not bars:
        raise ValueError("At least one bar is required")
    quantity = int(initial_cash // bars[0].close)
    cash = initial_cash - quantity * bars[0].close
    return [(bar.timestamp, cash + quantity * bar.close) for bar in bars]


def performance_metrics(
    equity_curve: list[tuple[object, float]],
    trades: Iterable[TradeRecord] = (),
    periods_per_year: int = 252,
) -> dict[str, float]:
    """Return portfolio, risk, and trade-level performance metrics."""
    metrics = summary(equity_curve, periods_per_year)
    values = [value for _, value in equity_curve]
    returns = [current / previous - 1 for previous, current in zip(values, values[1:])]
    years = max((len(values) - 1) / periods_per_year, 1 / periods_per_year)
    metrics["cagr"] = (values[-1] / values[0]) ** (1 / years) - 1
    downside = [min(value, 0.0) ** 2 for value in returns]
    downside_deviation = sqrt(sum(downside) / len(returns)) * sqrt(periods_per_year)
    metrics["downside_deviation"] = downside_deviation
    metrics["sortino_ratio"] = (
        0.0 if downside_deviation == 0 else metrics["cagr"] / downside_deviation
    )
    metrics["calmar_ratio"] = (
        0.0
        if metrics["max_drawdown"] == 0
        else metrics["cagr"] / abs(metrics["max_drawdown"])
    )

    completed_trades = list(trades)
    profits = [trade.net_profit for trade in completed_trades]
    wins = [profit for profit in profits if profit > 0]
    losses = [profit for profit in profits if profit < 0]
    metrics["trade_count"] = float(len(completed_trades))
    metrics["win_rate"] = len(wins) / len(profits) if profits else 0.0
    metrics["profit_factor"] = sum(wins) / abs(sum(losses)) if losses else 0.0
    metrics["average_trade_return"] = (
        sum(trade.return_pct for trade in completed_trades) / len(completed_trades)
        if completed_trades
        else 0.0
    )
    metrics["total_commissions"] = sum(
        trade.entry_commission + trade.exit_commission for trade in completed_trades
    )
    return metrics


def relative_metrics(
    strategy_curve: list[tuple[object, float]],
    benchmark_curve: list[tuple[object, float]],
) -> dict[str, float]:
    """Calculate excess return, beta, tracking error, and information ratio."""
    if len(strategy_curve) != len(benchmark_curve):
        raise ValueError("Strategy and benchmark curves must have the same length")
    strategy_returns = [
        current / previous - 1
        for (_, previous), (_, current) in zip(strategy_curve, strategy_curve[1:])
    ]
    benchmark_returns = [
        current / previous - 1
        for (_, previous), (_, current) in zip(benchmark_curve, benchmark_curve[1:])
    ]
    if not strategy_returns:
        raise ValueError("At least two equity observations are required")
    mean_strategy = sum(strategy_returns) / len(strategy_returns)
    mean_benchmark = sum(benchmark_returns) / len(benchmark_returns)
    covariance = sum(
        (strategy - mean_strategy) * (benchmark - mean_benchmark)
        for strategy, benchmark in zip(strategy_returns, benchmark_returns)
    ) / len(strategy_returns)
    benchmark_variance = sum((value - mean_benchmark) ** 2 for value in benchmark_returns) / len(
        benchmark_returns
    )
    active_returns = [strategy - benchmark for strategy, benchmark in zip(strategy_returns, benchmark_returns)]
    tracking_error = sqrt(sum(value * value for value in active_returns) / len(active_returns)) * sqrt(252)
    return {
        "excess_return": strategy_curve[-1][1] / strategy_curve[0][1]
        - benchmark_curve[-1][1] / benchmark_curve[0][1],
        "beta": 0.0 if benchmark_variance == 0 else covariance / benchmark_variance,
        "tracking_error": tracking_error,
        "information_ratio": 0.0
        if tracking_error == 0
        else (mean_strategy - mean_benchmark) * sqrt(252) / tracking_error,
    }


@dataclass(frozen=True)
class WalkForwardWindow:
    train_start: object
    train_end: object
    test_start: object
    test_end: object
    parameters: dict[str, object]
    train_metrics: dict[str, float]
    test_metrics: dict[str, float]


@dataclass(frozen=True)
class ParameterSweepResult:
    parameters: dict[str, object]
    metrics: dict[str, float]


def parameter_sweep(
    bars: list[Bar],
    strategy_factory: Callable[..., Strategy],
    parameter_grid: Mapping[str, Iterable[object]],
    initial_cash: float = 100_000.0,
) -> list[ParameterSweepResult]:
    """Evaluate every combination in a parameter grid, ranked by total return."""
    names = list(parameter_grid)
    combinations = product(*(parameter_grid[name] for name in names))
    results: list[ParameterSweepResult] = []
    for values in combinations:
        parameters = dict(zip(names, values))
        result = run_backtest(bars, lambda parameters=parameters: strategy_factory(**parameters), initial_cash)
        results.append(
            ParameterSweepResult(
                parameters=parameters,
                metrics=performance_metrics(result.equity_curve, result.trades),
            )
        )
    return sorted(results, key=lambda result: result.metrics["total_return"], reverse=True)


def walk_forward(
    bars: list[Bar],
    strategy_factory: Callable[..., Strategy],
    parameter_grid: Mapping[str, Iterable[object]],
    train_bars: int,
    test_bars: int,
    initial_cash: float = 100_000.0,
    step_bars: int | None = None,
) -> list[WalkForwardWindow]:
    """Select parameters in each train window and evaluate them on the next test window."""
    if train_bars < 2 or test_bars < 2:
        raise ValueError("train_bars and test_bars must be at least 2")
    step = step_bars or test_bars
    windows = []
    for start in range(0, len(bars) - train_bars - test_bars + 1, step):
        train = bars[start : start + train_bars]
        test = bars[start + train_bars : start + train_bars + test_bars]
        sweep = parameter_sweep(train, strategy_factory, parameter_grid, initial_cash)
        best_parameters = sweep[0].parameters
        train_result = run_backtest(train, lambda: strategy_factory(**best_parameters), initial_cash)
        test_result: BacktestResult = run_backtest(test, lambda: strategy_factory(**best_parameters), initial_cash)
        windows.append(
            WalkForwardWindow(
                train_start=train[0].timestamp,
                train_end=train[-1].timestamp,
                test_start=test[0].timestamp,
                test_end=test[-1].timestamp,
                parameters=best_parameters,
                train_metrics=performance_metrics(train_result.equity_curve, train_result.trades),
                test_metrics=performance_metrics(test_result.equity_curve, test_result.trades),
            )
        )
    return windows