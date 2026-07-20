# 3. 财务造假与财务困境预警

**研究问题：** 公开财务、审计和公司事件信息能否提前识别ST、重述、非标审计或监管处罚风险？

## 主题说明

该方向适合把AI定位为风险筛查工具。重点在于定义清晰的未来标签、避免把风险发生后的信息泄漏到特征中，并处理严重类别不平衡。评价应优先采用PR-AUC、召回率、误报率和提前预警期，而不是只报告总体准确率。

## 可用数据

聚源财务报表、现金流、审计意见、事务所变更、股权质押、担保、诉讼、处罚、ST与退市记录。

## 建议阅读顺序

### 1. Dechow, Ge, Larson & Sloan (2011), Predicting Material Accounting Misstatements

- 文件：`01_Dechow_et_al_Predicting_Material_Accounting_Misstatements.pdf`
- 用途：经典基准。重点学习F-Score变量、标签定义和财务错报的经济解释。
- 公开来源：https://gyanresearch.wdfiles.com/local--files/alpha/SSRN-id997483.pdf

### 2. Jofre & Gerlach (2018), Fighting Accounting Fraud Through Forensic Data Analytics

- 文件：`02_Jofre_Gerlach_Fighting_Accounting_Fraud_Data_Analytics.pdf`
- 用途：机器学习应用。参考公开会计变量、样本外分类和可解释性分析。
- 公开来源：https://arxiv.org/pdf/1805.02840

### 3. Sharma & Panigrahi, A Review of Financial Accounting Fraud Detection Based on Data Mining Techniques

- 文件：`03_Sharma_Panigrahi_Review_Financial_Accounting_Fraud_Detection.pdf`
- 用途：入门综述。了解Logit、决策树、神经网络等方法在财务欺诈检测中的传统用法。
- 公开来源：https://arxiv.org/pdf/1309.3944

## 研究注意事项

补充核心文献：Bao et al. (2020), Detecting Accounting Fraud in Publicly Traded U.S. Firms Using a Machine Learning Approach，正式期刊版可通过学校数据库获取。
