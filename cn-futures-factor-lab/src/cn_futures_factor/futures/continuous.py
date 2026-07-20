"""构造研究用连续序列和真实合约前瞻收益。"""

from __future__ import annotations

import numpy as np
import pandas as pd

from cn_futures_factor.exceptions import DataValidationError


def build_continuous_panel(
    schedule: pd.DataFrame,
    contract_daily: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """在主力合约映射基础上构造无换月跳点的指数序列。

    方法说明：

    - ``contract_return`` 是所选具体合约从上一结算价到当日结算价的收益；
    - ``continuous_close`` 对这些合约内收益连乘，因此换月当天不会把新旧合约价差误当收益；
    - ``forward_return`` 是当前选中合约从当日到下一交易日的真实可交易收益，供回测使用；
    - 连续价格只用于因子，不能被当作真实成交价。
    """

    required = {"trade_date", "product", "contract", "settlement", "pre_settlement"}
    missing = required.difference(schedule.columns)
    if missing:
        raise DataValidationError(f"连续序列缺少字段：{sorted(missing)}")

    panel = schedule.sort_values(["contract", "trade_date"], kind="stable").copy()

    # 前瞻收益必须先在“完整具体合约行情”中计算，再映射到主力日历。若只在主力表中
    # shift，换月前一天会找不到旧合约的下一日价格。为了兼容旧调用，未提供完整表时
    # 仍可使用 schedule，但正式回测应始终传入 contract_daily。
    source = contract_daily if contract_daily is not None else schedule
    returns = source.sort_values(["contract", "trade_date"], kind="stable").copy()
    if "pre_settlement" not in returns:
        returns["pre_settlement"] = returns.groupby("contract", sort=False)["settlement"].shift(1)
    returns["contract_return"] = returns["settlement"] / returns["pre_settlement"] - 1.0
    returns["forward_return"] = (
        returns.groupby("contract", sort=False)["settlement"].shift(-1) / returns["settlement"]
        - 1.0
    )
    return_columns = returns[["trade_date", "contract", "contract_return", "forward_return"]]
    panel = panel.drop(columns=["contract_return", "forward_return"], errors="ignore").merge(
        return_columns,
        on=["trade_date", "contract"],
        how="left",
        validate="one_to_one",
    )

    panel = panel.sort_values(["product", "trade_date"], kind="stable")
    panel["continuous_return"] = panel["contract_return"].replace([np.inf, -np.inf], np.nan)
    panel["continuous_return"] = panel["continuous_return"].fillna(0.0)
    panel["continuous_close"] = panel.groupby("product", sort=False)["continuous_return"].transform(
        lambda values: 100.0 * (1.0 + values).cumprod()
    )

    return panel.sort_values(["trade_date", "product"], kind="stable").reset_index(drop=True)
