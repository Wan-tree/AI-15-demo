"""日频横截面期货回测引擎。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from cn_futures_factor.exceptions import DataValidationError


@dataclass(frozen=True)
class BacktestResult:
    """回测的标准输出，便于报告、测试和未来模型复用。"""

    daily: pd.DataFrame
    positions: pd.DataFrame


def run_backtest(
    positions: pd.DataFrame,
    market_panel: pd.DataFrame,
    cost_config: dict[str, Any],
) -> BacktestResult:
    """使用当日收盘后形成的权重和下一日具体合约收益进行回测。

    ``forward_return`` 定义为当前选中具体合约从 t 到 t+1 的结算价收益。权重在 t 日
    形成，收益在下一交易日实现。最后一个没有前瞻价格的交易日不会进入绩效统计。
    """

    required_positions = {"trade_date", "product", "weight"}
    required_market = {"trade_date", "product", "contract", "forward_return", "is_roll_day"}
    missing_positions = required_positions.difference(positions.columns)
    missing_market = required_market.difference(market_panel.columns)
    if missing_positions or missing_market:
        raise DataValidationError(
            f"回测输入缺少字段：positions={sorted(missing_positions)}, market={sorted(missing_market)}"
        )

    market_columns = [
        "trade_date",
        "product",
        "contract",
        "forward_return",
        "is_roll_day",
    ]
    merged = positions.merge(
        market_panel[market_columns],
        on=["trade_date", "product"],
        how="left",
        validate="many_to_one",
    ).sort_values(["product", "trade_date"], kind="stable")

    merged["previous_weight"] = merged.groupby("product", sort=False)["weight"].shift(1).fillna(0.0)
    merged["weight_change"] = merged["weight"] - merged["previous_weight"]
    merged["gross_contribution"] = merged["weight"] * merged["forward_return"]
    merged["rebalance_turnover_component"] = merged["weight_change"].abs() / 2.0
    merged["roll_turnover_component"] = np.where(
        merged["is_roll_day"], merged["previous_weight"].abs(), 0.0
    )

    # 若某日没有下一交易日价格，则不能假定收益为零。把这些日期排除，避免对绩效产生
    # 向零偏差。正常情况下只有样本最后一天会被排除。
    usable = merged.dropna(subset=["forward_return"]).copy()
    daily = usable.groupby("trade_date", sort=True).agg(
        gross_return=("gross_contribution", "sum"),
        rebalance_turnover=("rebalance_turnover_component", "sum"),
        roll_turnover=("roll_turnover_component", "sum"),
        active_products=("weight", lambda values: int((values != 0).sum())),
    )

    rebalance_rate = float(cost_config.get("rebalance_bps", 0.0)) / 10_000.0
    roll_rate = float(cost_config.get("roll_bps", 0.0)) / 10_000.0
    daily["transaction_cost"] = (
        daily["rebalance_turnover"] * rebalance_rate + daily["roll_turnover"] * roll_rate
    )
    daily["net_return"] = daily["gross_return"] - daily["transaction_cost"]
    daily["nav"] = (1.0 + daily["net_return"]).cumprod()
    daily["drawdown"] = daily["nav"] / daily["nav"].cummax() - 1.0
    daily = daily.reset_index()

    return BacktestResult(daily=daily, positions=merged.reset_index(drop=True))
