"""期货合约代码解析。

国内不同交易所和数据商的代码格式并不完全一致。本模块只做可解释的基础解析；如果
真实数据商提供了独立的品种和交割月字段，应优先使用数据商字段，而不是猜测代码。
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime

import pandas as pd

from cn_futures_factor.exceptions import DataValidationError

_CONTRACT_PATTERN = re.compile(r"^([A-Z]+)[._-]?(\d{3,4})(?:\.[A-Z]+)?$")


@dataclass(frozen=True)
class ContractInfo:
    """从合约代码中提取出的标准信息。"""

    original: str
    product: str
    delivery_year: int
    delivery_month: int

    @property
    def delivery_yyyymm(self) -> int:
        return self.delivery_year * 100 + self.delivery_month


def _expand_three_digit_delivery(code: str, reference_year: int) -> tuple[int, int]:
    """根据交易年份解释郑商所历史上常见的三位交割代码。

    例如在 2024 年附近，``409`` 应解释为 2024 年 9 月。选择距离参考年份最近的十年，
    比简单地固定补成 2024 更稳健，但仍建议真实项目优先使用供应商的交割日期字段。
    """

    year_digit = int(code[0])
    month = int(code[1:])
    decade = (reference_year // 10) * 10
    year = decade + year_digit
    if year < reference_year - 5:
        year += 10
    elif year > reference_year + 5:
        year -= 10
    return year, month


def parse_contract_code(
    contract: str,
    reference_date: str | date | datetime | pd.Timestamp | None = None,
) -> ContractInfo:
    """解析形如 ``RB2610``、``MA409`` 或 ``CU2609.SHFE`` 的合约代码。

    无法可靠解析时会抛出明确的数据异常，避免错误代码悄悄进入主力合约逻辑。
    """

    normalized = str(contract).strip().upper()
    match = _CONTRACT_PATTERN.match(normalized)
    if not match:
        raise DataValidationError(f"无法解析期货合约代码：{contract!r}")

    product, digits = match.groups()
    if len(digits) == 4:
        year = 2000 + int(digits[:2])
        month = int(digits[2:])
    else:
        if reference_date is None:
            raise DataValidationError(
                f"三位交割代码 {contract!r} 必须提供交易日期，才能判断所属十年"
            )
        reference_year = pd.Timestamp(reference_date).year
        year, month = _expand_three_digit_delivery(digits, reference_year)

    if not 1 <= month <= 12:
        raise DataValidationError(f"合约月份无效：{contract!r}")
    return ContractInfo(normalized, product, year, month)


def product_from_contract(contract: str) -> str:
    """只提取品种字母；不需要交割年月时可使用这个更宽松的函数。"""

    match = re.match(r"^([A-Za-z]+)", str(contract).strip())
    if not match:
        raise DataValidationError(f"无法从合约代码提取品种：{contract!r}")
    return match.group(1).upper()
