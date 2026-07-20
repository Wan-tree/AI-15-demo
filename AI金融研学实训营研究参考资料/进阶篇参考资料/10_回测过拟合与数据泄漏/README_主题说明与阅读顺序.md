# 10. AI量化策略的回测过拟合与数据泄漏

**研究问题：** AI策略的历史超额收益有多少来自真实信号，有多少来自反复试验、前视偏差和不现实交易假设？

## 主题说明

该主题可对同一策略设置随机划分与时间划分、当前成分股与历史成分股、含与不含交易成本等版本，量化研究设计对结果的影响。它既可以成为独立课题，也应作为其他九个课题共同遵守的研究规范。

## 可用数据

可复用机器学习选股、商品期货或订单簿策略的数据与结果，重点保存全部模型尝试和参数搜索记录。

## 建议阅读顺序

### 1. Bailey, Borwein, López de Prado & Zhu, The Probability of Backtest Overfitting

- 文件：`01_Bailey_et_al_Probability_of_Backtest_Overfitting.pdf`
- 用途：核心精读。理解组合对称交叉验证、过拟合概率和模型选择风险。
- 公开来源：https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf

### 2. Bailey et al., Statistical Overfitting and Backtest Performance

- 文件：`02_Bailey_et_al_Statistical_Overfitting_and_Backtest_Performance.pdf`
- 用途：入门说明。理解大规模策略搜索为何容易产生虚假的最优策略。
- 公开来源：https://sdm.lbl.gov/oapapers/ssrn-id2507040-bailey.pdf

### 3. Bailey, Borwein, López de Prado & Zhu, Pseudo-Mathematics and Financial Charlatanism

- 文件：`03_Lopez_de_Prado_Pseudo_Mathematics_and_Financial_Charlatanism.pdf`
- 用途：研究反思。重点看多重检验、回测选择偏差及样本外失效。
- 公开来源：https://obj.portfolioconstructionforum.edu.au/articles_perspectives/Pseudo-mathematics-and-financial-charlatanism.pdf

## 研究注意事项

建议把“时间序列切分、历史成分股、真实可得时间、退市样本、交易成本、参数搜索次数”列为所有小组的强制检查项。
