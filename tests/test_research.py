from datetime import date, timedelta

import pytest

from backtest_engine.engine import run_backtest
from backtest_engine.models import Bar, SignalEvent, TradeRecord
from backtest_engine.research import (
    buy_and_hold,
    parameter_sweep,
    performance_metrics,
    relative_metrics,
    walk_forward,
)
from backtest_engine.strategy import MovingAverageCrossStrategy


def make_bars(symbol: str, closes: list[float]) -> list[Bar]:
    return [
        Bar(date(2024, 1, 1) + timedelta(days=index), symbol, close, close, close, close, 1_000)
        for index, close in enumerate(closes)
    ]


def test_buy_and_hold_and_relative_metrics() -> None:
    bars = make_bars("ABC", [100, 110, 120])
    benchmark = buy_and_hold(bars, initial_cash=1_000)
    strategy = [(timestamp, value) for (timestamp, _), value in zip(benchmark, [1_000, 1_050, 1_100])]

    assert benchmark == [(bars[0].timestamp, 1_000), (bars[1].timestamp, 1_100), (bars[2].timestamp, 1_200)]
    assert relative_metrics(strategy, benchmark)["excess_return"] == pytest.approx(-0.1)


def test_backtest_result_contains_completed_trade_log() -> None:
    class EntryExitStrategy:
        def __init__(self) -> None:
            self.index = 0

        def on_bar(self, bar: Bar) -> SignalEvent:
            self.index += 1
            return SignalEvent(bar.timestamp, bar.symbol, 10 if self.index == 1 else 0)

    result = run_backtest(
        make_bars("ABC", [100, 110]),
        EntryExitStrategy,
        initial_cash=2_000,
    )

    assert len(result.fills) == 2
    assert len(result.trades) == 1
    assert result.trades[0].net_profit == pytest.approx(97.58)


def test_performance_metrics_include_trade_statistics() -> None:
    trade = TradeRecord("ABC", date(2024, 1, 1), date(2024, 1, 3), 10, 100, 110, 1, 1)
    metrics = performance_metrics([(date(2024, 1, 1), 1_000), (date(2024, 1, 2), 1_100)], [trade])

    assert metrics["trade_count"] == 1
    assert metrics["win_rate"] == 1
    assert metrics["total_commissions"] == 2
    assert metrics["cagr"] > 0


def test_parameter_sweep_is_ranked_and_walk_forward_uses_training_data() -> None:
    bars = make_bars("ABC", [100, 100, 100, 100, 100, 110, 90, 90, 90, 90, 90, 100])
    grid = {"fast_window": [2, 3], "slow_window": [4, 5]}

    results = parameter_sweep(bars, MovingAverageCrossStrategy, grid)
    windows = walk_forward(
        bars,
        MovingAverageCrossStrategy,
        grid,
        train_bars=6,
        test_bars=6,
    )

    assert len(results) == 4
    assert results[0].metrics["total_return"] >= results[-1].metrics["total_return"]
    assert len(windows) == 1
    assert windows[0].train_start == bars[0].timestamp
    assert windows[0].test_start == bars[6].timestamp