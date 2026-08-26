from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Protocol

from .models import Bar, SignalEvent


class Strategy(Protocol):
    """Protocol implemented by all strategies supported by the engine."""

    def on_bar(self, bar: Bar) -> SignalEvent | None:
        ...


def _mean(values: deque[float] | list[float]) -> float:
    return sum(values) / len(values)


def _rsi(closes: list[float], period: int) -> float | None:
    if len(closes) <= period:
        return None
    changes = [closes[i] - closes[i - 1] for i in range(len(closes) - period, len(closes))]
    gains = [max(change, 0.0) for change in changes]
    losses = [max(-change, 0.0) for change in changes]
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    if avg_loss == 0:
        return 100.0
    relative_strength = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + relative_strength))


@dataclass
class MovingAverageCrossStrategy:
    """Long-only fast/slow moving-average crossover."""

    fast_window: int = 3
    slow_window: int = 5
    target_quantity: int = 100
    _closes: deque[float] = field(default_factory=deque, init=False)
    _was_long: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        if self.fast_window >= self.slow_window:
            raise ValueError("fast_window must be smaller than slow_window")

    def on_bar(self, bar: Bar) -> SignalEvent | None:
        self._closes.append(bar.close)
        if len(self._closes) > self.slow_window:
            self._closes.popleft()
        if len(self._closes) < self.slow_window:
            return None
        closes = list(self._closes)
        fast = _mean(closes[-self.fast_window :])
        slow = _mean(closes)
        should_be_long = fast > slow
        if should_be_long == self._was_long:
            return None
        self._was_long = should_be_long
        return SignalEvent(bar.timestamp, bar.symbol, self.target_quantity if should_be_long else 0)


@dataclass
class ThreeMovingAverageStrategy:
    """EPAT-style three moving-average trend filter.

    Enters long when close is above all three averages and exits when that
    condition is lost. This is deliberately long-only so it fits the current
    portfolio implementation without introducing short-selling assumptions.
    """

    short_window: int = 20
    medium_window: int = 40
    long_window: int = 80
    target_quantity: int = 100
    _closes: deque[float] = field(default_factory=deque, init=False)
    _was_long: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        if not 0 < self.short_window < self.medium_window < self.long_window:
            raise ValueError("windows must satisfy 0 < short < medium < long")

    def on_bar(self, bar: Bar) -> SignalEvent | None:
        self._closes.append(bar.close)
        if len(self._closes) > self.long_window:
            self._closes.popleft()
        if len(self._closes) < self.long_window:
            return None
        closes = list(self._closes)
        averages = (
            _mean(closes[-self.short_window :]),
            _mean(closes[-self.medium_window :]),
            _mean(closes),
        )
        should_be_long = all(bar.close >= average for average in averages)
        if should_be_long == self._was_long:
            return None
        self._was_long = should_be_long
        return SignalEvent(bar.timestamp, bar.symbol, self.target_quantity if should_be_long else 0)


@dataclass
class RSIMeanReversionStrategy:
    """Long-only RSI mean-reversion strategy with percentage exits.

    Entry: RSI <= oversold threshold.
    Exit: RSI >= overbought threshold, take-profit, or stop-loss.

    Exits are generated from the current bar and executed by the engine using
    its next-bar execution model, avoiding same-bar look-ahead assumptions.
    """

    period: int = 14
    oversold: float = 30.0
    overbought: float = 70.0
    take_profit: float = 0.05
    stop_loss: float = 0.02
    target_quantity: int = 100
    _closes: list[float] = field(default_factory=list, init=False)
    _entry_price: float | None = field(default=None, init=False)

    def on_bar(self, bar: Bar) -> SignalEvent | None:
        self._closes.append(bar.close)
        if len(self._closes) > self.period + 1:
            self._closes.pop(0)
        rsi = _rsi(self._closes, self.period)
        if rsi is None:
            return None

        if self._entry_price is None and rsi <= self.oversold:
            self._entry_price = bar.close
            return SignalEvent(bar.timestamp, bar.symbol, self.target_quantity)

        if self._entry_price is not None:
            take_profit_hit = bar.close >= self._entry_price * (1 + self.take_profit)
            stop_loss_hit = bar.close <= self._entry_price * (1 - self.stop_loss)
            if rsi >= self.overbought or take_profit_hit or stop_loss_hit:
                self._entry_price = None
                return SignalEvent(bar.timestamp, bar.symbol, 0)

        return None


@dataclass
class DonchianBreakoutStrategy:
    """Long-only Donchian breakout with ATR-style percentage risk controls.

    Entry occurs when the close breaks the previous high channel. Exit occurs
    when the close breaks the previous low channel. The channel is shifted by
    one observation so today's signal never uses today's high/low to define
    the threshold.
    """

    entry_window: int = 20
    exit_window: int = 20
    target_quantity: int = 100
    _highs: deque[float] = field(default_factory=deque, init=False)
    _lows: deque[float] = field(default_factory=deque, init=False)
    _was_long: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        if self.entry_window < 2 or self.exit_window < 2:
            raise ValueError("channel windows must be at least 2")

    def on_bar(self, bar: Bar) -> SignalEvent | None:
        previous_high = max(self._highs) if len(self._highs) >= self.entry_window else None
        previous_low = min(self._lows) if len(self._lows) >= self.exit_window else None

        self._highs.append(bar.high)
        self._lows.append(bar.low)
        if len(self._highs) > self.entry_window:
            self._highs.popleft()
        if len(self._lows) > self.exit_window:
            self._lows.popleft()

        if not self._was_long and previous_high is not None and bar.close > previous_high:
            self._was_long = True
            return SignalEvent(bar.timestamp, bar.symbol, self.target_quantity)

        if self._was_long and previous_low is not None and bar.close < previous_low:
            self._was_long = False
            return SignalEvent(bar.timestamp, bar.symbol, 0)

        return None
