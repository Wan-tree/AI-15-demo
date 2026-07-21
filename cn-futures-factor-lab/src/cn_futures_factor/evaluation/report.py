"""生成适合课程项目提交的基础报告。"""

from __future__ import annotations

import os
from pathlib import Path

# 将字体和绘图库缓存放在项目可写目录。受限服务器或教学机的用户主目录可能不可写，
# 如果不处理，Matplotlib 首次导入会产生警告甚至拖慢每次命令。
_CACHE_ROOT = Path(__file__).resolve().parents[3] / "artifacts/.cache"
_CACHE_ROOT.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(_CACHE_ROOT / "matplotlib"))
os.environ.setdefault("XDG_CACHE_HOME", str(_CACHE_ROOT))

import matplotlib  # noqa: E402

# 使用无界面的 Agg 后端，确保在服务器、CI 和 Conda 终端中也能保存图片。
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402


def save_equity_curve(daily: pd.DataFrame, path: str | Path) -> Path:
    """保存净值和回撤双面板图。"""

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    figure, axes = plt.subplots(2, 1, figsize=(11, 7), sharex=True, height_ratios=(2, 1))
    axes[0].plot(daily["trade_date"], daily["nav"], color="#1769aa", linewidth=1.6)
    axes[0].set_title("Demo Strategy Equity Curve")
    axes[0].set_ylabel("NAV")
    axes[0].grid(alpha=0.25)
    axes[1].fill_between(daily["trade_date"], daily["drawdown"], 0, color="#c62828", alpha=0.55)
    axes[1].set_ylabel("Drawdown")
    axes[1].grid(alpha=0.25)
    figure.tight_layout()
    figure.savefig(destination, dpi=150, bbox_inches="tight")
    plt.close(figure)
    return destination


def write_markdown_report(
    metrics: dict[str, float],
    daily: pd.DataFrame,
    path: str | Path,
    *,
    factor_name: str,
    data_source: str = "synthetic",
    source_path: str | Path | None = None,
    input_row_count: int | None = None,
    product_count: int | None = None,
    validation_summary: str | None = None,
    data_quality_notes: list[str] | None = None,
    execution_lag_days: int = 1,
    period_metrics: pd.DataFrame | None = None,
    cost_scenario_metrics: pd.DataFrame | None = None,
    final_holdout_note: str | None = None,
) -> Path:
    """将绩效指标、数据来源和方法边界写入 Markdown。"""

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    percent_keys = {
        "total_return",
        "annual_return",
        "annualized_mean_return",
        "annual_volatility",
        "max_drawdown",
        "daily_hit_rate",
        "average_rebalance_turnover",
        "average_roll_turnover",
        "total_transaction_cost",
    }
    rows = []
    for key, value in metrics.items():
        display = f"{value:.2%}" if key in percent_keys else f"{value:.4f}"
        rows.append(f"| `{key}` | {display} |")

    start = pd.Timestamp(daily["trade_date"].min()).date()
    end = pd.Timestamp(daily["trade_date"].max()).date()
    is_synthetic = data_source == "synthetic"
    title = "合成数据演示回测报告" if is_synthetic else "真实数据基础演示回测报告"
    notice = (
        "本报告使用程序生成的合成数据，只用于验证工程流程，不能代表任何真实投资表现。"
        if is_synthetic
        else "本报告使用授权导出的真实历史数据，但仍只是工程链路和基础因子的技术演示，"
        "已加入基础可成交性、时间分期和成本压力检查，但尚未补齐完整交易规则与正式模型实验。"
    )
    source_display = str(source_path) if source_path is not None else "程序生成"
    input_rows_display = f"{input_row_count:,}" if input_row_count is not None else "未记录"
    products_display = str(product_count) if product_count is not None else "未记录"
    validation_display = validation_summary or "未记录"
    quality_notes_display = "\n".join(
        f"- {note}" for note in (data_quality_notes or ["没有额外记录"])
    )
    first_boundary = (
        "合成数据只测试代码，不能用于判断因子有效性；"
        if is_synthetic
        else "零 OHLC/零成交记录只保留日期链，公共执行层会拒绝在这些记录上形成目标仓位；"
    )
    period_rows = []
    if period_metrics is not None:
        for row in period_metrics.itertuples(index=False):
            period_rows.append(
                f"| `{row.period}` | {row.observed_start} 至 {row.observed_end} | "
                f"{row.total_return:.2%} | {row.annual_return:.2%} | {row.sharpe:.4f} | "
                f"{row.max_drawdown:.2%} |"
            )
    period_section = (
        "## 时间顺序分期绩效\n\n"
        "| 区间 | 实际日期 | 总收益 | CAGR | Sharpe | 最大回撤 |\n"
        "|---|---|---:|---:|---:|---:|\n"
        + "\n".join(period_rows)
        + "\n\n"
        + f"> 最终盲测规则：{final_holdout_note or '研究方案冻结后只查看一次。'}\n"
        if period_rows
        else ""
    )
    scenario_rows = []
    if cost_scenario_metrics is not None:
        for row in cost_scenario_metrics.itertuples(index=False):
            scenario_rows.append(
                f"| `{row.scenario}` | {row.rebalance_bps:.1f} | {row.roll_bps:.1f} | "
                f"{row.total_return:.2%} | {row.annual_return:.2%} | {row.sharpe:.4f} |"
            )
    cost_section = (
        "## 成本压力测试\n\n"
        "| 情景 | 调仓成本(bps) | 换月成本(bps) | 总收益 | CAGR | Sharpe |\n"
        "|---|---:|---:|---:|---:|---:|\n"
        + "\n".join(scenario_rows)
        + "\n"
        if scenario_rows
        else ""
    )
    content = f"""# {title}

> {notice}

## 运行摘要

- 数据类型：`{data_source}`
- 输入来源：`{source_display}`
- 输入记录数：{input_rows_display}
- 商品品种数：{products_display}
- 信号因子：`{factor_name}`
- 回测区间：{start} 至 {end}
- 有效交易日：{len(daily)}
- 执行时间线：t 日收盘后形成信号 → t+{execution_lag_days} 交易日执行
- 收益定义：执行日目标权重乘以所选具体合约从执行日到下一交易日的结算价收益
- 成本：普通调仓成本 + 主力换月额外成本
- 指标口径：`annual_return` 为 CAGR；`sharpe` 为日收益算术均值/标准差 × √252

## 数据质量记录

```text
{validation_display}
```

{quality_notes_display}

## 绩效指标

| 指标 | 数值 |
|---|---:|
{chr(10).join(rows)}

{period_section}
{cost_section}
## 结果文件

- `equity_curve.png`：净值与回撤图；
- `daily_returns.csv`：每日收益、成本、换手和净值；
- `positions.csv`：每日品种权重、实际合约和收益贡献。
- `period_metrics.csv`：训练、验证和测试期分别重置净值后的指标；
- `cost_scenarios.csv`：低、基准和压力成本下的结果。

## 解释边界

1. {first_boundary}
2. 第一版使用日频结算价，没有模拟涨跌停、保证金追缴和日内成交冲击；
3. 当前用三档成本压力代替未知的精确历史费率；正式研究仍应补充品种级手续费、合约乘数和历史交易规则；
4. 机器学习只能用训练期拟合、验证期选参；测试期和新增最终盲测不得参与调参。
"""
    destination.write_text(content, encoding="utf-8")
    return destination
