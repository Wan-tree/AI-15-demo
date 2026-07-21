import pandas as pd
import pytest

from cn_futures_factor.backtest.engine import run_backtest
from cn_futures_factor.backtest.execution import apply_execution_lag
from cn_futures_factor.exceptions import ConfigurationError
from cn_futures_factor.labels.forward_returns import add_forward_return_labels


def _market_panel() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "trade_date": pd.date_range("2026-01-05", periods=4, freq="B"),
            "product": "RB",
            "contract": "RB2605",
            "forward_return": [0.10, -0.05, 0.02, float("nan")],
            "is_roll_day": False,
            "lagged_volume": [100.0, 100.0, 100.0, 100.0],
            "lagged_open_interest": [200.0, 200.0, 200.0, 200.0],
            "volume": [100.0, 100.0, 100.0, 100.0],
            "open": [100.0, 100.0, 100.0, 100.0],
            "high": [101.0, 101.0, 101.0, 101.0],
            "low": [99.0, 99.0, 99.0, 99.0],
            "close": [100.0, 100.0, 100.0, 100.0],
        }
    )


def test_signal_is_executed_on_next_trading_day() -> None:
    market = _market_panel()
    targets = pd.DataFrame(
        {
            "trade_date": market["trade_date"].iloc[:3],
            "product": "RB",
            "weight": [1.0, -1.0, -1.0],
        }
    )

    result = run_backtest(
        targets,
        market,
        {"rebalance_bps": 0.0, "roll_bps": 0.0},
        execution_lag_days=1,
    )

    first = result.positions.iloc[0]
    assert first["signal_date"] == pd.Timestamp("2026-01-05")
    assert first["trade_date"] == pd.Timestamp("2026-01-06")
    # 第一天的 +10% 已经发生在信号可执行之前，绝不能被计入。
    assert result.daily.iloc[0]["gross_return"] == pytest.approx(-0.05)


def test_lower_frequency_target_is_held_until_next_execution() -> None:
    market = _market_panel()
    targets = pd.DataFrame(
        {
            "trade_date": [market["trade_date"].iloc[0], market["trade_date"].iloc[2]],
            "product": ["RB", "RB"],
            "weight": [1.0, -1.0],
        }
    )

    executable = apply_execution_lag(targets, market, execution_lag_days=1)

    assert executable["trade_date"].tolist() == market["trade_date"].iloc[1:].tolist()
    assert executable["weight"].tolist() == [1.0, 1.0, -1.0]
    assert executable["signal_date"].tolist() == [
        pd.Timestamp("2026-01-05"),
        pd.Timestamp("2026-01-05"),
        pd.Timestamp("2026-01-07"),
    ]


def test_same_day_execution_is_forbidden() -> None:
    market = _market_panel()
    targets = pd.DataFrame(
        {
            "trade_date": [market["trade_date"].iloc[0]],
            "product": ["RB"],
            "weight": [1.0],
        }
    )

    with pytest.raises(ConfigurationError, match="至少为 1"):
        apply_execution_lag(targets, market, execution_lag_days=0)


def test_lagged_liquidity_blocks_untradeable_target() -> None:
    market = _market_panel()
    # 1 月 6 日的实际候选合约在此前交易日没有成交，不能按 1 月 6 日结算价建仓。
    market.loc[1, "lagged_volume"] = 0.0
    targets = pd.DataFrame(
        {
            "trade_date": [market["trade_date"].iloc[0]],
            "product": ["RB"],
            "weight": [1.0],
        }
    )

    executable = apply_execution_lag(
        targets,
        market,
        execution_lag_days=1,
        minimum_lagged_volume=1.0,
        minimum_lagged_open_interest=1.0,
    )

    first = executable.iloc[0]
    assert first["requested_weight"] == pytest.approx(1.0)
    assert first["weight"] == pytest.approx(0.0)
    assert not first["execution_eligible"]
    assert "lagged_volume" in first["execution_exclusion_reason"]


def test_execution_day_without_trades_cannot_create_return() -> None:
    market = _market_panel()
    # 信号在 1 月 5 日形成，昨日流动性看起来正常，但 1 月 6 日最终没有任何成交。
    # 这是成交结果检查，不是把 1 月 6 日信息偷放回 1 月 5 日预测。
    market.loc[1, "volume"] = 0.0
    targets = pd.DataFrame(
        {
            "trade_date": [market["trade_date"].iloc[0]],
            "product": ["RB"],
            "weight": [1.0],
        }
    )

    executable = apply_execution_lag(
        targets,
        market,
        execution_lag_days=1,
        minimum_execution_volume=1.0,
        require_positive_execution_ohlc=True,
    )

    first = executable.iloc[0]
    assert first["requested_weight"] == pytest.approx(1.0)
    assert first["weight"] == pytest.approx(0.0)
    assert not first["execution_eligible"]
    assert "execution_volume" in first["execution_exclusion_reason"]


def test_label_starts_after_execution_lag() -> None:
    features = pd.DataFrame(
        {
            "trade_date": pd.date_range("2026-01-05", periods=4, freq="B"),
            "product": "RB",
            "continuous_close": [100.0, 101.0, 102.0, 104.0],
        }
    )

    labeled = add_forward_return_labels(
        features,
        horizons=(1,),
        execution_lag_days=1,
    )

    assert labeled.loc[0, "target_return_1d"] == pytest.approx(102.0 / 101.0 - 1.0)
    assert labeled.loc[1, "target_return_1d"] == pytest.approx(104.0 / 102.0 - 1.0)
    assert labeled.loc[2:, "target_return_1d"].isna().all()
