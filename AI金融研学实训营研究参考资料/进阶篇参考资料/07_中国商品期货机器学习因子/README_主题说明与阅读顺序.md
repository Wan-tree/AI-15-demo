# 7. 中国商品期货的机器学习因子投资

**研究问题：** 动量、期限结构、流动性和产业链关系能否经机器学习组合后，提高中国商品期货的样本外收益预测？

## 主题说明

该方向可以充分利用多交易所数据。研究应从有金融含义的基础因子出发，统一连续合约和换月规则，再比较线性组合、树模型、图神经网络或LLM生成因子。必须计入换月、涨跌停和交易成本。

## 可用数据

上期所、能源中心、大商所、郑商所和中金所逐笔/日频数据，可补充仓单、库存、现货、天气和产业链数据。

## 建议阅读顺序

### 1. Hu et al., Graph Portfolio / Futures Quantitative Investment with Heterogeneous Continual GNNs

- 文件：`01_Hu_et_al_Heterogeneous_Continual_GNN_Futures_Investment.pdf`
- 用途：技术精读。参考中国期货横截面关系、图结构、多任务学习和持续学习。
- 公开来源：https://arxiv.org/pdf/2303.16532

### 2. Cheng, Liu & Zhou, Large Language Models and Futures Price Factors in China

- 文件：`02_Cheng_Zhou_Liu_LLM_Futures_Price_Factors_China.pdf`
- 用途：创新扩展。了解LLM生成因子与组合回测，同时重点审查提示词选择和数据挖掘偏差。
- 公开来源：https://arxiv.org/pdf/2509.23609

### 3. Bianchi, Fan, Miffre & Zhang, Exploiting the Dynamics of Commodity Futures Curves

- 文件：`03_Bianchi_et_al_Commodity_Futures_Curve_Strategies.pdf`
- 用途：金融基准。参考期限结构的水平、斜率和曲率信号、价差策略和交易成本检验。
- 公开来源：https://arxiv.org/pdf/2308.00383

## 研究注意事项

补充核心文献：Commodity Factor Investing via Machine Learning（Pacific-Basin Finance Journal）和 Investable Commodity Premia in China，正式全文需通过学校数据库获取。
