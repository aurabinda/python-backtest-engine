from __future__ import annotations

from dataclasses import dataclass, field

from .execution import SimulatedBroker
from .models import Bar, OrderEvent, Side
from .portfolio import Portfolio
from .strategy import MovingAverageCrossStrategy


@dataclass
class BacktestEngine:
    strategy: MovingAverageCrossStrategy
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
                    order = OrderEvent(bar.timestamp, bar.symbol, Side.BUY if delta > 0 else Side.SELL, abs(delta))
                    self.portfolio.apply_fill(self.broker.fill(order, bar))
            self.equity_curve.append((bar.timestamp, self.portfolio.equity({bar.symbol: bar.close})))
        return self.equity_curve

