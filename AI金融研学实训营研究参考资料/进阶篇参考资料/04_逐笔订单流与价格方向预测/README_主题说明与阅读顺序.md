# 4. 逐笔订单流与短期价格方向预测

**研究问题：** 盘口深度、订单流不平衡和撤单行为能否预测未来若干事件或若干秒后的中间价方向？

## 主题说明

这个方向技术展示效果强，但最容易发生样本泄漏和“高准确率、不可交易”的问题。学生应按交易日划分样本，明确事件时间或物理时间标签，并把价差、手续费、排队成交和信号延迟纳入经济价值检验。

## 可用数据

上交所、深交所或期货交易所逐笔委托、逐笔成交、撤单和多档盘口数据。

## 建议阅读顺序

### 1. Zhang, Zohren & Roberts, DeepLOB

- 文件：`01_Zhang_Zohren_Roberts_DeepLOB.pdf`
- 用途：核心模型。重点学习订单簿张量、标签定义、CNN提取盘口空间结构和LSTM捕捉时序依赖。
- 公开来源：https://arxiv.org/pdf/1808.03668

### 2. Briola, Bartolucci & Aste, Deep Limit Order Book Forecasting: A Microstructural Guide

- 文件：`02_Briola_Bartolucci_Aste_Deep_LOB_Forecasting_LOBFrame.pdf`
- 用途：研究规范。重点看模型评价、数据切分和预测指标与交易收益不一致的问题。
- 公开来源：https://arxiv.org/pdf/2403.09267

### 3. Ntakaris et al., Benchmark Dataset for Mid-Price Forecasting of Limit Order Book Data

- 文件：`03_Ntakaris_et_al_FI2010_LOB_Benchmark_Dataset.pdf`
- 用途：数据基准。参考高频订单簿特征、标准化、预测区间和基准模型。
- 公开来源：https://arxiv.org/pdf/1705.03233

## 研究注意事项

建议助教预先提供统一的订单簿重建和标签代码，学生集中研究模型与经济解释。
