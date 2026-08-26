from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import StrEnum


class Side(StrEnum):
    BUY = "BUY"
    SELL = "SELL"


@dataclass(frozen=True)
class Bar:
    timestamp: date
    symbol: str
    open: float
    high: float
    low: float
    close: float
    volume: int


@dataclass(frozen=True)
class SignalEvent:
    timestamp: date
    symbol: str
    target_quantity: int


@dataclass(frozen=True)
class OrderEvent:
    timestamp: date
    symbol: str
    side: Side
    quantity: int


@dataclass(frozen=True)
class FillEvent:
    timestamp: date
    symbol: str
    side: Side
    quantity: int
    price: float
    commission: float


@dataclass(frozen=True)
class TradeRecord:
    symbol: str
    entry_timestamp: date
    exit_timestamp: date
    quantity: int
    entry_price: float
    exit_price: float
    entry_commission: float
    exit_commission: float

    @property
    def gross_profit(self) -> float:
        return (self.exit_price - self.entry_price) * self.quantity

    @property
    def net_profit(self) -> float:
        return self.gross_profit - self.entry_commission - self.exit_commission

    @property
    def return_pct(self) -> float:
        return self.net_profit / (self.entry_price * self.quantity)

