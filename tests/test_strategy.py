from datetime import date, timedelta

import pytest

from backtest_engine.models import Bar
from backtest_engine.strategy import MovingAverageCrossStrategy


@pytest.mark.parametrize(
    ("symbol", "start_date"),
    [
        ("TSLA", date(2024, 1, 2)),
        ("AAPL", date(2023, 6, 1)),
        ("MSFT", date(2022, 10, 3)),
    ],
)
def test_moving_average_strategy_emits_entry_and_exit_for_each_symbol_and_period(
    symbol: str, start_date: date
) -> None:
    closes = [100.0, 100.0, 100.0, 100.0, 100.0, 110.0, 90.0]
    strategy = MovingAverageCrossStrategy()
    signals = []

    for offset, close in enumerate(closes):
        bar = Bar(
            timestamp=start_date + timedelta(days=offset),
            symbol=symbol,
            open=close,
            high=close,
            low=close,
            close=close,
            volume=1_000,
        )
        signal = strategy.on_bar(bar)
        if signal is not None:
            signals.append(signal)

    assert [(signal.symbol, signal.timestamp, signal.target_quantity) for signal in signals] == [
        (symbol, start_date + timedelta(days=5), 100),
        (symbol, start_date + timedelta(days=6), 0),
    ]