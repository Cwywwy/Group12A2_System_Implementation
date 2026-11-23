# 面向 AI 的项目交接报告（Handoff for an AI Agent）

> 读者：另一个 AI 助手 / 自动化 agent。目标：你不读代码、不跑管线，也能准确复原这份工作做了什么、改了什么、数据从哪来、哪里被坑过、现在还剩什么。
> 生成时间：2026-11-24。仓库根目录：`D:\UM study life\session 1\Intro Fintec\Final\DSW`（Windows / PowerShell）。
> 本文件是**新增文档**，不替代 `README.md`、`GUIDE.md`、`CHANGELOG.md`；三者中的部分数字已过期，见 §9。

---

## 0. 给 AI 的阅读协议（先读这一节，能省你两小时）

### 0.1 真源等级（可信度从高到低）

| 等级 | 来源 | 为什么可信 | 用法 |
| --- | --- | --- | --- |
| A | `outputs/tables/*.csv` | 管线现算产物，论文所有头条数字的源头 | 引用任何数字前先来这里核 |
| A | `data/processed/feature_table.csv`、`event_table.csv` | 建模输入，行数与键集可自证 | 核对样本量、事件率 |
| B | `outputs/reports/data_audit_2026-11-23.md` + `.json` | 49 项机械审计，逐值比对原始表 | 判断数据是否可信 |
| B | `11.23base/核对报告-2026-11-23.md` | 人工核对组员疑问、定位两大缺陷的原始记录 | 想知道「为什么改」 |
| C | `CHANGELOG.md` | 按日期分组的变更流水，密度极高 | 时间线、修复理由 |
| D | `docs/*.md`（复现指南、特征字典、项目地图） | 方法描述准确，个别数字滞后 | 方法定义以此为准 |
| E | `README.md`、`GUIDE.md`、`docs/team_handoff.md` | 已于 2026-11-24 同步到 v0.3 口径（n=9,239、ρ=−0.021、AUC 0.802），但只覆盖「头条数字」层 | 结构与入口可放心看；细节数字仍以 `outputs/tables/` 为准 |
| F | `11.23base/*.docx`、根目录旧副本 | 历史存档，命名含 corrected/revised | 只作比对，不作交付 |

### 0.2 三条硬约束

1. **`data/` 不入 git**（`.gitignore` 第 15 行 `data/`）。`git clone` 下来的仓库没有数据、没有课程材料、没有 `.univer`。交接必须单独说明数据获取方式，见 §3.1。
2. **不要拿已交付的 docx 当输入重新插表**。`scripts/build_section5.py` 从 `outputs/manuscript/source/`（不含表格的母版）读、往 `outputs/manuscript/` 写；直接拿交付件当输入会重复插表并冲掉段落槽位（`docs/reproducibility_guide.md:186`）。
3. **数据不可外传**：CSMAR 三表与巨潮年报 PDF 仅限本课程作业使用；对外只带 `outputs/` 与 `course_materials/Copyright notice.pdf`。

### 0.3 五分钟自检（判断仓库是否处于「可交付」状态）

```powershell
& ".venv\Scripts\python.exe" -m pytest -q          # 应为 172 passed（约 30 s）
& ".venv\Scripts\python.exe" scripts\run_16_verify_manuscript.py   # 交付件 = 当前管线输出？
git status --short                                  # 应为空
git log --oneline -1                                # 应为 22d2b16
```

当前实测（2026-11-24 复核）：**130 passed / 3 warnings / 21.10 s**，工作树干净，HEAD = `22d2b16 build: compress the compact manuscript to 15 pages with a separate appendix`。

---

## 1. 这个项目到底是什么

**课程**：Introduction to FinTech（2026），Group 12A2，Option 2 = Research Manuscript。

**题目**：*Screening Financial Disclosure Risk through Textual-Financial Feature Fusion and Explainable Anomaly Detection: Evidence from Chinese A-share Manufacturing Firms, 2021–2023*
（中文：财务披露风险筛查——文本-财务特征融合与可解释异常检测，基于中国 A 股制造业 2021–2023）

**研究问题**：

| 编号 | 问题 | 判定标准 |
| --- | --- | --- |
| RQ1 | 财务异常分是否与 Beneish M-Score 排序一致？加入 MD&A 文本特征是否带来增量？ | Spearman ρ 与 top-k 富集率 |
| RQ2 | 哪些特征驱动异常判定？ | SHAP 全局 / 分组 / 单条 |
| RQ3 | 自编码器能否复现 Isolation Forest 的排序？ | 秩相关 + top-10% 名单重叠 |

**结论（阴性为主，论文如实报告）**：财务特征与 M-Score 呈**弱负相关**（ρ = −0.021，但 p = 0.0398）；文本特征**没有增量**（融合 ρ = −0.018，p = 0.0915）；自编码器**未复现**（ρ = −0.0066，p = 0.528）。但换成**真实监管事件**做结果变量后，财务排序对非标审计意见 AUC = **0.8015**，远好于 Beneish 代理的 **0.2418**（低于随机，方向相反）。

> ⚠ 关键认知转变：项目最初想证明「文本有用」，两轮数据修复后结论变成「代理基准本身是坏的」，最终论文立场是**测量批判 + 真实事件外部检验**。任何接手者若把结论写成「发现了财务舞弊」，就是误读。

---

## 2. 当前基线（一页纸）

```json
{
  "sample": {"firm_years_frame": 10172, "firms_frame": 3694,
             "firm_years_modelled": 9239, "firms_modelled": 3488,
             "by_year": {"2021": 2732, "2022": 3124, "2023": 3383},
             "exclusions": "9 个特征 + m_score 全非空（完整案例）"},
  "text": {"pdf_ok": 10051, "pdf_missing": 121, "coverage": 0.9881,
           "text_quality": {"ok": 9991, "suspicious": 7, "missing": 174}},
  "beneish": {"m_score_rows": 9414, "m_score_rows_in_sample": 9239,
              "legacy_flagged": 1686, "legacy_share": 0.1825,
              "calibrated_top10_threshold": -1.4366,
              "m_score_range": [-387.06, 9182.95], "m_score_abs_gt_20": 33},
  "spearman_vs_mscore": {"if_finance": -0.0214,  "if_finance_p": 0.0398,
                          "if_text": -0.0259,     "if_text_p": 0.0127,
                          "if_fused": -0.0176,    "if_fused_p": 0.0915,
                          "ae_fused": -0.0066,    "ae_fused_p": 0.5279},
  "top10_enrichment_calibrated": {"if_finance": 2.4456, "if_text": 0.9090,
                                  "if_fused": 2.0993, "ae_fused": 1.9587},
  "top10_enrichment_legacy": {"if_finance": 1.6902, "if_text": 0.8362,
                              "if_fused": 1.5597, "ae_fused": 1.5716},
  "external_auc_mod_opinion": {"finance_if": 0.8015, "text_if": 0.5197,
                                "fused_if": 0.7692, "fused_ae": 0.6899,
                                "beneish": 0.2418},
  "events": {"mod_opinion": 204, "mod_opinion_wide": 355,
             "violation_any_t1": 1965, "violation_disclosure_t1": 1337},
  "shap_group_share": {"finance": 0.6615, "text": 0.3385},
  "top1_symbol": "600870"
}
```

