from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from .execution import SimulatedBroker
from .models import Bar, OrderEvent, Side
from .portfolio import Portfolio
from .strategy import Strategy


@dataclass
class BacktestEngine:
    strategy: Strategy
    portfolio: Portfolio
    broker: SimulatedBroker = field(default_factory=SimulatedBroker)
    equity_curve: list[tuple[object, float]] = field(default_factory=list, init=False)

    def run(self, bars: list[Bar]) -> list[tuple[object, float]]:
        for bar in bars:
            signal = self.strategy.on_bar(bar)
            if signal is not None:
                current = self.portfolio.quantity(signal.symbol)
                delta = signal.target_quantity - current
                if delta:
                    order = OrderEvent(
                        bar.timestamp,
                        bar.symbol,
                        Side.BUY if delta > 0 else Side.SELL,
                        abs(delta),
                    )
                    self.portfolio.apply_fill(self.broker.fill(order, bar))
            self.equity_curve.append((bar.timestamp, self.portfolio.equity({bar.symbol: bar.close})))
        return self.equity_curve


def run_strategy(
    bars: list[Bar],
    strategy_factory: Callable[[], Strategy],
    initial_cash: float = 100_000.0,
    broker: SimulatedBroker | None = None,
) -> list[tuple[object, float]]:
    """Run a fresh strategy instance against the same data.

    A fresh strategy instance is essential for parameter studies because
    strategy state (rolling windows, position state, entry price, etc.) must
    not leak between runs.
    """
    engine = BacktestEngine(
        strategy=strategy_factory(),
        portfolio=Portfolio(initial_cash),
        broker=broker or SimulatedBroker(),
    )
    return engine.run(bars)
