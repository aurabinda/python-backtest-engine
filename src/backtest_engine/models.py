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

