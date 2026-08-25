from datetime import date
from types import ModuleType

from backtest_engine.data import download_daily_bars


class FakeHistory:
    empty = False

    def iterrows(self):
        yield date(2024, 1, 2), {
            "Open": 100.0,
            "High": 102.0,
            "Low": 99.0,
            "Close": 101.0,
            "Volume": 1_000,
        }


def test_download_daily_bars_converts_yahoo_history_to_bars(monkeypatch) -> None:
    requested: dict[str, object] = {}

    class FakeTicker:
        def __init__(self, symbol: str) -> None:
            requested["symbol"] = symbol

        def history(self, **kwargs: object) -> FakeHistory:
            requested.update(kwargs)
            return FakeHistory()

    fake_yfinance = ModuleType("yfinance")
    fake_yfinance.Ticker = FakeTicker
    monkeypatch.setitem(__import__("sys").modules, "yfinance", fake_yfinance)

    bars = download_daily_bars("ABC", "2024-01-01", "2024-02-01")

    assert bars[0].timestamp == date(2024, 1, 2)
    assert bars[0].symbol == "ABC"
    assert bars[0].close == 101.0
    assert requested == {
        "symbol": "ABC",
        "start": "2024-01-01",
        "end": "2024-02-01",
        "auto_adjust": False,
        "actions": False,
    }