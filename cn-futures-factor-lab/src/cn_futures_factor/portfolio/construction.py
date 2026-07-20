"""横截面多空组合构建。"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from cn_futures_factor.exceptions import ConfigurationError, InsufficientDataError


def build_long_short_positions(
    scores: pd.DataFrame,
    portfolio_config: dict[str, Any],
    *,
    score_column: str = "prediction",
) -> pd.DataFrame:
    """按每日横截面排名构造等权多空仓位。

    输出保留所有当日品种，包括权重为零的品种。这样某品种离开多空组时，回测器能够
    正确记录平仓换手，而不会因为该行消失而漏算成本。
    """

    if score_column not in scores:
        raise ConfigurationError(f"预测分数字段不存在：{score_column}")

    long_fraction = float(portfolio_config.get("long_fraction", 0.2))
    short_fraction = float(portfolio_config.get("short_fraction", 0.2))
    gross_exposure = float(portfolio_config.get("gross_exposure", 1.0))
    minimum_products = int(portfolio_config.get("minimum_products", 5))
    if not 0 < long_fraction < 0.5 or not 0 < short_fraction < 0.5:
        raise ConfigurationError("多头和空头比例必须位于 0 与 0.5 之间")
    if gross_exposure <= 0:
        raise ConfigurationError("gross_exposure 必须为正数")

    output: list[pd.DataFrame] = []
    valid_dates = 0
    for trade_date, date_rows in scores.groupby("trade_date", sort=True):
        date_rows = date_rows.copy()
        date_rows["weight"] = 0.0
        eligible = date_rows.dropna(subset=[score_column]).sort_values(
            [score_column, "product"], ascending=[False, True], kind="stable"
        )
        count = len(eligible)
        if count < minimum_products:
            continue

        number_long = max(1, int(np.floor(count * long_fraction)))
        number_short = max(1, int(np.floor(count * short_fraction)))
        if number_long + number_short > count:
            number_short = count - number_long
        if number_short < 1:
            continue

        long_products = set(eligible.iloc[:number_long]["product"])
        short_products = set(eligible.iloc[-number_short:]["product"])
        long_weight = gross_exposure / 2.0 / number_long
        short_weight = -gross_exposure / 2.0 / number_short
        date_rows.loc[date_rows["product"].isin(long_products), "weight"] = long_weight
        date_rows.loc[date_rows["product"].isin(short_products), "weight"] = short_weight
        date_rows["trade_date"] = trade_date
        output.append(date_rows)
        valid_dates += 1

    if not output:
        raise InsufficientDataError(
            f"没有任何日期拥有至少 {minimum_products} 个有效预测分数，请检查历史长度"
        )

    positions = pd.concat(output, ignore_index=True)
    positions["side"] = np.select(
        [positions["weight"] > 0, positions["weight"] < 0],
        ["long", "short"],
        default="flat",
    )
    positions.attrs["valid_dates"] = valid_dates
    return positions.sort_values(["trade_date", "product"], kind="stable").reset_index(drop=True)
