# 5. 机器学习与高频波动率预测

**研究问题：** 订单簿和日内交易信息能否在HAR-RV基础上改善下一时段或下一交易日的波动率预测？

## 主题说明

波动率比短期方向更具有持续性，因此更适合短周期课程项目。研究可以先从高频成交计算已实现波动率，再加入价差、深度、订单流和跨品种共性，比较传统HAR-RV与机器学习模型，并进一步检验VaR或风险管理价值。

## 可用数据

股票、股指期货、原油、有色或农产品逐笔/分钟数据，以及盘口深度、成交量和订单流特征。

## 建议阅读顺序

### 1. Corsi (2009), A Simple Approximate Long-Memory Model of Realized Volatility

- 文件：`01_Corsi_HAR_RV.pdf`
- 用途：必要基准。理解日、周、月不同期限波动成分和HAR-RV设定。
- 公开来源：https://statmath.wu.ac.at/~hauser/LVs/FinEtricsQF/References/Corsi2009JFinEtrics_LMmodelRealizedVola.pdf

### 2. Zhang et al., Volatility Forecasting with Machine Learning and Intraday Commonality

- 文件：`02_Zhang_et_al_ML_and_Intraday_Commonality.pdf`
- 用途：核心扩展。参考跨资产共性、机器学习面板和样本外评价。
- 公开来源：https://arxiv.org/pdf/2202.08962

### 3. Moreno-Pino & Zohren, DeepVol

- 文件：`03_DeepVol_Deep_Learning_Volatility_Forecasting.pdf`
- 用途：深度学习扩展。参考扩张因果卷积和从高频数据直接预测波动率。
- 公开来源：https://arxiv.org/pdf/2210.04797

## 研究注意事项

推荐同时报告MAE、MSE、QLIKE和基于预测波动率的风险管理指标。
