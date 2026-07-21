# 中国商品期货机器学习因子研究框架

这是一个面向教学、课程研究与团队协作的中国商品期货日频因子研究框架。项目当前已经接入 2020～2025 年的真实全合约日行情；合成数据仍保留为自动测试和无数据时的离线兜底。

## 当前已经实现

- Conda 环境配置；
- 可重复生成的合成商品期货数据；
- CSV、Excel、Parquet 数据接入；
- 字段映射、标准化、数据质量检查与来源清单；
- 真实上财导出全合约数据的专用字段映射；
- 基于滞后持仓量的主力合约选择；
- 无跳点的连续收益与连续价格序列；
- 动量、反转、波动率、流动性和持仓变化因子；
- 横截面多空组合；
- 所有策略统一强制至少 1 个交易日的信号—执行滞后；
- 下单前滞后流动性准入与执行日成交/OHLC 成交确认；
- 与执行滞后对齐的 1/5/20 日未来收益标签；
- 含统一基点调仓成本和额外换月成本的日频回测；
- 固定训练/验证/测试日期边界与三档成本压力测试；
- 绩效指标、净值图和 Markdown 报告；
- 防止未来信息泄漏的自动测试；
- 为后续机器学习模型预留的稳定接口。

## 1. 安装 Conda 环境

在本目录中运行：

```bash
conda env create -f environment.yml
conda activate cn-futures-factor
python -m pip install -e ".[dev]"
```

如果环境已经存在，更新环境：

```bash
conda env update -f environment.yml --prune
conda activate cn-futures-factor
python -m pip install -e ".[dev]"
```

检查安装：

```bash
cn-futures doctor
```

## 2. 首次运行

下面的命令默认读取 `data/interim/sufe_contract_daily.parquet`，执行数据校验、主力合约构造、因子计算、组合构建和回测，并在 `artifacts/real_demo/` 生成报告：

```bash
cn-futures demo
```

也可以不依赖命令行入口，直接运行：

```bash
python -m cn_futures_factor demo
```

正常情况下会生成：

```text
data/processed/sufe_contract_daily.parquet
data/processed/sufe_main_panel.parquet
data/processed/sufe_features.parquet
artifacts/real_demo/daily_returns.csv
artifacts/real_demo/positions.csv
artifacts/real_demo/period_metrics.csv
artifacts/real_demo/cost_scenarios.csv
artifacts/real_demo/equity_curve.png
artifacts/real_demo/report.md
```

如需验证代码在完全不依赖真实文件时仍能运行：

```bash
cn-futures demo --source synthetic
```

## 3. 接入上财平台导出的数据

先在上财授权环境中导出一个小样本 CSV 或 XLSX，把文件放入：

```text
data/raw/sufe/
```

当前全合约文件使用专用映射，执行：

```bash
cn-futures ingest \
  --input data/raw/sufe/sufe_all_contracts_daily_20200102_20251231_exported_20260721.csv \
  --mapping configs/field_mappings_sufe_all_contracts.yaml \
  --output data/interim/sufe_contract_daily.parquet \
  --allow-inactive-ohlc
```

导入程序不会修改原始文件。它会额外生成 `.manifest.json`，记录文件摘要、行数、字段和处理时间，便于复现与审计。

`sufe_vendor_main_contracts_daily_...csv` 仅用于核对供应商主力合约，不作为正式收益输入；项目使用全合约数据自行按滞后持仓量选择主力。

## 4. 常用命令

```bash
# 环境与目录检查
cn-futures doctor

# 运行当前默认的真实数据演示
cn-futures demo

# 运行合成数据兜底演示
cn-futures demo --source synthetic

# 导入上财平台导出的文件
cn-futures ingest --input 文件路径 --mapping configs/field_mappings.yaml

# 运行测试
pytest

# 检查代码风格
ruff check .

# 自动格式化
ruff format .
```

## 5. 目录说明

```text
configs/        可修改的研究参数和字段映射
data/raw/       原始导出文件，只读保存，不提交 Git
data/interim/   标准化后的中间数据
data/processed/ 可直接用于研究的数据
data/manifests/ 数据来源与处理记录
docs/           中文说明文档
notebooks/      探索性分析，不承载核心业务逻辑
src/            可复用、可测试的核心代码
tests/          自动测试
artifacts/      回测结果、图表和报告
```

## 6. 阅读顺序

1. [当前项目进度与团队统一认知](docs/08_当前项目进度与团队统一认知.md)
2. [新手上手指南](docs/01_新手上手指南.md)
3. [上财数据导出与接入](docs/02_上财数据导出与接入.md)
4. [架构与扩展指南](docs/03_架构与扩展指南.md)
5. [方法与防泄漏](docs/04_方法与防泄漏.md)
6. [标准数据字典](docs/05_标准数据字典.md)
7. [团队协作规范](docs/06_团队协作规范.md)
8. [后续研究任务与完整实验路线图](docs/07_后续研究任务与完整实验路线图.md)

## 7. 重要边界

- 本项目是教学和研究框架，不是实盘交易系统；
- 不要把上财数据库账号、Cookie、原始授权数据提交到 Git；
- 不要绕过数据库访问控制或批量抓取网站；
- 连续合约价格用于研究，真实盈亏必须基于具体可交易合约；
- 任何模型都必须使用时间顺序验证，不能随机打乱历史数据。
