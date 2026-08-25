from datetime import date

import pytest

from backtest_engine.models import FillEvent, Side
from backtest_engine.portfolio import Portfolio


def test_fill_updates_cash_position_and_equity() -> None:
    portfolio = Portfolio(initial_cash=1_000)
    portfolio.apply_fill(FillEvent(date(2024, 1, 2), "ABC", Side.BUY, 5, 100, 1))
    assert portfolio.cash == 499
    assert portfolio.quantity("ABC") == 5
    assert portfolio.equity({"ABC": 110}) == 1_049


def test_long_only_portfolio_rejects_short_sale() -> None:
    with pytest.raises(ValueError, match="Short selling"):
        Portfolio(1_000).apply_fill(FillEvent(date(2024, 1, 2), "ABC", Side.SELL, 1, 100, 1))