出处：`outputs/reports/experiment_summary.md`、`outputs/tables/model_metrics.csv`、`outputs/tables/topk_metrics.csv`、`outputs/tables/event_ranking_metrics.csv`、`outputs/tables/shap_group_contributions.csv`。JSON 中的数值是精确值的四舍五入。

---

## 3. 数据：用了什么、从哪来、多大、什么口径

### 3.1 五个数据源

| 数据 | 本地路径 | 体量 | 获取方式 | 授权 |
| --- | --- | --- | --- | --- |
| CSMAR 三大报表（资产负债表/利润表/现金流量表） | `data/raw/csmar/FS_Combas.xlsx`、`FS_Comins.xlsx`、`FS_Comscfd.xlsx` | 172.3 / 237.5 / 91.3 MB | 组员从 CSMAR 手动下载 2020-01-01~2023-12-31 合并口径 | 课程授权，不可外传 |
| CSMAR 上市公司名单 | `data/raw/csmar/STK_LISTEDCOINFOANL.xlsx` | 17.0 MB | 同上 | 同上 |
| 巨潮（cninfo）年报 PDF | `data/raw/cninfo/{2021,2022,2023}/*.pdf` | 磁盘现有 20,149 份 / 79.6 GB（含 2024 目录与清单外代码）；审计口径 10,051 ok + 121 missing | `scripts/run_02_download_annual_reports.py` 自动下载，断点续传 | 公开披露但站点有限速，仅课程用 |
| CSMAR 审计意见 / 违规处理 | `data/raw/csmar_events/FIN_Audit.xlsx`、`STK_Violation_Main.xlsx` | 19.9 MB | 手动下载 | 课程授权 |
| 情感词典（姚加权等 2021 正式文本版） | `data/external/dictionaries/` | 0.87 MB | 公开 GitHub 镜像 + 手工清洗 | 可分享 |

> 磁盘上 PDF 总量（20,149）远大于审计口径（10,172），因为 2021–2024 四个年目录里还混有清单外代码与历史重下件；`run_02` 只按 `download_checklist.csv`（3,694 家）下载。别用目录文件数当样本量。

### 3.2 样本框怎么定的（可复核）

- 唯一来源：`data/raw/csmar/STK_LISTEDCOINFOANL.xlsx`。
- 制造业判定：`IndustryCodeD` 以 `"C"` 开头（CAPCO 分类，`src/config.py:38 MANUFACTURING_PREFIX="C"`）。用 CAPCO 而非 2012 证监会代码，原因是 2023 年该列在 CSMAR 中缺失。
- 年份：2021–2023；2020 只作基期（`BASE_YEAR=2020`），用于增长率与 M-Score 的 t−1 项。
- **没有**显式 A 股过滤，**没有** ST/退市剔除。实测含 205 家 920xxx 北交所公司与 2 家 8xxxxx，`docs/csmar_event_data_guide.md:123` 声称「已剔除部分退市/ST」与代码不符，属文档漂移。
- 结果：**3,694 家公司 / 10,172 firm-year**（2021: 3,165；2022: 3,404；2023: 3,603）。
- 产物：`data/processed/manufacturing_sample_frame.csv`（10,172×6）、`download_checklist.csv`（3,694×6，按年打 Y/空）。

### 3.3 三层数据（每层可单独核对，这是复现的关键）

```
data/raw/       原样下载（CSMAR xlsx / 巨潮 PDF / 事件表）        ← 不入库
data/interim/   标准化中间表（finance_intermediate 19,966×16；text_features_{年} 7 列；mda_text_{年}.jsonl 缓存 MD&A 原文）
data/processed/ 建模表（feature_table 10,172×20；event_table 9,239×15；审计/QC/日志）
```

**`data/processed/feature_table.csv` 表头（20 列，原样）**：

```
symbol,short_name,fiscal_year,industry_code_d,industry_name_d,end_date,
roa,leverage,revenue_growth,ocf_to_assets,receivables_turnover,accruals_to_assets,
m_score,text_status,readability,sentiment_balance,uncertainty_ratio,
n_tokens,n_sentences,text_quality
```

**`data/processed/event_table.csv` 表头（15 列，原样）**：

```
symbol,fiscal_year,audit_type,opinion_class,mod_opinion,mod_opinion_wide,
auditor,big4,audit_fee,announce_date,
violation_any_t1,violation_disclosure_t1,violation_any_t,violation_disclosure_t,
has_audit_record
```

**`data/interim/finance_intermediate.csv` 表头（16 列）**：`symbol,fiscal_year,revenue,cogs,total_assets,total_liabilities,current_assets,current_liabilities,receivables,fixed_assets,long_term_debt,cash,depreciation,sga,net_income,ocf`。

### 3.4 六个财务特征 + 三个文本特征（公式以 `docs/feature_dictionary.md` 为准）

财务（t 年，t−1 为上年）：
1. `roa = net_income_t / total_assets_t`
2. `leverage = total_liabilities_t / total_assets_t`
3. `revenue_growth = (revenue_t − revenue_{t−1}) / revenue_{t−1}`
4. `ocf_to_assets = ocf_t / total_assets_t`
5. `receivables_turnover = revenue_t / receivables_t`
6. `accruals_to_assets = (net_income_t − ocf_t) / total_assets_t`

文本（MD&A 章节）：
1. `readability = 1 / 平均句长`（句子按 `[。！？；]+` 切，句长按字符计，取值 (0,1]）
2. `sentiment_balance = (正向词数 − 负向词数) / 总词元数`
3. `uncertainty_ratio = 不确定词数 / 总词元数`

预处理（`src/features/standardise.py`）：每列全样本 (1%,99%) 缩尾 → 按 `(industry_code_d, fiscal_year)` 组内 z 标准化（`ddof=0`）→ 单元样本 <20 时整格回退全样本均值/标准差（`MIN_SUBINDUSTRY_YEAR_CELL=20`）。

