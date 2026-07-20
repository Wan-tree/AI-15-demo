"""把数据商导出的表格转换为项目标准格式。"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from cn_futures_factor.data.schema import ACTIVITY_COLUMNS, PRICE_COLUMNS
from cn_futures_factor.exceptions import DataValidationError
from cn_futures_factor.futures.contracts import product_from_contract


def _clean_column_name(value: Any) -> str:
    """清理 Excel 中偶尔出现的换行、全角空格和首尾空格。"""

    return str(value).replace("\n", " ").replace("\u3000", " ").strip()


def standardize_contract_daily(
    raw: pd.DataFrame,
    mapping_config: dict[str, Any],
    *,
    source_name: str,
) -> pd.DataFrame:
    """根据字段映射转换数据类型，并补充可安全推导的字段。

    注意：本函数不会删除重复记录或填补核心价格。研究数据有问题时，应通过校验报告
    暴露问题，而不是用隐式清洗让问题消失。
    """

    frame = raw.copy()
    frame.columns = [_clean_column_name(column) for column in frame.columns]

    standard_to_source = mapping_config.get("columns", {})
    if not isinstance(standard_to_source, dict):
        raise DataValidationError("field_mappings.yaml 中 columns 必须是键值结构")
    rename_map = {
        _clean_column_name(source): standard
        for standard, source in standard_to_source.items()
        if source is not None and _clean_column_name(source) in frame.columns
    }
    frame = frame.rename(columns=rename_map)

    if "trade_date" not in frame or "contract" not in frame:
        raise DataValidationError("导入文件至少需要交易日期和合约代码字段")

    date_format = mapping_config.get("date_format")
    frame["trade_date"] = pd.to_datetime(
        frame["trade_date"], format=date_format, errors="coerce"
    ).dt.normalize()
    frame["contract"] = frame["contract"].astype("string").str.strip().str.upper()

    if "product" not in frame:
        frame["product"] = frame["contract"].map(product_from_contract)
    else:
        frame["product"] = frame["product"].astype("string").str.strip().str.upper()

    if "exchange" not in frame:
        frame["exchange"] = "UNKNOWN"
    else:
        frame["exchange"] = frame["exchange"].astype("string").str.strip().str.upper()

    # 结算价是期货研究中的核心字段。部分文件只有收盘价时允许显式回退到收盘价，
    # 但会保留标准列名，便于以后替换为真实结算价。
    if "settlement" not in frame and "close" in frame:
        frame["settlement"] = frame["close"]

    numeric_columns = [column for column in (*PRICE_COLUMNS, *ACTIVITY_COLUMNS) if column in frame]
    for column in numeric_columns:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")

    multipliers = mapping_config.get("multipliers", {}) or {}
    for column, multiplier in multipliers.items():
        if column in frame:
            frame[column] = frame[column] * float(multiplier)

    if "pre_settlement" not in frame and "settlement" in frame:
        frame = frame.sort_values(["contract", "trade_date"], kind="stable")
        frame["pre_settlement"] = frame.groupby("contract", sort=False)["settlement"].shift(1)

    for optional in ("turnover", "upper_limit", "lower_limit"):
        if optional not in frame:
            frame[optional] = np.nan
    frame["source"] = source_name

    preferred_order = [
        "trade_date",
        "exchange",
        "product",
        "contract",
        "open",
        "high",
        "low",
        "close",
        "settlement",
        "pre_settlement",
        "volume",
        "open_interest",
        "turnover",
        "upper_limit",
        "lower_limit",
        "source",
    ]
    available = [column for column in preferred_order if column in frame]
    remaining = [column for column in frame.columns if column not in available]
    return (
        frame[available + remaining]
        .sort_values(["trade_date", "product", "contract"], kind="stable")
        .reset_index(drop=True)
    )
