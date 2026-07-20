"""无需训练的因子基线模型。"""

from __future__ import annotations

import pandas as pd

from cn_futures_factor.models.base import ResearchModel


class IdentityFactorModel(ResearchModel):
    """直接把某个因子作为预测分数，用于验证完整工程链路。"""

    def __init__(self, factor_name: str) -> None:
        self.factor_name = factor_name

    def fit(self, features: pd.DataFrame, target: pd.Series) -> IdentityFactorModel:
        """基线无需训练；保留该方法是为了与未来模型兼容。"""

        if self.factor_name not in features:
            raise KeyError(f"特征中不存在因子：{self.factor_name}")
        if len(features) != len(target):
            raise ValueError("特征和目标行数不一致")
        return self

    def predict(self, features: pd.DataFrame) -> pd.Series:
        if self.factor_name not in features:
            raise KeyError(f"特征中不存在因子：{self.factor_name}")
        return features[self.factor_name].rename("prediction")
