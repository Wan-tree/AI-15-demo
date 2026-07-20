# Notebooks 使用原则

Notebook 用于观察数据、画图和讲解，不用于保存不可复用的核心逻辑。

建议后续按以下顺序创建：

1. `01_data_exploration.ipynb`：检查字段、缺失值和品种覆盖；
2. `02_contract_and_roll.ipynb`：展示主力合约和换月过程；
3. `03_factor_analysis.ipynb`：展示因子分布、IC 和分组收益；
4. `04_backtest_report.ipynb`：展示策略净值、回撤和品种贡献。

如果一个 Notebook 中的函数被重复使用两次，就应把它迁移到 `src/cn_futures_factor/` 并为其增加测试。

