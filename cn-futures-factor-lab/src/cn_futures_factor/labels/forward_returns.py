"""生成未来收益标签。

标签包含未来信息，只能作为训练目标或评价结果，绝不能重新进入因子计算。
"""

from __future__ import annotations

import pandas as pd


def add_forward_return_labels(
    features: pd.DataFrame,
    horizons: tuple[int, ...] = (1, 5, 20),
    *,
    execution_lag_days: int = 1,
) -> pd.DataFrame:
    """根据统一执行滞后生成多个期限的未来收益标签。

    t 日特征对应的标签从 t + execution_lag_days 开始，而不是从尚未可成交的 t 日开始。
    例如滞后 1 日、期限 5 日时，标签为 t+1 到 t+6 的累计收益。
    """

    if execution_lag_days < 1:
        raise ValueError("execution_lag_days 必须至少为 1")

    result = features.sort_values(["product", "trade_date"], kind="stable").copy()
    grouped_price = result.groupby("product", sort=False)["continuous_close"]
    entry_price = grouped_price.shift(-execution_lag_days)
    for horizon in horizons:
        if horizon < 1:
            raise ValueError("标签期限必须是正整数")
        exit_price = grouped_price.shift(-(execution_lag_days + horizon))
        result[f"target_return_{horizon}d"] = exit_price / entry_price - 1.0
    return result.sort_values(["trade_date", "product"], kind="stable").reset_index(drop=True)
