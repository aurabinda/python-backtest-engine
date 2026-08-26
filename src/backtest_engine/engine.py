from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from .execution import SimulatedBroker
from .models import Bar, FillEvent, OrderEvent, Side, TradeRecord
from .portfolio import Portfolio
from .strategy import Strategy


@dataclass
class BacktestEngine:
    strategy: Strategy
    portfolio: Portfolio
    broker: SimulatedBroker = field(default_factory=SimulatedBroker)
    equity_curve: list[tuple[object, float]] = field(default_factory=list, init=False)
    fills: list[FillEvent] = field(default_factory=list, init=False)
    trades: list[TradeRecord] = field(default_factory=list, init=False)
    _open_entries: dict[str, FillEvent] = field(default_factory=dict, init=False)

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
                    fill = self.broker.fill(order, bar)
                    self.portfolio.apply_fill(fill)
                    self.fills.append(fill)
                    self._record_trade(fill)
            self.equity_curve.append((bar.timestamp, self.portfolio.equity({bar.symbol: bar.close})))
        return self.equity_curve

    def _record_trade(self, fill: FillEvent) -> None:
        if fill.side is Side.BUY:
            self._open_entries[fill.symbol] = fill
            return
        entry = self._open_entries.pop(fill.symbol, None)
        if entry is not None:
            self.trades.append(
                TradeRecord(
                    symbol=fill.symbol,
                    entry_timestamp=entry.timestamp,
                    exit_timestamp=fill.timestamp,
                    quantity=fill.quantity,
                    entry_price=entry.price,
                    exit_price=fill.price,
                    entry_commission=entry.commission,
                    exit_commission=fill.commission,
                )
            )


@dataclass(frozen=True)
class BacktestResult:
    equity_curve: list[tuple[object, float]]
    fills: list[FillEvent]
    trades: list[TradeRecord]


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


def run_backtest(
    bars: list[Bar],
    strategy_factory: Callable[[], Strategy],
    initial_cash: float = 100_000.0,
    broker: SimulatedBroker | None = None,
) -> BacktestResult:
    """Run a strategy and retain its equity curve, fills, and completed trades."""
    engine = BacktestEngine(
        strategy=strategy_factory(),
        portfolio=Portfolio(initial_cash),
        broker=broker or SimulatedBroker(),
    )
    engine.run(bars)
    return BacktestResult(engine.equity_curve, engine.fills, engine.trades)
