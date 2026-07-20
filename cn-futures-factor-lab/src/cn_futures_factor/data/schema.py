"""标准数据契约。

外部数据库可以使用不同字段名，但进入核心研究代码前必须转换成这里的标准字段。
"""

from __future__ import annotations

REQUIRED_CONTRACT_DAILY_COLUMNS: tuple[str, ...] = (
    "trade_date",
    "exchange",
    "product",
    "contract",
    "open",
    "high",
    "low",
    "close",
    "settlement",
    "volume",
    "open_interest",
)

OPTIONAL_CONTRACT_DAILY_COLUMNS: tuple[str, ...] = (
    "pre_settlement",
    "turnover",
    "upper_limit",
    "lower_limit",
    "source",
)

PRICE_COLUMNS: tuple[str, ...] = (
    "open",
    "high",
    "low",
    "close",
    "settlement",
    "pre_settlement",
    "upper_limit",
    "lower_limit",
)

ACTIVITY_COLUMNS: tuple[str, ...] = ("volume", "open_interest", "turnover")
