from __future__ import annotations

from math import sqrt


def summary(equity_curve: list[tuple[object, float]], periods_per_year: int = 252) -> dict[str, float]:
    values = [value for _, value in equity_curve]
    if len(values) < 2:
        raise ValueError("At least two equity observations are required")
    returns = [current / previous - 1 for previous, current in zip(values, values[1:])]
    mean_return = sum(returns) / len(returns)
    variance = sum((item - mean_return) ** 2 for item in returns) / len(returns)
    volatility = sqrt(variance) * sqrt(periods_per_year)
    peak = values[0]
    max_drawdown = 0.0
    for value in values:
        peak = max(peak, value)
        max_drawdown = min(max_drawdown, value / peak - 1)
    return {
        "total_return": values[-1] / values[0] - 1,
        "annualised_volatility": volatility,
        "sharpe_ratio": 0.0 if variance == 0 else mean_return / sqrt(variance) * sqrt(periods_per_year),
        "max_drawdown": max_drawdown,
    }