> ⚠ `outputs/reports/descriptives_summary.md` 里的特征统计是**缩尾前原始值**：`leverage` 最大 5.906、`revenue_growth` 最大 944.10、`receivables_turnover` 均值 262.2 最大 1,764,970、标准差 17,698。这些极端值不是 bug，是原始比率的长尾；模型输入已被缩尾。论文表 5.1 也曾因此被误读（`11.23base/核对报告-2026-11-23.md` 第 ① 条）。

### 3.5 词典（v0.2）

- 正向 3,585 / 负向 1,633 词：姚加权、冯绪、王赞钧、纪荣嵘、张维《语调、情绪及市场影响：基于金融情绪词典》，《管理科学学报》2021, 24(5): 26–46。
- 不确定性约 100 词：参考 Loughran-McDonald (2011) 中译 + 曾庆生等 (2018) 扩充。
- `jieba_userdict.txt` 5,218 行，保证「营业收入」「商誉减值」这类多字金融词整词切分。
- 命中密度（同一 token 流，`outputs/tables/lexicon_density.csv`）：情感词 13.41 → 111.30 每千词元（**8.30×**）；不确定词 2.14 → 5.66（2.64×）。这是回应「是不是词表太薄才没信号」的关键证据。
- v0.1 引导版（38 正 / 33 负 / 23 不确定）已归档到 `data/archive_v0.1/dictionaries/`。

### 3.6 数据质量（机械审计，49/49 通过）

`scripts/run_02b_audit_data.py` → `outputs/reports/data_audit_2026-11-23.md`（JSON 同名）。覆盖 8 组：

1. 原始 CSMAR 期间分布（是否混入季报/期初数）；
2. 中间表年度范围与去重；
3. 六个科目逐值与原始年报比对（不一致 0）；
4. 期初数污染回归（39,610 可比行，命中 0）；
5. 一年滞后回归（14,493 可比行，命中 0）；
6. 特征可由中间表重算（roa/leverage/ocf/accruals/m_score，不一致 0）；
7. 特征格式与取值域（readability∈(0,1]、无 inf、symbol 6 位等）；
8. 事件表键集 = 建模样本（仅事件有 0，仅模型有 0）与输出表 NaN/inf。

---

## 4. 代码架构

### 4.1 目录

```
src/
  config.py            路径/超参/特征清单（唯一超参源）
  sample_frame.py      样本框与下载清单
  pipeline.py          建模主流程 run_pipeline(feature_csv, output_dir)
  data_ingestion/      csmar_parser.py、cninfo_client.py、event_parser.py
  features/            financial.py、textual.py、beneish.py、standardise.py、feature_table.py、qc.py
  models/              isolation_forest.py、autoencoder.py、shap_explain.py
  evaluation/          metrics.py、event_eval.py
  reporting/           figures.py、descriptives.py、narrate_results.py
scripts/               run_00…run_16、run_99 编排、build_* 组装器
tests/                 21 个文件 / 130 个用例 / 1,868 行
```

规模：`src/` 26 个 py 文件 2,496 行；`scripts/` 38 个 7,626 行；`tests/` 21 个 1,868 行。

### 4.2 `src/pipeline.py` 执行顺序（`run_pipeline`）

1. 读 `feature_table.csv`；**完整案例过滤** `dropna(subset=9 特征 + m_score)`（这就是 10,172 → 9,239 的原因）。
2. `winsorize_columns`（1%/99%）→ `standardise_within_groups`（子行业×年，<20 回退全样本）。
3. 拆三矩阵：财务 6 维 / 文本 3 维 / 融合 9 维。
4. 三个 `IsolationForest(n_estimators=500, max_samples=min(256,n), random_state=42)`；分数取 `-score_samples`（越大越异常）。融合模型被保留给 SHAP 复用，不重拟合。
5. 自编码器：`MLPRegressor`，结构 `(16, 8, 16)`、`relu`、`adam`、`alpha=1e-4`、`batch_size=256`、`lr=1e-3`、`max_iter=500`、`early_stopping=True`、`n_iter_no_change=20`、`validation_fraction=0.1`、`random_state=42`；以逐行 MSE 作异常分。超参写 `outputs/reports/autoencoder_config.json`。
6. 双基准：`legacy = m_score > -1.78`；`calibrated = M-Score 前 10%`（`round(n*0.1)` 个）。
7. 指标：Spearman（vs M-Score）、top-k（5/10/15%）事件率与富集、4×4 top-10% 重叠。
8. SHAP：`TreeExplainer` 对融合 IF；>2000 行时固定种子抽 1,999 行并**强制并入 top-1 行**。
9. 落盘：`model_metrics.csv`、`topk_metrics.csv`、`ranking_overlap.csv`、`anomaly_scores.csv`、`shap_global.csv`、`shap_group_contributions.csv`、`shap_local_top1.csv`。

### 4.3 关键超参（`src/config.py`）

`SEED=42`；`IF_N_ESTIMATORS=500`；`IF_MAX_SAMPLES=256`；`WINSOR_QUANTILES=(0.01,0.99)`；`MIN_SUBINDUSTRY_YEAR_CELL=20`；`BENEISH_THRESHOLD=-1.78`；`BENEISH_TOP_QUANTILE=0.10`；`SAMPLE_YEARS=(2021,2022,2023)`；`BASE_YEAR=2020`；`FIN_YEARS=(2020..2023)`；`SHAP_SAMPLE_CAP=2000`（在 `pipeline.py:67` 硬编码，不在 config）。

### 4.4 指标定义（写论文时必须一致）

| 指标 | 定义 | 代码 |
| --- | --- | --- |
| Spearman ρ | 异常分与 `m_score` 的秩相关，逐模型 | `src/evaluation/metrics.py:18` |
| top-k 事件率 | 前 k 名单内 `flags` 均值 | `metrics.py:27` |
| 富集率 | 事件率 / 全样本事件率（基线 0 → NaN） | `metrics.py:33` |
| top-10% 重叠 | `|A∩B| / |A|`（只除 A 侧） | `metrics.py:41` |
| AUC 区间 | 行级 bootstrap 1,000 次、百分位 [2.5,97.5] | `event_eval.py:53` |
| ΔAUC | 同一批重抽索引配对算 A、B 的 AUC 差 | `event_eval.py:214` |
| OOF AUC | `StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42)`，`groups=symbol` | `event_eval.py:188` |

