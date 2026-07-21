"""使用可观察的历史信息选择每日主力合约。"""

from __future__ import annotations

import pandas as pd

from cn_futures_factor.exceptions import DataValidationError
from cn_futures_factor.futures.contracts import parse_contract_code


def _add_delivery_month(frame: pd.DataFrame) -> pd.DataFrame:
    """解析每条记录的交割年月。

    三位代码需要结合交易日判断十年，因此不能简单地对唯一合约代码做一次映射。
    """

    result = frame.copy()
    result["delivery_yyyymm"] = [
        parse_contract_code(contract, trade_date).delivery_yyyymm
        for contract, trade_date in zip(result["contract"], result["trade_date"], strict=True)
    ]
    return result


def build_main_contract_schedule(
    contract_daily: pd.DataFrame,
    *,
    selector: str = "open_interest",
    selector_lag: int = 1,
    prevent_delivery_month_rollback: bool = True,
) -> pd.DataFrame:
    """构造每日品种到实际合约的映射。

    ``selector_lag=1`` 表示在交易日 t 使用合约在 t-1 的持仓量选择主力合约。
    这避免了使用当天收盘后才完整可知的持仓量，默认值不应随意改成 0。

    为减少主力合约在近远月之间反复跳动，默认不允许选中的交割月份倒退。如果一个品种
    存在特殊交割规则，应在后续通过品种级策略扩展，而不是在这里硬编码例外。
    """

    if selector not in contract_daily:
        raise DataValidationError(f"主力选择字段不存在：{selector}")
    if selector_lag < 1:
        raise DataValidationError("主力合约选择至少滞后 1 个交易日，防止未来信息泄漏")

    required = {"trade_date", "product", "contract", selector}
    missing = required.difference(contract_daily.columns)
    if missing:
        raise DataValidationError(f"构造主力合约缺少字段：{sorted(missing)}")

    frame = contract_daily.sort_values(["contract", "trade_date"], kind="stable").copy()
    frame["selection_value"] = frame.groupby("contract", sort=False)[selector].shift(selector_lag)
    # 执行日能使用的流动性信息也必须来自此前交易日。选中行会把这两列带入主力面板，
    # 供公共执行层阻止在昨日无成交/无持仓的合约上建立仓位。
    if "volume" in frame:
        frame["lagged_volume"] = frame.groupby("contract", sort=False)["volume"].shift(
            selector_lag
        )
    if "open_interest" in frame:
        frame["lagged_open_interest"] = frame.groupby("contract", sort=False)[
            "open_interest"
        ].shift(selector_lag)
    frame = _add_delivery_month(frame)
    candidates = frame.dropna(subset=["selection_value"]).sort_values(
        ["product", "trade_date", "selection_value", "delivery_yyyymm", "contract"],
        ascending=[True, True, False, True, True],
        kind="stable",
    )

    chosen_rows: list[pd.Series] = []
    for _product, product_rows in candidates.groupby("product", sort=False):
        last_delivery: int | None = None
        for _date, date_rows in product_rows.groupby("trade_date", sort=True):
            eligible = date_rows
            if prevent_delivery_month_rollback and last_delivery is not None:
                non_rollback = date_rows[date_rows["delivery_yyyymm"] >= last_delivery]
                if not non_rollback.empty:
                    eligible = non_rollback

            # date_rows 已按 selection_value 降序排列，因此第一行就是最优候选。
            selected = eligible.iloc[0]
            chosen_rows.append(selected)
            last_delivery = int(selected["delivery_yyyymm"])

    if not chosen_rows:
        raise DataValidationError("没有可用于主力合约选择的记录；请检查历史长度和持仓量")

    schedule = (
        pd.DataFrame(chosen_rows)
        .sort_values(["trade_date", "product"], kind="stable")
        .reset_index(drop=True)
    )
    schedule["previous_contract"] = schedule.groupby("product", sort=False)["contract"].shift(1)
    schedule["is_roll_day"] = schedule["previous_contract"].notna() & schedule["contract"].ne(
        schedule["previous_contract"]
    )
    return schedule
