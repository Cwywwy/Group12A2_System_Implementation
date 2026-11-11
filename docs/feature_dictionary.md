# 特征字典（Feature Dictionary）

- 项目：Group12A2 · Screening Financial Disclosure Risk through Textual-Financial Feature Fusion and Explainable Anomaly Detection
- 版本：v0.2（2026-11-11；词典升级为完整公开词表、词频改词元匹配，基准改双口径，见 §4、§5）
- 对应大纲：§V.A（6 金融特征）、§V.B（3 文本特征）、§V.C（Beneish M-Score 基准）

本文档固化全部变量定义与公式，论文方法与复现脚本以此为准。

## 1. 样本与预处理规则

- 样本：A 股制造业（CAPCO 分类 IndustryCodeD 前缀 C）2021–2023 firm-year；基期 2020 用于增长率与 M-Score t−1 项。
- 缺失值：按公司-年份对齐后直接缺失（不插补）；特征表记录每特征缺失计数，写入 outputs/reports/missingness.csv。
- Winsorise：每列在 (1%, 99%) 分位截尾（`src/features/standardise.py::winsorize_columns`，逐列、跨组统一分位）。
- 标准化：winsorise 后按「制造业子行业(CAPCO 2 位码)-年份」组内 z 标准化（ddof=0）；组内样本 < 20 时退回全样本均值/标准差（大纲规定的 sparse fallback）。
- 异常分方向：模型输出的异常分统一转化为「越大越异常」，再做排名（主模型原始分数若为负向则取反，代码中记录校正过程）。

## 2. 金融特征（6 个，§V.A）

中间表模式（`src/features/financial.py::FINANCE_COLS`，由 CSMAR 三表映射而来）：

| 字段 | 含义 | CSMAR 来源 |
| --- | --- | --- |
| revenue | 营业收入 | FS_Comins |
| cogs | 营业成本 | FS_Comins |
| total_assets | 资产总计 | FS_Combas |
| total_liabilities | 负债合计 | FS_Combas |
| current_assets | 流动资产合计 | FS_Combas |
| current_liabilities | 流动负债合计 | FS_Combas |
| receivables | 应收账款净额 | FS_Combas |
| fixed_assets | 固定资产净额 | FS_Combas |
| long_term_debt | 长期借款 | FS_Combas |
| cash | 货币资金 | FS_Combas |
| depreciation | 固定资产折旧 | FS_Comscfd |
| sga | 销售费用 + 管理费用 | FS_Comins |
| net_income | 净利润 | FS_Comins |
| ocf | 经营活动产生的现金流量净额 | FS_Comscfd |

公式（下标 t 为当年，t−1 为上一年）：

1. roa = net_income_t / total_assets_t
2. leverage = total_liabilities_t / total_assets_t
3. revenue_growth = (revenue_t − revenue_{t−1}) / revenue_{t−1}
4. ocf_to_assets = ocf_t / total_assets_t
5. receivables_turnover = revenue_t / receivables_t
6. accruals_to_assets = (net_income_t − ocf_t) / total_assets_t

## 3. 文本特征（3 个，§V.B）

- 提取：年报 PDF → 文本层（pypdf）→ 定位「管理层讨论与分析」标题，截取至下一「第X节」标题（`src/features/textual.py::locate_mda`）。扫描件无文本层 → 记 status=no_mda，逐项列入缺失报告（大纲要求）。
- 分词：jieba（默认词典，HMM 开）+ 加载 `data/external/dictionaries/jieba_userdict.txt` 自定义词表（含全部词典词，保证多字金融词整词切分）；仅保留纯中文词元。
- 词频计数：词典词在 MD&A 词元序列上的**精确词元匹配**计数（`src/features/textual.py::count_dictionary_tokens`），每个词元命中一次；非子串计数，重叠词（如「增长」与「高增长」）经整词切分后各自独立计数。