分类器：logit = 中位数插补 + 标准化 + `LogisticRegression(max_iter=2000, class_weight="balanced")`；hgb = 中位数插补 + `HistGradientBoostingClassifier(max_iter=300, lr=0.05, max_leaf_nodes=15, min_samples_leaf=40, l2=1.0)`。

### 4.5 脚本阶段表（谁是正式管线，谁是组装器）

| 阶段 | 脚本 | 产物 |
| --- | --- | --- |
| 环境 | `run_00_env_check.py` | 终端 14 项就绪检查 |
| 导出检查 | `run_00c_inspect_csmar_export.py` | 新下载 CSMAR 的 sheet/列名/前导零 |
| 样本 | `run_01_sample.py` | 样本框、下载清单 |
| 下载 | `run_02_download_annual_reports.py --year` | `data/raw/cninfo/{年}/*.pdf` |
| 财务中间表 | `run_03_build_finance_intermediate.py` | `finance_intermediate.csv` 19,966×16 |
| 演示数据（**不是正式**） | `run_03_make_demo_data.py` | 240 行冒烟数据 |
| 事件表 | `run_03b_build_event_table.py` | `event_table.csv` 9,239×15 |
| 下载审计 | `run_04_audit_downloads.py` | `download_audit.csv` 10,172 行 |
| 文本提取 | `run_05_extract_mda_features.py --year`（增量）/ `run_05b_recompute_text_features.py --workers 8`（并行全量） | `text_features_{年}.csv`、`mda_text_{年}.jsonl` |
| 词典密度 | `run_05c_lexicon_density.py` | `lexicon_density.csv` |
| 特征表 | `run_06_build_feature_table.py` | `feature_table.csv` 10,172×20 |
| 建模 | `run_07_experiment.py` | 7 张表 + 8 张图 + 实验摘要 |
| 事件检验 | `run_07b_event_models.py --boot 400` | `event_ranking_metrics.csv`、`event_supervised_metrics.csv` |
| QC | `run_08_qc_report.py` | `qc_summary.csv`、`qc_issues.csv` |
| 定向重下 | `run_09_repair_downloads.py`（默认 dry-run，`--apply` 才下） | `repair_log_*.csv` |
| 北交所补下 | `run_10_bse_legacy_download.py` | 同上 |
| 描述统计 | `run_11_descriptives.py` | `descriptives_summary.md` |
| 结果叙事 | `run_12_narrate_results.py` | `results_narrative.md` |
| 中文 Word | `run_13_build_chinese_docx.py` | `Group12A2_Final_CN.docx` |
| 发布 PDF | `run_14_publish_pdfs.py` | 覆盖 `outputs/manuscript/*.pdf`，被占用时退出码 2 |
| 清理 | `run_15_cleanup_workspace.py [--apply]` | 清 `_trash/`、探针 `.univer` |
| 交付件自检 | `run_16_verify_manuscript.py` | 重建 docx 与交付件逐段比对 |
| 数据审计 | `run_02b_audit_data.py` | 49 项审计报告 |
| 一键流程 | `run_99_full_pipeline.py [--stage ...] [--skip-05]` | 全流程，退出码 2 = 前置未就绪 |

组装器（不属于数据阶段，改论文/PPT/Excel 才用）：`build_section5.py`（§5 + 表 + §5.6/5.7/5.8）、`build_report_figures.py`（重画 6 图并塞进 docx）、`build_results_excel.py`（7 表 + 6 原生图，`--lang en`）、`build_slides.py`（12 页 deck）、`patch_manuscript_docx.py`（函数式就地打补丁 + 精简版/附录）、`compare_runs.py`、`analyze_branch_beneish_components.py`。

---

## 5. 结果（v0.3 最终口径）

### 5.1 主结果（相对 Beneish M-Score）

| 模型 | ρ | p | calibrated 富集（top-10%） | legacy 富集 |
| --- | --- | --- | --- | --- |
| if_finance | −0.0214 | 0.0398 | 2.4456 | 1.6902 |
| if_text | −0.0259 | 0.0127 | 0.9090 | 0.8362 |
| if_fused | −0.0176 | 0.0915 | 2.0993 | 1.5597 |
| ae_fused | −0.0066 | 0.5279 | 1.9587 | 1.5716 |

- 只有财务与文本单独显著；融合在 10% 边际上不显著。
- **方向为负**：异常分越高，M-Score 越低。这不是符号错误，是「M-Score 刻画收入虚增型操纵、而本文特征捕捉困境型异常」的实质发现（见 §5.4）。
- top-10% 重合：finance–fused **0.7965**、finance–text 0.1320、fused–text 0.2857、finance–AE 0.4545。融合基本由财务主导。

### 5.2 SHAP（RQ2）

- 组贡献：财务 **66.15%** / 文本 **33.85%**。
- 全局均值 |SHAP| 极平：最高 `accruals_to_assets` 0.3138，最低 `leverage` 0.2535，九特征全在 0.25–0.31 带内 → 「没有单一主导特征」本身就是结论。
- top-1 局部解释（`shap_local_top1.csv`）由 `receivables_turnover`（−2.35）主导。

### 5.3 外部检验（§5.6，真实监管事件）

下表是**无监督排序 AUC**（IF 的 0–1 异常分 / AE / M-Score 直接当分数），出处 `outputs/tables/event_ranking_metrics.csv`；有监督 OOF 的 AUC 在下一节，两者**不可混用**。

| 标签 | 事件数 | 占比 | finance IF AUC | text IF | fused IF | AE | Beneish |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 非标审计意见（窄） | 204 | 2.21% | **0.8015** [0.774, 0.833] | 0.5197 | 0.7692 | 0.6899 | **0.2418** |
| 非标审计意见（宽，加强调事项） | 355 | 3.84% | 0.7812 | 0.5302 | 0.7591 | 0.6777 | 0.2762 |
| t+1 任意违规 | 1,965 | 21.27% | 0.5703 | 0.4970 | 0.5572 | 0.5439 | 0.4249 |
| t+1 披露类违规 | 1,337 | 14.47% | 0.5955 | 0.5027 | 0.5820 | 0.5572 | 0.4074 |
| t+1 披露类违规（严格门：公告日晚于年报披露日） | 1,040 | 11.26% | 0.6005 [0.584, 0.619] | 0.5119 | 0.5904 | — | 0.4135 |

> 严格门一行出自 `outputs/tables/event_ranking_metrics_strict.csv`：标签由 1,965 / 1,337 降为 1,543 / 1,040（丢 21.5% / 22.2%），结论不弱反强。宽松版的 0.5955 与严格版的 0.6005 是两个标签口径，不能互相替代引用。
> ⚠ 曾有版本把 `event_supervised_metrics.csv` 的 OOF 数（0.6723 / 0.5701 / 0.6733）填进本表，那是**有监督**结果，已更正。

