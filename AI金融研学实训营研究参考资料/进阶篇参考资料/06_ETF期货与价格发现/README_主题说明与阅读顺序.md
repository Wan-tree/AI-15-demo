# 6. ETF、期货与成分股之间的高频价格发现

**研究问题：** ETF、股指期货或不同期限合约中，哪个市场更快吸收信息，领先关系是否随流动性和市场状态变化？

## 主题说明

该方向首先是市场微观结构研究，其次才是AI研究。学生应先使用协整、VECM、信息份额或成分份额量化价格发现，再用机器学习预测价格领导者或价格发现份额的动态变化。

## 可用数据

沪深300ETF与IF、上证50ETF与IH、中证500ETF与IC，或同一商品的近远月合约逐笔数据。

## 建议阅读顺序

### 1. de Jong, Measures of Contributions to Price Discovery

- 文件：`01_de_Jong_Measures_of_Contributions_to_Price_Discovery.pdf`
- 用途：方法入门。梳理多个价格发现测度及其比较。
- 公开来源：https://papers.tinbergen.nl/01114.pdf

### 2. Hasbrouck, Price Discovery in High Resolution

- 文件：`02_Hasbrouck_Price_Discovery_in_High_Resolution.pdf`
- 用途：高频方法。理解高分辨率数据、异步交易和短期动态对价格发现测度的影响。
- 公开来源：https://people.stern.nyu.edu/jhasbrou/Research/HRVAR/HRVAR08.pdf

### 3. Li, Chen & Liu (2025), High-Frequency Lead-Lag Relationships in the Chinese Stock Index Futures Market

- 文件：`03_Chinese_Index_Futures_High_Frequency_Price_Discovery.pdf`
- 用途：中国实证。参考逐笔数据、跨期限价差及领先—滞后关系。
- 公开来源：https://arxiv.org/pdf/2501.03171

## 研究注意事项

补充经典文献：Hasbrouck (1995) One Security, Many Markets；Gonzalo & Granger (1995)；Baillie et al. (2002)。正式全文可通过学校数据库获取。
