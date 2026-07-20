"""回测绩效指标。"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd


def calculate_metrics(daily: pd.DataFrame, annualization_days: int = 252) -> dict[str, float]:
    """计算一组常用且定义透明的绩效指标。"""

    if daily.empty:
        raise ValueError("回测日收益为空")
    returns = daily["net_return"].astype(float)
    nav = daily["nav"].astype(float)
    observations = len(returns)
    annual_return = float(nav.iloc[-1] ** (annualization_days / observations) - 1.0)
    annual_volatility = float(returns.std(ddof=1) * math.sqrt(annualization_days))
    sharpe = annual_return / annual_volatility if annual_volatility > 0 else np.nan
    max_drawdown = float(daily["drawdown"].min())
    calmar = annual_return / abs(max_drawdown) if max_drawdown < 0 else np.nan

    return {
        "observations": float(observations),
        "total_return": float(nav.iloc[-1] - 1.0),
        "annual_return": annual_return,
        "annual_volatility": annual_volatility,
        "sharpe": float(sharpe),
        "max_drawdown": max_drawdown,
        "calmar": float(calmar),
        "daily_hit_rate": float((returns > 0).mean()),
        "average_rebalance_turnover": float(daily["rebalance_turnover"].mean()),
        "average_roll_turnover": float(daily["roll_turnover"].mean()),
        "total_transaction_cost": float(daily["transaction_cost"].sum()),
    }
