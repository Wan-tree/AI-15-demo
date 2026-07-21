"""把模型产生的目标仓位转换为以后才可执行的仓位。

所有策略和模型都必须经过这里。这样不会出现某个模型使用 t 日完整结算数据产生信号，
却又假设自己已经按同一个 t 日结算价成交的时间穿越问题。
"""

from __future__ import annotations

import pandas as pd

from cn_futures_factor.exceptions import ConfigurationError, DataValidationError


def apply_execution_lag(
    target_positions: pd.DataFrame,
    market_panel: pd.DataFrame,
    *,
    execution_lag_days: int,
    minimum_lagged_volume: float = 0.0,
    minimum_lagged_open_interest: float = 0.0,
    minimum_execution_volume: float = 0.0,
    require_positive_execution_ohlc: bool = False,
) -> pd.DataFrame:
    """将信号日目标仓位映射到未来的实际执行日。

    参数
    ----
    target_positions:
        模型或规则在 ``trade_date`` 收盘后产生的目标仓位。日期在本函数中被保留为
        ``signal_date``，不能直接用于当日收益。
    market_panel:
        每个品种的交易日历。滞后按各品种实际存在的交易记录计算，而不是自然日。
    execution_lag_days:
        信号到执行至少间隔几个交易日。正式框架强制不小于 1。

    说明
    ----
    输入可以是每日信号，也可以是较低频信号。信号在执行日生效，之后会一直持有，
    直到下一条信号到达其执行日。这样未来改成每 5 日调仓时不会漏掉中间持有收益。
    """

    if execution_lag_days < 1:
        raise ConfigurationError("execution_lag_days 必须至少为 1，禁止同日信息同日成交")
    if (
        minimum_lagged_volume < 0
        or minimum_lagged_open_interest < 0
        or minimum_execution_volume < 0
    ):
        raise ConfigurationError("成交量和持仓量门槛不能为负")

    required_positions = {"trade_date", "product", "weight"}
    required_market = {"trade_date", "product"}
    missing_positions = required_positions.difference(target_positions.columns)
    missing_market = required_market.difference(market_panel.columns)
    if missing_positions or missing_market:
        raise DataValidationError(
            "执行层输入缺少字段："
            f"positions={sorted(missing_positions)}, market={sorted(missing_market)}"
        )

    positions = target_positions.copy()
    positions["trade_date"] = pd.to_datetime(positions["trade_date"]).dt.normalize()
    if positions.duplicated(["trade_date", "product"]).any():
        raise DataValidationError("同一信号日和品种存在多条目标仓位")

    calendar = market_panel[["trade_date", "product"]].drop_duplicates().copy()
    calendar["trade_date"] = pd.to_datetime(calendar["trade_date"]).dt.normalize()
    calendar = calendar.sort_values(["product", "trade_date"], kind="stable")
    calendar["market_order"] = calendar.groupby("product", sort=False).cumcount()

    # 先为每条信号找到它在对应品种交易日历中的序号，再向后移动 execution_lag_days。
    signal_lookup = calendar.rename(
        columns={"trade_date": "signal_date", "market_order": "signal_order"}
    )
    signals = positions.rename(columns={"trade_date": "signal_date"})
    events = signals.merge(
        signal_lookup,
        on=["signal_date", "product"],
        how="left",
        validate="many_to_one",
    )
    missing_calendar = events["signal_order"].isna()
    if missing_calendar.any():
        examples = events.loc[missing_calendar, ["signal_date", "product"]].head(5)
        raise DataValidationError(
            "部分目标仓位日期不在市场交易日历中，例如："
            f"{examples.to_dict(orient='records')}"
        )

    events["execution_order"] = events["signal_order"].astype(int) + execution_lag_days
    execution_lookup = calendar.rename(
        columns={"trade_date": "execution_date", "market_order": "execution_order"}
    )
    events = events.merge(
        execution_lookup[["product", "execution_order", "execution_date"]],
        on=["product", "execution_order"],
        how="left",
        validate="many_to_one",
    )

    # 样本末尾没有未来执行日的信号无法成交，应自然丢弃而不是映射回最后一天。
    events = events.dropna(subset=["execution_date"]).copy()
    if events.empty:
        raise DataValidationError("没有任何信号拥有可用的未来执行日")

    # 用执行日前已知的实际候选合约流动性决定能否建立目标仓位。这里绝不读取执行日
    # 最终成交量，因为它在执行决策时尚不可知。
    liquidity_columns = [
        column
        for column in ("lagged_volume", "lagged_open_interest")
        if column in market_panel
    ]
    if minimum_lagged_volume > 0 and "lagged_volume" not in liquidity_columns:
        raise DataValidationError("启用了成交量门槛，但市场面板缺少 lagged_volume")
    if minimum_lagged_open_interest > 0 and "lagged_open_interest" not in liquidity_columns:
        raise DataValidationError("启用了持仓量门槛，但市场面板缺少 lagged_open_interest")
    if liquidity_columns:
        liquidity = market_panel[["trade_date", "product", *liquidity_columns]].copy()
        liquidity["trade_date"] = pd.to_datetime(liquidity["trade_date"]).dt.normalize()
        liquidity = liquidity.rename(columns={"trade_date": "execution_date"})
        events = events.merge(
            liquidity,
            on=["execution_date", "product"],
            how="left",
            validate="many_to_one",
        )

    # 滞后流动性用于下单前的品种准入；执行日成交量/OHLC 用于事后确认这张订单当天
    # 是否存在可观察的成交条件。后者只影响“订单是否成交”，绝不回流到信号或预测。
    execution_market_mapping = {
        "volume": "execution_volume",
        "open": "execution_open",
        "high": "execution_high",
        "low": "execution_low",
        "close": "execution_close",
    }
    required_execution_fields: set[str] = set()
    if minimum_execution_volume > 0:
        required_execution_fields.add("volume")
    if require_positive_execution_ohlc:
        required_execution_fields.update({"open", "high", "low", "close"})
    missing_execution_fields = required_execution_fields.difference(market_panel.columns)
    if missing_execution_fields:
        raise DataValidationError(
            f"启用了执行日可成交性检查，但市场面板缺少 {sorted(missing_execution_fields)}"
        )
    execution_market_columns = [
        column for column in execution_market_mapping if column in required_execution_fields
    ]
    if execution_market_columns:
        execution_market = market_panel[
            ["trade_date", "product", *execution_market_columns]
        ].copy()
        execution_market["trade_date"] = pd.to_datetime(
            execution_market["trade_date"]
        ).dt.normalize()
        execution_market = execution_market.rename(
            columns={"trade_date": "execution_date", **execution_market_mapping}
        )
        events = events.merge(
            execution_market,
            on=["execution_date", "product"],
            how="left",
            validate="many_to_one",
        )

    events["requested_weight"] = events["weight"]
    events["execution_eligible"] = True
    events["execution_exclusion_reason"] = ""

    def block(mask: pd.Series, reason: str) -> None:
        """把一种不可成交原因追加到审计字段，并把目标仓位标记为不可执行。"""

        existing_reason = events.loc[mask, "execution_exclusion_reason"]
        separator = existing_reason.ne("").map({True: ";", False: ""})
        events.loc[mask, "execution_exclusion_reason"] = existing_reason + separator + reason
        events.loc[mask, "execution_eligible"] = False

    if minimum_lagged_volume > 0:
        blocked_volume = events["lagged_volume"].isna() | events["lagged_volume"].lt(
            minimum_lagged_volume
        )
        block(blocked_volume, "lagged_volume_below_threshold")
    if minimum_lagged_open_interest > 0:
        blocked_open_interest = events["lagged_open_interest"].isna() | events[
            "lagged_open_interest"
        ].lt(minimum_lagged_open_interest)
        block(blocked_open_interest, "lagged_open_interest_below_threshold")
    if minimum_execution_volume > 0:
        blocked_execution_volume = events["execution_volume"].isna() | events[
            "execution_volume"
        ].lt(minimum_execution_volume)
        block(blocked_execution_volume, "execution_volume_below_threshold")
    if require_positive_execution_ohlc:
        execution_ohlc = events[
            ["execution_open", "execution_high", "execution_low", "execution_close"]
        ]
        blocked_execution_ohlc = execution_ohlc.isna().any(axis=1) | execution_ohlc.le(0).any(
            axis=1
        )
        block(blocked_execution_ohlc, "execution_ohlc_not_positive")
    events.loc[~events["execution_eligible"], "weight"] = 0.0
    events["is_execution_event"] = True

    metadata_columns = [
        column
        for column in signals.columns
        if column not in {"signal_date", "product"}
    ]
    execution_columns = [
        "requested_weight",
        "execution_eligible",
        "execution_exclusion_reason",
        *liquidity_columns,
        *execution_market_mapping.values(),
    ]
    execution_columns = [column for column in execution_columns if column in events]
    event_table = events[
        [
            "execution_date",
            "signal_date",
            "product",
            *metadata_columns,
            *execution_columns,
            "is_execution_event",
        ]
    ].rename(columns={"execution_date": "trade_date"})
    if event_table.duplicated(["trade_date", "product"]).any():
        raise DataValidationError("多条信号被映射到同一执行日和品种")

    # 在完整交易日历上展开，并把最近一次已执行目标仓位向前持有到下一次执行事件。
    timeline = calendar[["trade_date", "product"]].merge(
        event_table,
        on=["trade_date", "product"],
        how="left",
        validate="one_to_one",
    )
    timeline = timeline.sort_values(["product", "trade_date"], kind="stable")
    fill_columns = ["signal_date", *metadata_columns, *execution_columns]
    timeline[fill_columns] = timeline.groupby("product", sort=False)[fill_columns].ffill()
    timeline = timeline[timeline["signal_date"].notna()].copy()
    # merge + ffill 会让布尔列暂时成为 object；在公共层恢复严格类型，避免下游使用
    # ``~series`` 时触发 Python 对象位运算并生成 -1/-2 一类错误统计。
    timeline["execution_eligible"] = timeline["execution_eligible"].astype(bool)
    timeline["is_execution_event"] = timeline["is_execution_event"].fillna(False).astype(bool)
    timeline["execution_lag_days"] = execution_lag_days
    return timeline.sort_values(["trade_date", "product"], kind="stable").reset_index(drop=True)
