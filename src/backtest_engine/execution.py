from __future__ import annotations

from dataclasses import dataclass

from .models import Bar, FillEvent, OrderEvent, Side


@dataclass(frozen=True)
class SimulatedBroker:
    commission_per_order: float = 1.00
    slippage_bps: float = 2.0

    def fill(self, order: OrderEvent, bar: Bar) -> FillEvent:
        """Fill at the current bar open, with adverse slippage in basis points."""
        direction = 1 if order.side is Side.BUY else -1
        price = bar.open * (1 + direction * self.slippage_bps / 10_000)
        return FillEvent(order.timestamp, order.symbol, order.side, order.quantity, price, self.commission_per_order)