- 前 10% 队列对非标意见的富集：finance **4.95×**，Beneish 0.64×（方向相反）。
- 有监督分组交叉验证（OOF）：logit finance 0.8648 / text 0.6804 / fused 0.8664，`Δfused−finance = +0.0016 [−0.0135, 0.0137]`；hgb finance 0.8611 / fused 0.8726，`Δ = +0.0115 [−0.0053, 0.0267]`。
- **表述纪律**：文本块单独在所有标签上都弱于财务；融合增量「小而一致为正」但 8 个组合**没有一个区间排除 0**。论文只能写「小且一致的互补增量」，不能写「文本显著提升」。

### 5.4 为什么 Beneish 方向是反的（这是论文最有价值的解释）

非标意见组 vs 其余：`TATA` −0.105 vs −0.011、`SGI` 0.885 vs 1.085、M-Score −3.05 vs −2.33。Beneish 的系数奖励**正应计与高增长**（TATA 系数 +4.679、SGI +0.892），所以「收入虚增型」公司 M-Score 高；而本文财务特征捕捉的是**困境/低增长型**异常（低应计、低增长），于是排序相反。代理基准不是噪声，是**测错了构念**。

### 5.5 §5.8 稳健性（样本/年份/结果定义）

- 行业×年份 2×2；逐年 q90 阈值；六种结果定义；两项零结果。
- 2021 年样本明显更弱；2023 年最强。逐年阈值下结论不变。
- 该节 766 词、表 5.7（9×6 双面板），数据来自 `DSW_all` / `DSW_dv` / `DSW_branch` 三处分支实验。

---

## 6. 三个版本与「改了什么」

| 版本 | 时间 | 核心改动 | 结果口径 |
| --- | --- | --- | --- |
| v0.1 基线 | 2026-11-05~10 | 引导版小词典（38/33/23）+ 子串计数 + 单一 `M>−1.78` 基准 | n=8,276；ρ finance 0.136 量级（后被证伪） |
| v0.2 校准版 | 2026-11-11 | 姚加权全量词典 + jieba 词元精确匹配 + legacy/calibrated 双基准；新增 §5.6、§5.7 | n=8,140；ρ 0.136/−0.029/0.103/0.009（后被证伪） |
| v0.3 修正版 | 2026-11-23 | ①三表按公司-年度合并（修 73.4% 滞后）②科目取列纠正（营业总收入→营业收入、营业总成本→营业成本）③DEPI 中性化 ④新增 §5.8 + 表 5.7 ⑤精简到 15 页 + 附录 | **n=9,239；ρ −0.021/−0.026/−0.018/−0.007；AUC 0.802** |

git：20 个提交、3 个 tag（`v0.1-baseline` = `542395b`、`v0.2-calibrated` = `b700d27`、`v0.3-events`）。第一版可用 `git worktree add ../v01 v0.1-baseline` 完整检出。

**时间线**：

- 11-05：环境（Python 3.12.14）、样本框 3,694 家、巨潮客户端、特征 v0.1、IF/AE/SHAP、47 个测试。
- 11-06：三路下载完成；北交所 920xxx 旧码方案；QC 模块；描述统计；§4 系统实现（23 段 / 约 2,600 词）。
- 11-10：CSMAR 三表到位，发现年份范围错（2022–2025）→ 重下 2020–2023；三年跑通 n=8,140；参考文献 [22]/[24] 查证补全。
- 11-11：v0.2 词典全量重提取（10,052 份 PDF，8 进程，2–3 小时）；§5.6 两版对比、§5.7 外部检验；目录五层整理（46 MB 出库）。
- 11-12：`run_16` 交付件自检，EN 109 段 / 6 表 = 重建结果。
- 11-22：中英结果汇总工作簿（各 7 表 + 6 原生图）。
- 11-23：**数据修复两轮**（滞后合并 → 取错列）→ 全量重跑 → §5.8 → 精简版 15 页 + 4 页附录 → 130 测试。

---

## 7. 踩过的坑（按「会再次咬人」排序）

### A. 数据层

**A1 三表按行号合并，73.4% 的年份资产负债表滞后一年。**
现象：M-Score 与收入对不上；收入仅 1.0% 能与原始报表对齐。根因：`combine_first` 按行位置合并，三表行数不同（96,528 / 115,931 / 96,525）。修复：`csmar_parser.build_finance_intermediate` 新增 `period_end`，只取 `12-31` 年报行，按 `["symbol","fiscal_year"]` 对齐（`scripts/run_03_build_finance_intermediate.py:91-111`）。回归：`data_audit` 的「一年滞后」检查（14,493 可比行，命中 0）。教训：**任何多表合并先建键，别信行序**。

**A2 科目取错列：`revenue` 取了「营业总收入」（B001100000），`cogs` 取了「营业总成本」。**
后果：毛利率均值 **−3.74**（用对后 +0.291）；M-Score 的 GMI/SGAI 全歪。修复：`CODE_ALIASES` 改为「营业收入 B001101000」与「营业成本 B001201000」，`probe_field_columns()` 按别名优先级查找。教训：CSMAR 的「总」字科目前缀是陷阱，**用毛利率符号做一次健全性检查**。

**A3 `depreciation` 列根本不存在。**
直接法现金流量表没有「固定资产折旧」行；旧别名误指「处置长期资产收回现金净额」。修复：别名置空，`src/features/beneish.py:50` 把 `DEPI` 钉为 1.0（中性化）。后果：每个 M-Score 含固定 `0.115` 项，DEPI 不区分公司——**这是已知方法缺陷，论文未单列，接手者应知道**。

**A4 CSMAR 下载年份窗口错。**
首次下载实际覆盖 2022–2025（资产负债表还含 2026Q1），缺 2020/2021 基期 → Beneish 只有 2023 年可算（2,979/3,603）。修复：按 `docs/csmar_download_guide.md` 重下 2020-01-01~2023-12-31 并覆盖。

**A5 季报与期初数混入。**
CSMAR 导出含 `01-01`（上年结转）、`03-31`、`06-30`、`09-30` 行；`01-01` 行会让「本年」读到上年数。修复：`period_end` 只留 `12-31`；审计里专设「期初数污染回归」（39,610 可比行，0 命中）。

