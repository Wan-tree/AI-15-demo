import pandas as pd
import pytest

from cn_futures_factor.evaluation.robustness import (
    summarize_cost_scenarios,
    summarize_research_periods,
)


def _daily_result() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "trade_date": pd.to_datetime(
                ["2022-12-30", "2023-01-03", "2023-01-04", "2023-01-05"]
            ),
            "gross_return": [0.10, -0.10, 0.05, 0.02],
            "rebalance_turnover": [1.0, 1.0, 1.0, 1.0],
            "roll_turnover": [0.0, 0.0, 0.0, 0.0],
            "transaction_cost": [0.0, 0.0, 0.0, 0.0],
            "net_return": [0.10, -0.10, 0.05, 0.02],
            "nav": [1.10, 0.99, 1.0395, 1.06029],
            "drawdown": [0.0, -0.10, -0.055, -0.0361],
        }
    )


def test_period_metrics_restart_nav_inside_each_period() -> None:
    periods = {
        "train": {"start": "2022-01-01", "end": "2022-12-31"},
        "validation": {"start": "2023-01-01", "end": "2023-12-31"},
    }

    result = summarize_research_periods(_daily_result(), periods, annualization_days=252)
    validation = result.loc[result["period"].eq("validation")].iloc[0]

    # 验证期应只复合 -10%、+5%、+2%，不能继承训练期先涨 10% 的净值。
    assert validation["total_return"] == pytest.approx(0.9 * 1.05 * 1.02 - 1.0)


def test_higher_cost_scenario_cannot_improve_the_same_positions() -> None:
    scenarios = {
        "low": {"rebalance_bps": 1.0, "roll_bps": 1.0},
        "high": {"rebalance_bps": 20.0, "roll_bps": 20.0},
    }

    result = summarize_cost_scenarios(_daily_result(), scenarios, annualization_days=252)
    returns = result.set_index("scenario")["total_return"]

    assert returns["high"] < returns["low"]
