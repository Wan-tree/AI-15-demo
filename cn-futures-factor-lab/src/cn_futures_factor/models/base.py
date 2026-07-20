"""未来机器学习模型需要遵守的统一接口。"""

from __future__ import annotations

from abc import ABC, abstractmethod

import pandas as pd


class ResearchModel(ABC):
    """最小研究模型协议。

    组合层只依赖 ``predict`` 输出，不关心内部是线性模型、树模型还是神经网络。
    """

    @abstractmethod
    def fit(self, features: pd.DataFrame, target: pd.Series) -> ResearchModel:
        """使用训练期数据拟合模型并返回自身。"""

    @abstractmethod
    def predict(self, features: pd.DataFrame) -> pd.Series:
        """输出与 features 索引对齐的预测分数。"""
