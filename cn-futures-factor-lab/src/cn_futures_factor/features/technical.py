"""不依赖第三方技术指标库的基础量价因子。"""

from __future__ import annotations

import numpy as np
import pandas as pd


def momentum(group: pd.DataFrame, lookback: int) -> pd.Series:
    """过去 lookback 个交易日的连续价格收益。"""

    return group["continuous_close"].pct_change(lookback, fill_method=None)


def reversal(group: pd.DataFrame, lookback: int) -> pd.Series:
    """短期反转：短期收益的相反数。"""

    return -group["continuous_close"].pct_change(lookback, fill_method=None)


def volatility(group: pd.DataFrame, lookback: int) -> pd.Series:
    """连续合约日收益的滚动年化波动率。"""

    return group["continuous_return"].rolling(lookback, min_periods=lookback).std() * np.sqrt(252)


def liquidity(group: pd.DataFrame, lookback: int) -> pd.Series:
    """滚动平均成交量的对数，降低极端值影响。"""

    average_volume = group["volume"].rolling(lookback, min_periods=lookback).mean()
    return np.log1p(average_volume)


def open_interest_change(group: pd.DataFrame, lookback: int) -> pd.Series:
    """主力合约持仓量的中期变化率。换月附近应谨慎解释。"""

    return group["open_interest"].pct_change(lookback, fill_method=None)
