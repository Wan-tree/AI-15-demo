"""配置驱动的因子计算流水线。"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from cn_futures_factor.exceptions import ConfigurationError
from cn_futures_factor.features.base import FactorDefinition
from cn_futures_factor.features.technical import (
    liquidity,
    momentum,
    open_interest_change,
    reversal,
    volatility,
)

FACTOR_REGISTRY: dict[str, FactorDefinition] = {
    "momentum_20": FactorDefinition("momentum_20", momentum, "20 日动量"),
    "momentum_60": FactorDefinition("momentum_60", momentum, "60 日动量"),
    "reversal_5": FactorDefinition("reversal_5", reversal, "5 日反转"),
    "volatility_20": FactorDefinition(
        "volatility_20", volatility, "20 日年化波动率", higher_is_better=False
    ),
    "liquidity_20": FactorDefinition("liquidity_20", liquidity, "20 日平均流动性"),
    "open_interest_change_20": FactorDefinition(
        "open_interest_change_20", open_interest_change, "20 日持仓量变化"
    ),
}


def compute_features(panel: pd.DataFrame, factor_config: dict[str, Any]) -> pd.DataFrame:
    """在连续主力面板上计算所有启用因子。

    因子按品种独立计算，结果保持宽表结构。宽表方便机器学习；如果未来需要因子库，
    可以在存储层将其转换成长表，而无需修改单个因子函数。
    """

    required = {"trade_date", "product", "continuous_close", "continuous_return"}
    missing = required.difference(panel.columns)
    if missing:
        raise ConfigurationError(f"因子输入缺少字段：{sorted(missing)}")

    result = panel.sort_values(["product", "trade_date"], kind="stable").copy()
    configured = factor_config.get("factors", {})
    for factor_name, settings in configured.items():
        if not settings.get("enabled", True):
            continue
        if factor_name not in FACTOR_REGISTRY:
            raise ConfigurationError(f"配置了尚未注册的因子：{factor_name}")
        lookback = int(settings["lookback"])
        if lookback < 2:
            raise ConfigurationError(f"因子 {factor_name} 的 lookback 必须至少为 2")

        definition = FACTOR_REGISTRY[factor_name]
        values = result.groupby("product", sort=False, group_keys=False).apply(
            lambda group, fn=definition.function, window=lookback: fn(group, window),
            include_groups=False,
        )
        # groupby.apply 在不同 pandas 版本可能返回多层索引。按原始行索引对齐可以避免
        # 将某个品种的因子写到另一个品种上。
        if isinstance(values.index, pd.MultiIndex):
            values.index = values.index.get_level_values(-1)
        result[factor_name] = values.reindex(result.index).replace([np.inf, -np.inf], np.nan)

    return result.sort_values(["trade_date", "product"], kind="stable").reset_index(drop=True)