**A6 北交所 920xxx 新旧代码。**
巨潮只按 2025-10 切换前的旧码收录 920xxx 公司；直接按 920 搜 0 命中。修复：`data/external/bse_920_code_mapping.csv`（248 行）做新旧对照，`search_annual_reports_bse` 用 `category=""` + `searchkey="年度报告"` 单页命中，按新码落盘（`run_10_bse_legacy_download.py`）。

**A7 年报标题式样与目录切片。**
两种标题（`2021年年度报告` / `2021年度报告`）都要认；`locate_mda` 原逻辑会选中目录行，把 MD&A 截成 56 字符（实例 000408 只有 4 tokens）。修复：`_has_annual_report_tag` 双式样 + 「标题独占一行且非目录行」才算强候选（`textual.py:93-95`）；实测 000008 从 67 → 7,835 tokens、000012 从 90 → 11,085 tokens。

**A8 跨年误选。**
原 `select_annual_report` 会在没有同年报告时回退到别的年份。修复：锁定同年（含「更新后/更新前/全文」变体），找不到返回 `None`；两轮 `run_09` 共恢复 20 个错位/缺失文件。

**A9 121 个 missing 是数据边界，不是 bug。**
其中约 71 个是 920xxx 公司在挂牌前的 NEEQ 三板年份（巨潮不收录三板公告），约 50 个是退市/重组/长期停牌。论文作为可得性边界陈述，不要试图补齐。

### B. 代码层

**B1 除零产生 ±inf。**
`src/features/beneish.py:62` 已 `replace([inf,-inf], nan)`；但 `src/features/financial.py:42-47` 仍无保护，`pipeline.py:91` 只 `dropna` 不 `dropna` inf → 若某列出现 inf，缩尾分位数会变 inf，z 分数整列变 NaN。当前数据未触发，**换数据必查**。

**B2 SHAP 子采样可能与 top-1 行错位。**
n>2000 时随机抽 1,999 行，top-1 可能不在样本内（`get_loc` KeyError）。修复：强制并入 top-1 行，并用 `shap_frame.index.get_loc(top1_index)` 对齐位置（`pipeline.py:161-176`）。注意：`work` 索引重复时 `get_loc` 会返回切片 — 当前 `feature_table` 索引唯一，未触发。

**B3 断点续传丢 `symbol`。**
`run_05` 重启时 `set_index('symbol').to_dict('index')` 丢索引列，carried-over 行 `symbol` 变 NaN，污染 2022/2023 共 175 行（QC 里出现 `'000nan'`）。修复：读回时重新挂回 symbol、过滤非法行、写盘前按 symbol 去重。

**B4 完整案例过滤造成「非同一财务样本」比较。**
`pipeline.py:91` 要求 9 特征 + m_score 全非空，于是 `if_finance` 也只在「文本可用」子样本上评估；三路模型不是同一财务样本上的嵌套比较。这是评审可能追问的点，论文未展开。

**B5 「top-decile」两套定义。**
`pipeline.py:118` 用 `round(n*0.1)` 个最高 M-Score；`descriptives.py:108` 用 `m.quantile(0.90)` 阈值。两者标记数通常不等（1,686 vs 1,731 的来源之一）。引用时必须写明用的是哪一种。

**B6 自编码器「瓶颈」几乎不压缩。**
结构 (16,8,16) 作用在 9 维输入上，瓶颈 8 ≈ 输入 9，重建误差接近恒等映射的噪声。这是「AE 未复现」的结构性原因之一，不只是数据问题。

**B7 bootstrap 次数不一致。**
`event_eval.py:38 DEFAULT_BOOTSTRAP=1000`，但 `run_07b_event_models.py` 默认 `--boot 400`；论文里的区间是 400 次。

**B8 巨潮检索只取第一页 30 条。**
`cninfo_client.py:113-114` 固定 `pageNum=1, pageSize=30`；命中 >30 时年报可能落在第 2 页被判 missing。当前 121 个 missing 已人工确认是边界，但换年份/换市场会踩。

**B9 事件表静默丢行。**
`event_parser.py:237` `dropna(subset=["declare_date"])` 直接丢日期不可解析的违规记录；`_read_export` 的 `SKIP_ROWS=2` 假定「英文代码行 + 中文标签行 + 单位行」固定三行表头，CSMAR 改版即静默错位。

### C. 文档与交付层（最容易被下一个人踩）

**C1 三份「权威文档」的数字一度停在 v0.2（2026-11-24 已修）。**
原状：`README.md`、`GUIDE.md`、`docs/team_handoff.md` 写 n=8,140、ρ=0.136、AUC 0.640、富集 1.22/1.87。现已改为 n=9,239、ρ=−0.021、AUC 0.802、富集 2.45/1.69，并把测试数从 130 提到 172。**这类文档只同步头条数字，细节仍以 `outputs/tables/` 为准**。

**C2 PDF 曾比 docx 旧一整个数据版本（v0.3 交付件已重打）。**
`outputs/manuscript/Group12A2_Final_EN_v0.3.pdf` 与 `_v0.3.docx` 同日生成（22 页，正文 15 页 + 附录 7 页），PDF 文本已逐段比对与 docx 一致。**旧的 `Group12A2_Final_EN.pdf` / `_CN.pdf`（11-11 17:45）仍是 8,140 口径，已声明不再维护**，不要拿它们交付。

**C3 演示稿停在 11-11。**
`outputs/slides/Group12A2_Deck.pptx`（11-11 04:29）没有 §5.7 外部检验、没有 §5.8，结论页仍写 "MD&A text features add none"（在 v0.3 语境下这句话需要限定为「对 Beneish 式无监督排序无增量」）。

**C4 两个都叫 Final 的英文稿，编号体系不同。**

| 文件 | 页数 | 结构 | 用途 |
| --- | --- | --- | --- |
| `outputs/manuscript/Group12A2_Final_EN_v0.3.docx` + `.pdf` | **22 页**（15 正文 + 7 附录） | 137 段 / 10 表 / 8,274 词；正文 15 页 + 附录（A1、B1–B6） | **唯一在维护的交付件**（2026-11-24） |
| `outputs/manuscript/Group12A2_Final_EN.docx` | 23 页 | 145 段 / 7 表 / 6 图；§5.6 两版对比、§5.7 外部检验、**§5.8 稳健性 + 表 5.7** | 完整母本（历史，已含 v0.3 文字修正但不再重打） |
| `11.23base/Group12A2_Final_EN_corrected_compact.docx` | **15 页** | 117 段 → 现 132 段 / 3 表 / 3 图；表 5.1/5.3 移入附录 | 稿源（补丁脚本以它为准） |
| `11.23base/..._compact_appendix.docx` | **7 页** | 现含表 A1、B1–B6 | 稿源附录 |

