"""所有策略共用的时间分期和交易成本压力测试。

这个模块不关心预测来自单因子、LightGBM 还是神经网络。只要进入统一回测输出，
就必须按同一组时间边界和成本情景评价，避免不同模型各挑一套有利口径。
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from cn_futures_factor.evaluation.metrics import calculate_metrics
from cn_futures_factor.exceptions import ConfigurationError, DataValidationError


def rebuild_performance_path(
    daily: pd.DataFrame,
    *,
    rebalance_bps: float,
    roll_bps: float,
) -> pd.DataFrame:
    """在不改变持仓的前提下，用指定成本重新构造净收益和净值路径。"""

    required = {"trade_date", "gross_return", "rebalance_turnover", "roll_turnover"}
    missing = required.difference(daily.columns)
    if missing:
        raise DataValidationError(f"成本压力测试缺少日频字段：{sorted(missing)}")
    if rebalance_bps < 0 or roll_bps < 0:
        raise ConfigurationError("交易成本不能为负")

    result = daily.copy().sort_values("trade_date", kind="stable").reset_index(drop=True)
    result["transaction_cost"] = (
        result["rebalance_turnover"] * float(rebalance_bps) / 10_000.0
        + result["roll_turnover"] * float(roll_bps) / 10_000.0
    )
    result["net_return"] = result["gross_return"] - result["transaction_cost"]
    result["nav"] = (1.0 + result["net_return"]).cumprod()
    result["drawdown"] = result["nav"] / result["nav"].cummax() - 1.0
    return result


def summarize_cost_scenarios(
    daily: pd.DataFrame,
    scenarios: dict[str, dict[str, Any]],
    *,
    annualization_days: int,
) -> pd.DataFrame:
    """固定同一批持仓，仅改变成本假设，返回每个情景的完整绩效指标。"""

    if not scenarios:
        raise ConfigurationError("至少需要一个交易成本情景")
    rows: list[dict[str, Any]] = []
    for scenario_name, scenario in scenarios.items():
        rebalance_bps = float(scenario["rebalance_bps"])
        roll_bps = float(scenario["roll_bps"])
        path = rebuild_performance_path(
            daily,
            rebalance_bps=rebalance_bps,
            roll_bps=roll_bps,
        )
        metrics = calculate_metrics(path, annualization_days=annualization_days)
        rows.append(
            {
                "scenario": scenario_name,
                "rebalance_bps": rebalance_bps,
                "roll_bps": roll_bps,
                **metrics,
            }
        )
    return pd.DataFrame(rows)


def summarize_research_periods(
    daily: pd.DataFrame,
    periods: dict[str, dict[str, Any]],
    *,
    annualization_days: int,
) -> pd.DataFrame:
    """严格按预先配置的日期边界统计训练、验证和测试期绩效。

    每个子区间都会从 1 重新构造净值与回撤；不能直接沿用全样本净值，否则验证期
    的总收益和最大回撤会被训练期起点污染。区间可以不覆盖全部数据，但不允许重叠。
    """

    if not periods:
        raise ConfigurationError("研究分期配置不能为空")
    if "trade_date" not in daily:
        raise DataValidationError("研究分期缺少 trade_date")

    source = daily.copy()
    source["trade_date"] = pd.to_datetime(source["trade_date"]).dt.normalize()
    assigned = pd.Series(pd.NA, index=source.index, dtype="string")
    rows: list[dict[str, Any]] = []

    for period_name, period in periods.items():
        start = pd.Timestamp(period["start"]).normalize()
        end = pd.Timestamp(period["end"]).normalize()
        if start > end:
            raise ConfigurationError(f"研究区间 {period_name!r} 的开始日期晚于结束日期")
        mask = source["trade_date"].between(start, end, inclusive="both")
        if assigned.loc[mask].notna().any():
            raise ConfigurationError(f"研究区间 {period_name!r} 与前一个区间发生重叠")
        assigned.loc[mask] = period_name
        subset = source.loc[mask].copy()
        if subset.empty:
            # 合成测试数据或较短样本可能尚未覆盖后面的区间；保留配置但不伪造指标。
            continue
        subset["nav"] = (1.0 + subset["net_return"]).cumprod()
        subset["drawdown"] = subset["nav"] / subset["nav"].cummax() - 1.0
        metrics = calculate_metrics(subset, annualization_days=annualization_days)
        rows.append(
            {
                "period": period_name,
                "purpose": str(period.get("purpose", "")),
                "configured_start": start.date().isoformat(),
                "configured_end": end.date().isoformat(),
                "observed_start": subset["trade_date"].min().date().isoformat(),
                "observed_end": subset["trade_date"].max().date().isoformat(),
                **metrics,
            }
        )
    return pd.DataFrame(rows)
