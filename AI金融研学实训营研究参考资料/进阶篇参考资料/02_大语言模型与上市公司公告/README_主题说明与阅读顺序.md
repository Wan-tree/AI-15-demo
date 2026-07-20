# 2. 大语言模型与上市公司公告事件因子

**研究问题：** 大语言模型能否从公告长文本中提取事件、金额、确定性和增量信息，并预测公告后的收益或风险？

## 主题说明

这一方向不是简单做“正面/负面”分类，而是把非结构化公告转成可检验的事件字段，例如事件类型、涉及金额、是否超预期、执行进度和不确定性。学生需要制作小规模人工金标准，比较关键词、FinBERT与LLM，并检验文本变量相对传统公告分类是否有增量价值。

## 可用数据

聚源公告全文、公告类别与发布时间、公司基本面、行情；建议只选业绩预告、回购增持、重大合同、问询函等一类事件。

## 建议阅读顺序

### 1. Chen et al. (2025), A Dataset for Document-Level Chinese Financial Event Extraction

- 文件：`01_Chen_et_al_DocFEE_Chinese_Financial_Event_Extraction.pdf`
- 用途：核心精读。参考中文长公告的事件类型、参数字段、标注规范和模型评价。
- 公开来源：https://www.nature.com/articles/s41597-025-05083-9.pdf

### 2. Araci (2019), FinBERT: Financial Sentiment Analysis with Pre-trained Language Models

- 文件：`02_Araci_FinBERT.pdf`
- 用途：基准方法。用于建立传统预训练金融文本模型，并和通用LLM比较。
- 公开来源：https://arxiv.org/pdf/1908.10063

### 3. Lopez-Lira & Tang, Can ChatGPT Forecast Stock Price Movements?

- 文件：`03_Lopez_Lira_Tang_ChatGPT_Stock_Price_Movements.pdf`
- 用途：应用精读。参考提示词、新闻解释、预测标签和投资组合检验，同时注意其结论的样本外稳定性。
- 公开来源：https://arxiv.org/pdf/2304.07619

## 研究注意事项

建议每组人工核验200—500份公告；LLM输出必须保存模型版本、提示词、温度和运行日期。