**投哪个是开放问题**（见 §9 第 4 条）。若投 compact，附录 4 页要不要计入页数，需要问教授。

**C5 页数不是靠「把表挪进附录」降下来的。**
移表不减页（附录仍占页）。22 → 15 页的真正来源：删 3 图（图 5.1/5.4/5.6）、合并段落、正文行距 1.45 → 1.2、图高上限 2.3 in。`patch_manuscript_docx.py` 为此新增 `TABLE_REMAP`、`FIGURE_REMAP`、`slim_compact()`、`split_appendices()`、`tighten_typography()`。

**C6 中文稿出现过「张冠李戴」。**
旧中文结论段把「财务单独 ρ=0.136」挂到融合模型上；v0.3 已按英文重写（段 78/79），并清除 ρ=0.136、0.103、富集 1.22、SHAP 65.9%/34.1%、重叠 0.828 等旧值。改中文稿时务必两边同步。

**C7 参考文献 [22]/[24] 的标题曾写错。**
词典头部注释把姚加权 2021 误写成《中国上市公司文本信息披露的情感分析》，正确是《语调、情绪及市场影响：基于金融情绪词典》。已查证补全，别再改回去。

**C8 测试数量一路漂移：39 → 77 → 85 → 114 → 126 → 130 → 172。**
README 里已改。以 `pytest -q` 实际输出为准（当前 **172 passed**，约 30 s）。

**C9 `symbol` 以整数入库。**
CSV 里 `000008` 读成 `8`；不经 `dtype=str` + `zfill(6)` 就会丢前导零，join 全错。审计报告把它列为「唯一瑕疵（非违规）」。

**C10 M-Score 尾部极端值（原「000820 = 2,023.3」已不存在）。**
现表 `anomaly_scores.csv` 中 000820 的 2021 年 M-Score 为 **81.215**（legacy/calibrated 双双报警），2022 年为 **−2.107**（不报警）；2,023.3 那个值是修复前的行错位产物，已随 v0.3 数据修复消失。全样本 M-Score 区间 **−387.06 ～ 9,182.95**，33 个 firm-year（0.4%）|M|>20——因为 M-Score 本身不做 winsorise，而九个特征在 1%/99% 分位被截尾。引用时按「未截尾、极端值来自分母接近 0 的困境公司」解释，不能当结论。

---

## 8. 交付物清单（当前磁盘状态）

| 类别 | 文件 | 状态 |
| --- | --- | --- |
| **英文论文（唯一在维护）** | `outputs/manuscript/Group12A2_Final_EN_v0.3.docx`（137 段 / 10 表 / 8,274 词） + `.pdf`（22 页） | **最新（11-24），正文 15 页 + 附录 7 页** |
| 英文论文（完整母本） | `outputs/manuscript/Group12A2_Final_EN.docx`（145 段 / 7 表 / 7,612 词） | docx 含 v0.3 文字修正；PDF 旧（11-11），不再维护 |
| 英文论文（精简稿源） | `11.23base/Group12A2_Final_EN_corrected_compact.docx` + `..._appendix.docx` | 15 页 + 7 页；补丁脚本的输入 |
| 中文论文 | `outputs/manuscript/Group12A2_Final_CN.docx`（87 段 / 7 表） | docx 新，PDF 旧（不在 v0.3 维护范围） |
| 系统实现报告 | `outputs/manuscript/Group12A2_System_Implementation_{EN,CN}.docx/.pdf` | 11-09/11-10，未受 v0.3 影响 |
| 结果工作簿 | `outputs/Group12A2_Results_Summary.xlsx` / `_EN.xlsx`（各 7 表 + 6 原生图） | 11-23，**内含 8,140/3,265 旧口径，不再维护** |
| 演示稿 | `outputs/slides/Group12A2_Deck.pptx/.pdf`（12 页） | 11-11，过期，不再维护 |
| 结果表 | `outputs/tables/*.csv`（10 个基础 + 6 个本轮新增） | 11-24，最新 |
| 图 | `outputs/figures/*.png`（8 张） | 11-23 |
| 报告 | `outputs/reports/*.md`（实验摘要、描述统计、叙事、数据审计、v0.1→v0.2 差异、AE 配置） | 混合日期 |
| 分支研究 | `outputs/branches/`（换结果变量 7 条路线、Beneish 八分量、问询函爬虫规格、事件检验、严格时序与词典对照） | 11-23 / 11-24 |
| 修订总册 | `docs/revision/v0.3_consistency_revision.md` | 11-24，36 条登记 + 结论边界 + 证据索引 |

> 结果工作簿由 `build_results_excel.py` 在运行时从 `outputs/tables/` 现算，所以**重跑一次即可对齐**：
> `& ".venv\Scripts\python.exe" scripts\build_results_excel.py` 与 `... --lang en`。

---

## 9. 已知未解决项与风险（接手第一周该处理的顺序）

1. **旧 PDF 未重发（但已不再需要）**：v0.3 已自带 `outputs/manuscript/Group12A2_Final_EN_v0.3.pdf`（22 页，与 docx 逐段一致）。旧的 `Group12A2_Final_EN.pdf` / `_CN.pdf` 仍是 11-11 的 8,140 口径，**已标注不再维护**，任何场合都不要拿它们交付。
2. **演示稿过期**，结论句与新口径冲突（"MD&A text features add none" 需限定为「对 Beneish 式无监督排序无增量」）。按用户决策本轮不重建；若要用，改 `build_slides.py` 的 RQ1 页与结论页并补外部检验两页。
3. ~~README / GUIDE / team_handoff 的数字过期~~ —— **2026-11-24 已同步**到 n=9,239 / ρ=−0.021 / AUC 0.802 / 富集 2.45、1.69，测试数 172。
4. **提交版已定**：只用 `outputs/manuscript/Group12A2_Final_EN_v0.3.docx`（+ PDF）。23 页完整母本与 15 页精简稿源仅作内部比对。仍需教授的只是「附录 7 页是否计入 12–15 页限制」这一句话。
5. **`symbol` 整数存储**。动作：所有读取点统一 `dtype={"symbol": str}` + `zfill(6)`；或在 `run_01` 落盘时就写成 6 位字符串。
6. **DEPI 恒为 1.0**、**AE 瓶颈 8 vs 9 维**、**bootstrap 400 vs 1000**、**top-decile 两套定义**：都是需要在论文「局限」里点明、或在下一版修掉的。
7. **小组成员 4 人 vs 评分要求「最多 3 人」**（`GUIDE.md:311`、`docs/manuscript_assembly_checklist.md` 风险条）——需要与教授确认，不是技术问题。
8. **磁盘冗余**：`data/raw/cninfo/2024`（5,114 份 / 17.2 GB）与清单外代码的 PDF 不在样本内；`outputs/.tmp/*.univer` 与根目录 `.univer` 约 472 MB 被 Univer 服务占用，需重启 DSH 后 `run_15_cleanup_workspace.py --apply`。

