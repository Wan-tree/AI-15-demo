"""数据连接器抽象接口。"""

from __future__ import annotations

from abc import ABC, abstractmethod

import pandas as pd


class DataConnector(ABC):
    """任何数据源都必须遵守的最小接口。"""

    @abstractmethod
    def load(self) -> pd.DataFrame:
        """读取并返回标准化后的合约日行情表。"""
