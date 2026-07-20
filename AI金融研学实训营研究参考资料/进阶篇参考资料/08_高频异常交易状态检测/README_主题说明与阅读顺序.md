# 8. 高频异常交易状态与订单簿异常检测

**研究问题：** 在缺少完整监管标签时，无监督或半监督模型能否识别集中报撤单、流动性消失和异常盘口状态？

## 主题说明

本主题应把输出定义为“异常状态评分”，而不是直接认定市场操纵。研究可以构造报撤单强度、盘口失衡、价差跳升和成交异常等特征，比较Isolation Forest、自编码器和Transformer，并检验异常得分对后续波动或流动性恶化的预测作用。

## 可用数据

股票或期货逐笔委托、成交、撤单、盘口深度，以及必要的人工案例标签。

## 建议阅读顺序

### 1. DeLise (2023), Deep Semi-Supervised Anomaly Detection for Finding Fraud in the Futures Market

- 文件：`01_DeLise_Deep_Semi_Supervised_Anomaly_Detection_Futures.pdf`
- 用途：核心应用。与期货逐笔数据和少量标签场景高度契合。
- 公开来源：https://arxiv.org/pdf/2309.00088

### 2. Bao & Wang, A Deep Learning Approach to Anomaly Detection in High-Frequency Trading Data

- 文件：`02_Transformer_Anomaly_Detection_High_Frequency_Trading.pdf`
- 用途：深度模型。参考滑动窗口、注意力机制和高频异常评分。
- 公开来源：https://arxiv.org/pdf/2504.00287

### 3. Letteri et al., Comparative Analysis of Outlier Detection in Bitcoin Limit Order Books

- 文件：`03_Outlier_Detection_Bitcoin_Limit_Order_Books.pdf`
- 用途：方法比较。参考统计模型与机器学习异常检测的统一评价框架。
- 公开来源：https://arxiv.org/pdf/2507.14960

## 研究注意事项

论文或答辩中应使用“异常”“疑似异常”“需进一步核查”等表述，不能仅凭模型输出作法律或监管定性。
