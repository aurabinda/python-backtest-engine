from __future__ import annotations

from dataclasses import dataclass, field

from .models import FillEvent, Side


@dataclass
class Portfolio:
    initial_cash: float
    cash: float = field(init=False)
    positions: dict[str, int] = field(default_factory=dict)
    total_commissions: float = 0.0

    def __post_init__(self) -> None:
        self.cash = self.initial_cash

    def quantity(self, symbol: str) -> int:
        return self.positions.get(symbol, 0)

    def apply_fill(self, fill: FillEvent) -> None:
        signed_quantity = fill.quantity if fill.side is Side.BUY else -fill.quantity
        cash_change = fill.price * signed_quantity + fill.commission
        if fill.side is Side.BUY and self.cash < cash_change:
            raise ValueError("Insufficient cash for order")
        if fill.side is Side.SELL and self.quantity(fill.symbol) < fill.quantity:
            raise ValueError("Short selling is not enabled")
        self.cash -= cash_change
        self.positions[fill.symbol] = self.quantity(fill.symbol) + signed_quantity
        self.total_commissions += fill.commission

    def equity(self, marks: dict[str, float]) -> float:
        return self.cash + sum(quantity * marks[symbol] for symbol, quantity in self.positions.items())

