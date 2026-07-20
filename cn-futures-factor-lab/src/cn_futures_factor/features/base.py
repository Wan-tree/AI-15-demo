"""因子接口。

未来新增机器学习特征时，函数应继续遵守“只读取当日及历史数据”的约定。
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import pandas as pd

FactorFunction = Callable[[pd.DataFrame, int], pd.Series]


@dataclass(frozen=True)
class FactorDefinition:
    """一个可注册因子的元数据。"""

    name: str
    function: FactorFunction
    description: str
    higher_is_better: bool = True
