import math

import pandas as pd
import pytest

from cn_futures_factor.evaluation.metrics import calculate_metrics


def test_sharpe_uses_arithmetic_mean_instead_of_cagr() -> None:
    returns = pd.Series([0.01, -0.005, 0.002, 0.004], dtype=float)
    nav = (1.0 + returns).cumprod()
    daily = pd.DataFrame(
        {
            "net_return": returns,
            "nav": nav,
            "drawdown": nav / nav.cummax() - 1.0,
            "rebalance_turnover": 0.0,
            "roll_turnover": 0.0,
            "transaction_cost": 0.0,
        }
    )

    metrics = calculate_metrics(daily, annualization_days=252)
    expected_sharpe = returns.mean() / returns.std(ddof=1) * math.sqrt(252)

    assert metrics["sharpe"] == pytest.approx(expected_sharpe)
    assert metrics["annualized_mean_return"] == pytest.approx(returns.mean() * 252)
    assert metrics["annual_return"] != pytest.approx(metrics["annualized_mean_return"])
