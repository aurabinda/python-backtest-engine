from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

from .models import Bar, SignalEvent


@dataclass
class MovingAverageCrossStrategy:
    fast_window: int = 3
    slow_window: int = 5
    target_quantity: int = 100
    _closes: deque[float] = field(default_factory=deque, init=False)
    _was_long: bool = field(default=False, init=False)

    def on_bar(self, bar: Bar) -> SignalEvent | None:
        self._closes.append(bar.close)
        if len(self._closes) > self.slow_window:
            self._closes.popleft()
        if len(self._closes) < self.slow_window:
            return None
        fast = sum(list(self._closes)[-self.fast_window :]) / self.fast_window
        slow = sum(self._closes) / self.slow_window
        should_be_long = fast > slow
        if should_be_long == self._was_long:
            return None
        self._was_long = should_be_long
        return SignalEvent(bar.timestamp, bar.symbol, self.target_quantity if should_be_long else 0)

