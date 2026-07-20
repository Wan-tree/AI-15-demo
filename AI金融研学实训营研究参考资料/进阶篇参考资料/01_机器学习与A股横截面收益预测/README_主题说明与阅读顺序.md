# 1. 机器学习与A股横截面收益预测

**研究问题：** 机器学习能否利用财务、估值和交易特征，提高A股未来收益排序的样本外表现？

## 主题说明

该方向以“公司特征—未来收益”为主线，重点比较线性基准与树模型、神经网络对非线性关系和特征交互的识别能力。研究不应只报告预测误差，还应报告Rank IC、分组收益、换手率和交易成本后表现，并解释哪些变量在不同市场状态下更重要。

## 可用数据

聚源财务报表、估值、公司属性、分析师预测、行情、成交量、换手率、停复牌和分红送转数据。

## 建议阅读顺序

### 1. Gu, Kelly & Xiu (2020), Empirical Asset Pricing via Machine Learning

- 文件：`01_Gu_Kelly_Xiu_Empirical_Asset_Pricing_via_Machine_Learning.pdf`
- 用途：核心精读。重点看公司特征处理、滚动训练/验证/测试划分、模型比较、特征重要性和投资组合检验。
- 公开来源：https://dachxiu.chicagobooth.edu/download/ML_BKP.pdf

### 2. Freyberger, Neuhierl & Weber (2020), Dissecting Characteristics Nonparametrically

- 文件：`02_Freyberger_Neuhierl_Weber_Dissecting_Characteristics_Nonparametrically.pdf`
- 用途：方法精读。理解如何用非参数方法识别特征的独立作用、非线性和冗余。
- 公开来源：https://www.ifo.de/DocDL/cesifo1_wp7187.pdf

### 3. Giglio, Kelly & Xiu (2022), Factor Models, Machine Learning, and Asset Pricing

- 文件：`03_Giglio_Kelly_Xiu_Factor_Models_ML_and_Asset_Pricing.pdf`
- 用途：综述阅读。用于搭建机器学习资产定价的知识框架，并区分收益预测、因子提取和定价检验。
- 公开来源：https://stefanogiglio.org/papers/giglio-kelly-xiu-arfe-2022.pdf

## 研究注意事项

建议同步学习Fama–MacBeth回归、Lasso/Elastic Net和SHAP；中国样本必须使用真实可得日期和历史股票池。
