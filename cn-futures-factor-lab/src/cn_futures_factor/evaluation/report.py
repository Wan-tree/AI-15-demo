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
) -> Path:
    """将绩效指标和方法边界写入 Markdown。"""

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    percent_keys = {
        "total_return",
        "annual_return",
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
    content = f"""# 合成数据演示回测报告

> 本报告使用程序生成的合成数据，只用于验证工程流程，不能代表任何真实投资表现。

## 运行摘要

- 信号因子：`{factor_name}`
- 回测区间：{start} 至 {end}
- 有效交易日：{len(daily)}
- 收益定义：当日信号权重乘以所选具体合约下一日结算价收益
- 成本：普通调仓成本 + 主力换月额外成本

## 绩效指标

| 指标 | 数值 |
|---|---:|
{chr(10).join(rows)}

## 结果文件

- `equity_curve.png`：净值与回撤图；
- `daily_returns.csv`：每日收益、成本、换手和净值；
- `positions.csv`：每日品种权重、实际合约和收益贡献。

## 解释边界

1. 合成数据只测试代码，不能用于判断因子有效性；
2. 第一版使用日频结算价，没有模拟涨跌停、保证金追缴和日内成交冲击；
3. 接入真实数据后，应补充品种级手续费、合约乘数和历史交易规则；
4. 增加机器学习后，必须使用时间顺序或滚动验证，禁止随机打乱全样本。
"""
    destination.write_text(content, encoding="utf-8")
    return destination
