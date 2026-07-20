"""生成未来收益标签。

标签包含未来信息，只能作为训练目标或评价结果，绝不能重新进入因子计算。
"""

from __future__ import annotations

import pandas as pd


def add_forward_return_labels(
    features: pd.DataFrame,
    horizons: tuple[int, ...] = (1, 5, 20),
) -> pd.DataFrame:
    """根据连续研究价格添加多个期限的未来收益。"""

    result = features.sort_values(["product", "trade_date"], kind="stable").copy()
    grouped_price = result.groupby("product", sort=False)["continuous_close"]
    for horizon in horizons:
        if horizon < 1:
            raise ValueError("标签期限必须是正整数")
        future_price = grouped_price.shift(-horizon)
        result[f"target_return_{horizon}d"] = future_price / result["continuous_close"] - 1.0
    return result.sort_values(["trade_date", "product"], kind="stable").reset_index(drop=True)