| 特征 | 公式 | 说明 |
| --- | --- | --- |
| readability | 1 / 平均句长（句长按字符计，句子以 。！？； 切分） | 透明长度-复杂度代理：句子越长可读性越低，取值 (0, 1]；思路参考 Xu-Yao-Chen (2019) 中文可读性测度 |
| sentiment_balance | (正向词数 − 负向词数) / 总词元数 | 词典见 §5；正值偏乐观 |
| uncertainty_ratio | 不确定词数 / 总词元数 | 词典见 §5 |

## 4. Beneish M-Score（§V.C，仅作基准）

8 变量模型，系数与常数按 Beneish (1999) 原文：

- M = −4.84 + 0.920·DSRI + 0.528·GMI + 0.404·AQI + 0.892·SGI + 0.115·DEPI − 0.172·SGAI + 4.679·TATA − 0.327·LVGI
- 比率定义（全部用 t 与 t−1 的中间表字段）：
  - DSRI = (receivables_t/revenue_t) / (receivables_{t−1}/revenue_{t−1})
  - GMI = ((revenue_{t−1}−cogs_{t−1})/revenue_{t−1}) / ((revenue_t−cogs_t)/revenue_t)
  - AQI = (1 − (current_assets_t+fixed_assets_t)/total_assets_t) / (1 − (current_assets_{t−1}+fixed_assets_{t−1})/total_assets_{t−1})
  - SGI = revenue_t / revenue_{t−1}
  - DEPI = (depreciation_{t−1}/(depreciation_{t−1}+fixed_assets_{t−1})) / (depreciation_t/(depreciation_t+fixed_assets_t))
  - SGAI = (sga_t/revenue_t) / (sga_{t−1}/revenue_{t−1})
  - LVGI = (total_liabilities_t/total_assets_t) / (total_liabilities_{t−1}/total_assets_{t−1})
  - TATA = (net_income_t − ocf_t) / total_assets_t
- 用法：**绝不进入训练集**，仅用于 Spearman 相关与 top-k 事件率。基准事件采用双口径：
  - legacy：M > −1.78（Beneish 1999 原阈值；在中国样本下会标记多数样本，见结果章节讨论）。
  - calibrated（默认）：按样本自身分布取 M-Score 前 10% 分位（`config.py::BENEISH_TOP_QUANTILE = 0.10`），避免原阈值不适用的噪声。

## 5. 词典（v0.2，完整公开词表）

- 正向/负向：`data/external/dictionaries/financial_positive.txt` / `financial_negative.txt`。v0.2 采用姚加权等 (2021)《语调、情绪及市场影响：基于金融情绪词典》公开词表的**正式文本版**（`yuanjiaguan_2021/Yao2021_formal_sentiment_score.txt`，管理科学学报 24(5):26–46），只保留纯中文词元后得正向 3,585 词、负向 1,633 词。来源：DavionWu2018/Sentiment_dictionary（GitHub）。
- 不确定性：`data/external/dictionaries/uncertainty.txt`。参考 Loughran-McDonald (2011) uncertain 词中译与曾庆生等 (2018) 语调研究常用词并扩充（约 100 词）。
- 自定义词表：`data/external/dictionaries/jieba_userdict.txt`（5,218 行，「词 1000」格式），供 jieba 整词切分。
- 复现说明：词典文件逐行一词、# 开头为注释；v0.1 引导版三文件已备份至 `data/archive_v0.1/dictionaries/`。

## 6. 版本记录

- v0.1（2026-11-05）：全部公式、中间表模式、预处理规则固化；词典为引导版。
- v0.2（2026-11-11）：词典升级为姚加权等 (2021) 完整正式文本词表（3,585 正 / 1,633 负）+ 扩充不确定性词表；词频计数由子串改为 jieba 词元精确匹配；Beneish 基准由单一 −1.78 改为 legacy/calibrated 双口径（calibrated 为样本前 10% 分位）。