---

## 10. 复现手册（干净机器）

```powershell
# 0) 环境（Python 3.12；项目实测 3.12.14）
python -m venv .venv
& ".venv\Scripts\python.exe" -m pip install -r requirements.txt
& ".venv\Scripts\python.exe" -m pytest -q        # 172 passed

# 1) 数据落位（data/ 不在 git 里）
#    data/raw/csmar/{FS_Combas,FS_Comins,FS_Comscfd,STK_LISTEDCOINFOANL}.xlsx
#    data/raw/csmar_events/{FIN_Audit,STK_Violation_Main}.xlsx
#    data/external/dictionaries/（姚加权词表、jieba 词典、BSE 对照）

# 2) 样本 → 财务中间表 → 文本 → 特征表
& ".venv\Scripts\python.exe" scripts\run_01_sample.py
& ".venv\Scripts\python.exe" scripts\run_03_build_finance_intermediate.py
& ".venv\Scripts\python.exe" scripts\run_02_download_annual_reports.py --year 2021   # 三路，各约 1–1.5 h
& ".venv\Scripts\python.exe" scripts\run_04_audit_downloads.py
& ".venv\Scripts\python.exe" scripts\run_05b_recompute_text_features.py --workers 8 # 约 2–3 h
& ".venv\Scripts\python.exe" scripts\run_06_build_feature_table.py

# 3) 建模与外部检验
& ".venv\Scripts\python.exe" scripts\run_07_experiment.py
& ".venv\Scripts\python.exe" scripts\run_03b_build_event_table.py
& ".venv\Scripts\python.exe" scripts\run_07b_event_models.py --boot 400
& ".venv\Scripts\python.exe" scripts\run_11_descriptives.py
& ".venv\Scripts\python.exe" scripts\run_12_narrate_results.py

# 4) 论文与交付
& ".venv\Scripts\python.exe" scripts\build_section5.py --markdown --markdown-cn --docx --docx-cn
& ".venv\Scripts\python.exe" scripts\build_results_excel.py            # 中文
& ".venv\Scripts\python.exe" scripts\build_results_excel.py --lang en  # 英文
& ".venv\Scripts\python.exe" scripts\build_slides.py
& ".venv\Scripts\python.exe" scripts\run_16_verify_manuscript.py       # 自检
```

耗时参考：全量文本提取 2–3 小时（8 进程）；测试 21 秒；建模 1–2 分钟；论文重建 1 分钟。所有随机组件固定 `SEED=42`，同数据应逐位可复现（浮点显示位数除外）。

---

## 11. 如果还要继续做研究

已有分支结论（`outputs/branches/`，不要重复劳动）：

| 分支 | 结论 | 成本 |
| --- | --- | --- |
| 换结果变量七条路线 | t+1 年报问询函首选（信号强、时点干净）；非标审计意见兜底；重述/处罚备选；内控否定与业绩预告修正排除 | 问询函需自建爬虫 |
| Beneish 八分量探针 | 文本对任一分量 \|ρ\| ≤ 0.064 → 「基准太粗」被排除 | 已完成 |
| 问询函爬虫 | 深交所接口最干净；沪市靠巨潮补；4.5–5 人日 | 中 |
| 真实事件检验 | 已升格为 §5.7，不必重做 | 已完成 |

下一步最值得做的三件事（按性价比）：① 用 `mda_text_{年}.jsonl` 缓存换 BERT/FinBERT 句向量（免重提 PDF，只重跑特征与建模）；② 把监督模型做实（现在是 OOF AUC 对比，非端到端筛查器）；③ 若允许改定位，做问询函前瞻检验。

---

## 12. 关键路径速查

```
研究问题 → docs/manuscript_methodology_section.md
方法实现 → docs/manuscript_implementation_section.md
结果叙事 → outputs/reports/results_narrative.md（英文段落，自动填数）
头条数字 → outputs/tables/model_metrics.csv / topk_metrics.csv / event_ranking_metrics.csv
数据字典 → docs/feature_dictionary.md
文件地图 → docs/project_layout.md
复现步骤 → docs/reproducibility_guide.md
变更理由 → CHANGELOG.md（按日期从新到旧）
数据可信度 → outputs/reports/data_audit_2026-11-23.md（49/49）
人工核对记录 → 11.23base/核对报告-2026-11-23.md
```

---

## 13. 术语表

| 术语 | 含义 |
| --- | --- |
| firm-year | 公司-年度观测，本文一个「公司×一个财年」 |
| 完整案例 | 9 个特征 + M-Score 全部非空，10,172 → 9,239 |
| legacy 基准 | `M-Score > −1.78`（Beneish 1999 原阈值） |
| calibrated 基准 | 样本自身 M-Score 前 10% 分位（阈值 −1.4366） |
| top-1 | 融合 IF 分数最高的公司（当前 600870） |
| 富集率 | 名单内事件率 ÷ 全样本事件率 |
| 非标意见 | 保留 / 无法表示 / 否定（窄口径）；宽口径另加带强调事项段 |
| t+1 违规 | 把 `declare_year` 减 1 对齐到年报年，保证严格前瞻 |
| OOF AUC | 分组 5 折交叉验证的折外预测 AUC |
| ΔAUC | 融合特征集减财务特征集的配对 AUC 差 |

---

## 14. 一句话总结（给下一个 AI 的开场白）

> 这是一份 FinTech 课程论文仓库：用 9,239 个 A 股制造业公司-年度样本，把 6 个财务比率与 3 个 MD&A 文本特征喂给 Isolation Forest / 自编码器，先用 Beneish M-Score 做代理基准、再用 CSMAR 真实监管事件做外部检验。结论是「财务弱、文本无增量、自编码器未复现，但真实事件上财务排序 AUC 0.80，而代理基准只有 0.24」——一篇诚实的阴性结果 + 测量批判论文。所有数字由 `outputs/tables/` 现算，130 个测试全绿；坑主要在数据合并、科目取列、以及文档/PDF/PPT 三类交付物滞后于代码。
