from datetime import date

from backtest_engine.execution import SimulatedBroker
from backtest_engine.models import Bar, OrderEvent, Side


def test_buy_fill_includes_adverse_slippage_and_commission() -> None:
    bar = Bar(date(2024, 1, 2), "ABC", 100, 101, 99, 100, 1_000)
    fill = SimulatedBroker(commission_per_order=1.5, slippage_bps=10).fill(
        OrderEvent(bar.timestamp, "ABC", Side.BUY, 10), bar
    )
    assert fill.price == 100.1
    assert fill.commission == 1.5

