# 查阅指南 · GUIDE

> 本文件只解决一个问题：**我想找 X，它在哪里。**
> This file answers one question only: **where do I find X?**
>
> 面向组员、评审老师与后来接手的人。按「目标」检索即可，不必通读。
> Written for teammates, markers and anyone taking this repository over. Search by goal; no need to read it end to end.
>
> 项目 · Project：Group12A2 · Introduction to FinTech · 财务披露风险筛查（文本-财务特征融合 + 可解释异常检测）
> Screening Financial Disclosure Risk through Textual-Financial Feature Fusion and Explainable Anomaly Detection
>
> 维护 · Maintenance：内容变动时同步更新本文件与 [CHANGELOG.md](CHANGELOG.md) · Update this file and `CHANGELOG.md` together.
> 最后更新 · Last updated：2026-11-11

---

## 0. 一分钟速查 · One-minute lookup

| 你要什么 · You want | 直接打开 · Open |
| --- | --- |
| 论文成品（Word / PDF）· Final paper | `outputs/manuscript/` 下的 Final_EN / Final_CN |
| 实验结论（一页看完）· Headline results | [experiment_summary.md](outputs/reports/experiment_summary.md) |
| 从零复现的步骤 · Reproduction from scratch | [reproducibility_guide.md](docs/reproducibility_guide.md) |
| 现在还剩什么没做 · What is still outstanding | [team_handoff.md](docs/team_handoff.md) 第三节 / section 3 |
| 每份文件是干什么的 · What each file does | 本文件，继续往下看 · this file |

---

## 1. 按目标查 · Find by goal

### 1.1 看实验结果 · See the experiment results

| 我想看 · I want to see | 文件 · File | 说明 · Notes |
| --- | --- | --- |
| 结论汇总（ρ、富集率两张小表）· Summary tables | [experiment_summary.md](outputs/reports/experiment_summary.md) | **先看这个** · read this first |
| 各模型与 Beneish M-Score 的秩相关 · Spearman ρ | [model_metrics.csv](outputs/tables/model_metrics.csv) | 论文 §5 RQ1 |
| top-5/10/15% 的事件率与富集率 · Event and enrichment rates | [topk_metrics.csv](outputs/tables/topk_metrics.csv) | 论文 §5 RQ1 |
| 逐公司异常得分与排名 · Per-firm scores and ranks | [anomaly_scores.csv](outputs/tables/anomaly_scores.csv) | 查「某只股票排第几」· rank of a given stock |
| IF 与 AE 的排序重叠 · Ranking overlap | [ranking_overlap.csv](outputs/tables/ranking_overlap.csv) | 论文 §5 RQ3 |
| SHAP 全局 / 组贡献 / 单条解释 · SHAP outputs | `outputs/tables/shap_*.csv` | 论文 §5 RQ2 |
| 图（可直接插 Word / PPT）· Figures | `outputs/figures/*.png` | 共 8 张 · 8 files |
| 可直接粘贴的英文结果段 · Ready-to-paste English §5 | [results_narrative.md](outputs/reports/results_narrative.md) | RQ1–RQ3 自动填数 · auto-filled |
| 描述统计、样本覆盖、缺失 · Descriptives and coverage | [descriptives_summary.md](outputs/reports/descriptives_summary.md) | 论文 §4 |

**核心结论 · Headline results**（出处 · source：[experiment_summary.md](outputs/reports/experiment_summary.md)）：

有效样本 n = **8,140** firm-year（3,265 家公司，2021–2023）。Spearman ρ = if_finance **0.1357**、if_text −0.0293、
if_fused 0.1034、ae_fused 0.0092（p=0.409）；top-10% 富集率 = if_finance **1.2172**（样本校准口径 1.8673）、if_fused 1.1977（1.8428）；
SHAP 组贡献 财务 65.4% / 文本 34.6%。即：财务特征弱但显著，文本特征无增量，自编码器的稳健性未复现；
换用姚加权等 (2021) 全量词典后（词元命中密度为旧引导版的 8.3 倍）结论不变。

Valid sample n = **8,140** firm-years (3,265 firms, 2021–2023). Spearman ρ = if_finance **0.1357**, if_text −0.0293,
if_fused 0.1034, ae_fused 0.0092 (p = 0.409); top-10% enrichment = if_finance **1.2172** (recalibrated 1.8673), if_fused 1.1977 (1.8428);
SHAP group contribution finance 65.4% / text 34.6%. In short: the financial signal is weak but significant, text features add nothing,
the autoencoder's robustness does not replicate, and replacing the lexicon with the full Yao et al. (2021) list (8.3x denser matches)
does not change the conclusion.

### 1.2 看数据 · See the data

| 我想要 · I want | 位置 · Location |
| --- | --- |
| 直接喂模型的**最终特征表** · Final modelling table | [feature_table.csv](data/processed/feature_table.csv)（10,172 行 × 20 列） |
| 中间层（追溯某个特征怎么算）· Intermediate layer | `data/interim/`：finance_intermediate + text_features_20xx |
| 原始数据（从头跑）· Raw data | `data/raw/csmar/*.xlsx`、`data/raw/cninfo/{2021,2022,2023}/*.pdf` |
| 样本框怎么选的 · Sample frame | `data/processed/manufacturing_sample_frame.csv` |
| 下载是否完整 · Download audit | `data/processed/download_audit.csv`（ok 10,051 / missing 121） |
| 数据质量标记 · QC flags | `data/processed/qc_summary.csv`、`qc_issues.csv` |
| 每个特征的公式与来源字段 · Feature formulas | [feature_dictionary.md](docs/feature_dictionary.md) |
| 数据怎么下载的 · How the data was obtained | [csmar_download_guide.md](docs/csmar_download_guide.md)、[cninfo_download_guide.md](docs/cninfo_download_guide.md) |

### 1.3 重跑 · Re-run

```powershell
# 只重跑建模 + 出图 + 摘要（最快）· Modelling, figures and summary only (fastest)
& ".venv\Scripts\python.exe" "scripts\run_07_experiment.py"

# 只重跑统计与结果叙事 · Descriptives and result narrative only
& ".venv\Scripts\python.exe" "scripts\run_11_descriptives.py"
& ".venv\Scripts\python.exe" "scripts\run_12_narrate_results.py"

# 全流程（数据齐备时）· Full pipeline once the data is in place
& ".venv\Scripts\python.exe" "scripts\run_99_full_pipeline.py"

# 跑测试 · Run the test suite
& ".venv\Scripts\python.exe" -m pytest -q
```

每个脚本负责哪一段，见第 5 节 · Which script owns which stage: see section 5.

### 1.4 看文字材料 · See the written material

| 我要 · I want | 文件 · File |
| --- | --- |
| 论文英文 §3 方法 · §3 Methodology (EN) | [manuscript_methodology_section.md](docs/manuscript_methodology_section.md) |
| 论文英文 §4 实现 · §4 Implementation (EN) | [manuscript_implementation_section.md](docs/manuscript_implementation_section.md) |
| 论文英文 §5 实验 · §5 Experiment (EN) | [manuscript_experiment_section.md](docs/manuscript_experiment_section.md) |
| 论文英文 §6 结论 · §6 Conclusion (EN) | [manuscript_conclusion_section.md](docs/manuscript_conclusion_section.md) |
| 中文稿全文 · Full Chinese draft | [manuscript_chinese_draft.md](docs/manuscript_chinese_draft.md) |
| 逐节对照 + 剩余工作 · Section-by-section checklist | [manuscript_assembly_checklist.md](docs/manuscript_assembly_checklist.md) |
| 演示文案（12 页讲稿）· Slide script | [slides_deck_draft.md](docs/slides_deck_draft.md) |
| 演示视觉规范与精确文案 · Slide spec | [slides_deck_spec.md](docs/slides_deck_spec.md) |
| 演示大纲 · Slide outline | [slides_outline.md](docs/slides_outline.md) |
| 前两页草稿（SVG）· First two pages | `docs/slides/page_01.svg`、`page_02.svg` |
| 小组分工与交接 · Roles and handover | [team_handoff.md](docs/team_handoff.md) |
| 管线计划书与模块划分 · Pipeline plan | [course_paper_pipeline_plan.md](.github/plans/course_paper_pipeline_plan.md) |
| 为什么代码这样改 · Why the code changed | [CHANGELOG.md](CHANGELOG.md) |

---

## 2. 顶层目录地图 · Top-level map

| 路径 · Path | 里面是什么 · Contents | 能否分享 · Shareable |
| --- | --- | --- |
| `.github/plans/` | 管线计划书（模块划分、阶段拆分）· Pipeline plan | 可以 · yes |
| `.venv/` | Python 3.12 虚拟环境 · virtual environment | **不要**打包 · **do not** ship |
| `data/` | 全部数据，约 41 GB · all data, c. 41 GB | **不可外传** · **not** to be redistributed（CSMAR / 巨潮授权） |
| `docs/` | 17 份文档：指南、字典、手稿分节、slides、交接 · 17 documents | 可以 · yes |
| `outputs/` | 全部结果产物：表、图、报告、论文 · all deliverables | 可以 · yes |
| `scripts/` | 分阶段入口脚本 `run_00`–`run_99` · stage entry points | 可以 · yes |
| `src/` | 源码包（采集 / 特征 / 模型 / 评估 / 报告）· source package | 可以 · yes |
| `tests/` | 77 个 pytest 用例 + 历史报告 · 77 tests and past reports | 可以 · yes |
| `.pytest_cache/` | 测试缓存 · test cache | 可删 · deletable |
| 根目录散落文件 · loose root files | 课程材料、论文正文、样本框原始表 · course material, paper, source table | 见第 7 节 · see section 7 |

**根目录散落文件清单 · Loose root files**

| 文件 · File | 作用 · Purpose |
| --- | --- |
| `Group12A2 Screening Financial Disclosure Risk through Textual-Financial Feature Fusion and Explainable Anomaly Detection Evidence from Chinese A-share Manufacturing Firms, 2021–2023.docx` | README 指定的**论文正文** · the paper text as designated by README |
| `Grading and Report Requirement for FinTech 2026-Modified.docx` | 教授给的评分与报告要求 · course grading and report requirements |
| `Financial_Disclosure_Quality_Assessment_English_Outline(1).docx` | 题目英文提纲 / 要求 · English assignment outline |
| `grading_rubric.univer` | 评分细则（Univer 格式）· grading rubric |
| `course_paper_materials.univer` | 课程资料合集（Univer 格式）· course material bundle |
| `Copyright notice.pdf` | CSMAR 与巨潮数据的版权声明（演示附录要用）· data licence notice |
| `STK_LISTEDCOINFOANL.xlsx` + `STK_LISTEDCOINFOANL[DES][xlsx].txt` | CSMAR 上市公司基本信息表（选样框输入）· listed-company table; the `.txt` is the field description |
| `README.md` | 项目总览与复现三步 · project overview |
| `CHANGELOG.md` | 按日期分组的变更日志 · dated change log |
| `GUIDE.md` | 本文件 · this file |
| `requirements.txt` / `pytest.ini` | 依赖固定版本 / 测试配置 · pinned dependencies / test configuration |

---

## 3. `data/` 的三层结构 · The three data layers

按「原样下载 → 标准化中间表 → 建模特征表」三层组织，**每层都可单独核对**，这是复现的关键。
Organised as raw download → standardised intermediate → modelling feature table. **Each layer can be checked on its own**, which is what makes reproduction possible.

| 层 · Layer | 路径 · Path | 内容 · Contents | 谁生产 · Produced by |
| --- | --- | --- | --- |
| 原始 · raw | `data/raw/csmar/` | `FS_Combas.xlsx` 资产负债表 135 MB、`FS_Comins.xlsx` 利润表 64 MB、`FS_Comscfd.xlsx` 现金流量表 62 MB，2020–2023 合并口径 · balance sheet, income statement, cash flow, consolidated basis | 组员手动下载 · manual download |
| 原始 · raw | `data/raw/cninfo/{2021,2022,2023}/` | 约 1 万份年报 PDF，命名 `代码_年份_annual_report.pdf` · c. 10,000 annual-report PDFs | `run_02` 自动下载 · automated |
| 外部 · external | `data/external/` | `bse_920_code_mapping.csv` 北交所新老代码对照 248 行 · BSE code mapping | 公开网页整理 · public web |
| 中间 · interim | `data/interim/` | `finance_intermediate.csv`（三表标准化，20,103 行）、`text_features_{2021,2022,2023}.csv`、`demo_feature_table.csv`（240 行演示用） | `run_03_build_finance_intermediate` / `run_05` / `run_03_make_demo_data` |
| 特征 · features | `data/processed/feature_table.csv` | 最终建模表 10,172 行 × 20 列：样本框 + 6 金融特征 + M-Score + 3 文本特征 + 质量标记 · final modelling table | `run_06` |
| 过程 · process | `data/processed/*.csv` | 样本框、下载清单、审计、QC、下载与修复日志 · frame, checklist, audit, QC and logs | `run_01`/`04`/`08`/`09`/`10` |

> 中间表与特征表行数不同是正常的：10,172 是全部 firm-year，8,140 是 9 个特征 + M-Score 全部齐全的子集——论文报的是后者。
> The row counts differ by design: 10,172 is every firm-year; 8,140 is the subset with all 9 features plus M-Score present. The paper reports the latter.

---

## 4. `outputs/` 产物清单 · Output inventory

### 4.1 `outputs/manuscript/` 交付物 · Deliverables

| 文件 · File | 内容 · Contents |
| --- | --- |
| `Group12A2_Final_EN.docx` / `.pdf` | 英文终稿（含 Table 5.1–5.3，13 页、24 条参考文献）· final English paper with the three result tables, 13 pages |
| `Group12A2_Final_CN.docx` / `.pdf` | 中文终稿（含三张表）· final Chinese paper with the same tables |
| `source/Group12A2_Final_EN.docx`、`source/Group12A2_Final_CN.docx` | 不含表格的母版，重排 §5 时脚本从母版读 · pre-table masters used as the patch input |
| `Group12A2_System_Implementation_EN.docx` / `.pdf` | 系统实现报告（11-10 已交）· system implementation report |
| `Group12A2_System_Implementation_CN.docx` / `.pdf` | 同上中文版 · the same, in Chinese |

### 4.2 `outputs/tables/` 表 · Tables（7 张 · 7 files）

`model_metrics.csv`（Spearman ρ）、`topk_metrics.csv`（top-k 事件率 / 富集 · event and enrichment）、
`anomaly_scores.csv`（逐公司得分 · per-firm scores）、`ranking_overlap.csv`（RQ3）、`shap_global.csv`、
`shap_group_contributions.csv`、`shap_local_top1.csv`（RQ2）。

### 4.3 `outputs/figures/` 图 · Figures（8 张 · 8 files）

`score_distribution_if_finance.png`、`score_distribution_if_text.png`、`score_distribution_if_fused.png`、
`score_distribution_ae_fused.png`、`topk_enrichment.png`、`group_contributions.png`、`shap_importance.png`、`ranking_overlap.png`。

### 4.4 `outputs/reports/` 报告 · Reports（5 份 · 5 files）

`experiment_summary.md`（结论摘要 · headline results）、`descriptives_summary.md`（描述统计 · descriptives）、
`results_narrative.md`（英文结果段落 · English results text）、`pipeline_runbook.md`（全流程执行记录 · run log）、
`autoencoder_config.json`（AE 超参存档 · autoencoder hyper-parameters）。

### 4.5 `outputs/slides/` 演示稿 · Presentation

`Group12A2_Deck.pptx` / `.pdf`：12 页 16:9 演示稿，数字由 `scripts/build_slides.py` 从 `outputs/tables/` 现算 · twelve-slide deck generated from the released tables.

### 4.6 `outputs/slides_preview/` 演示预览 · Slide previews

`page-01.png`、`page-02.png`、`contact-slide.png`。

---

## 5. `scripts/` 阶段对照 · Stage map

| 脚本 · Script | 作用 · Purpose | 产出 · Output |
| --- | --- | --- |
| `run_00_env_check.py` | 环境就绪探针（14 项输入）· readiness probe | 终端输出 · terminal |
| `run_01_sample.py` | 生成样本框与下载清单 · build sample frame and checklist | `data/processed/manufacturing_sample_frame.csv` |
| `run_02_download_annual_reports.py` | 巨潮年报 PDF 批量下载（断点续传）· batch download, resumable | `data/raw/cninfo/{年}/*.pdf` |
| `run_03_build_finance_intermediate.py` | CSMAR 三表 → 金融中间表 · three statements → finance table | `data/interim/finance_intermediate.csv` |
| `run_03_make_demo_data.py` | 生成 240 行演示数据（冒烟用）· demo data for smoke tests | `data/interim/demo_feature_table.csv` |
| `run_04_audit_downloads.py` | 下载审计（缺失 / 过小 / 年份错位）· download audit | `data/processed/download_audit.csv` |
| `run_05_extract_mda_features.py` | MD&A 文本特征提取（增量、可续跑）· MD&A features, resumable | `data/interim/text_features_{年}.csv` |
| `run_06_build_feature_table.py` | 合成最终特征表 · assemble the feature table | `data/processed/feature_table.csv` |
| `run_07_experiment.py` | 建模 + 评估 + 出图 + 摘要 · modelling and evaluation | `outputs/tables/`、`figures/`、`reports/` |
| `run_08_qc_report.py` | 数据质量标记与汇总 · quality flags | `data/processed/qc_summary.csv`、`qc_issues.csv` |
| `run_09_repair_downloads.py` | 按审计定向重下（默认 dry-run）· targeted re-download | `data/processed/repair_log_*.csv` |
| `run_10_bse_legacy_download.py` | 北交所旧代码补下 · BSE legacy-code download | 同上 · as above |
| `run_11_descriptives.py` | 描述统计与样本覆盖 · descriptives | `outputs/reports/descriptives_summary.md` |
| `run_12_narrate_results.py` | 读表生成英文结果段 · results narrative | `outputs/reports/results_narrative.md` |
| `run_13_build_chinese_docx.py` | 中文 Markdown → Word · Markdown to Word | `outputs/manuscript/Group12A2_Final_CN.docx` |
| `run_05b_recompute_text_features.py` | 换词典后全量重提取（8 进程并行）· full re-extraction | `data/interim/text_features_{年}.csv` |
| `run_05c_lexicon_density.py` | 新旧词表命中密度对照 · lexicon density check | `outputs/tables/lexicon_density.csv` |
| `compare_runs.py` | 两次运行的指标差异对比 · diff two result runs | 控制台报告 · console report |
| `analyze_branch_beneish_components.py` | 把 M-Score 拆成八个分量，逐分量查文本是否有信号 · branch probe per Beneish component | `outputs/tables/branch_component_correlations.csv` |
| `build_section5.py` | 由表重写 §5 并把三张表排进 Word · rewrite §5 and typeset tables | `docs/manuscript_experiment_section.md`、Word 终稿 |
| `build_slides.py` | 由表生成 12 页演示稿 · build the twelve-slide deck | `outputs/slides/Group12A2_Deck.pptx` / `.pdf` |
| `run_99_full_pipeline.py` | 一键全流程（`--stage` / `--skip-05`）· full pipeline | 全部 · all |
| `scripts/archive/` | 历史一次性脚本（回填数字、转 docx、校验）· one-off scripts | — |

`src/` 的分工 · What lives in `src/`：`config.py`（超参与 `SEED=42` · hyper-parameters and seed）、`pipeline.py`（主流程 · main flow）、
`data_ingestion/`、`features/`、`models/`、`evaluation/`、`reporting/`。

---

## 6. 常用命令 · Common commands

```powershell
# 测试（当前 77 个用例）· Test suite (77 cases)
& ".venv\Scripts\python.exe" -m pytest -q

# 环境与数据就绪检查 · Readiness check
& ".venv\Scripts\python.exe" "scripts\run_00_env_check.py"

# 重建特征表（不动原始数据）· Rebuild the feature table
& ".venv\Scripts\python.exe" "scripts\run_06_build_feature_table.py"

# 重跑实验 · Re-run the experiment
& ".venv\Scripts\python.exe" "scripts\run_07_experiment.py"
```

---

## 7. 五个坑（先读再动手）· Five pitfalls（read before you touch anything）

1. **`data/`、`.venv/`、`*.univer`、`STK_*`、根目录课程要求 docx 都被 `.gitignore` 排除。**
   别人 `git clone` 拿到的仓库**没有数据、没有课程材料**，交接时必须单独说明数据获取方式，不要以为 clone 下来就齐了。
   `data/`, `.venv/`, `*.univer`, `STK_*` and the course-requirement docx in the root are all ignored by Git.
   A fresh clone therefore has **no data and no course material**; explain how to obtain the data during handover.

2. **两个 `run_03_*.py` 不是同一个阶段。** `run_03_build_finance_intermediate.py` 是正式管线；
   `run_03_make_demo_data.py` 只造 240 行演示数据做冒烟，**别把它的输出当正式结果**。
   The two `run_03` scripts are different stages. `run_03_build_finance_intermediate.py` is the real pipeline;
   `run_03_make_demo_data.py` only creates 240 demo rows for smoke tests — never quote it as a result.

3. **「终稿」有两个位置。** README 把根目录那个超长文件名的 `.docx` 定义为论文正文，
   `outputs/manuscript/Group12A2_Final_EN.docx` 也叫 Final。交作业前先确认以哪份为准。
   The "final" paper exists in two places: README designates the long-named root `.docx` as the paper text, while
   `outputs/manuscript/Group12A2_Final_EN.docx` is also called Final. Confirm which one is submitted before you hand in.

4. **README 写的「39 个测试」已过时**，实际 77 个（以 `CHANGELOG.md` 2026-11-10 记录与 `tests/reports/` 最新报告为准）。
   README's "39 tests" is out of date: there are 77. Trust the 2026-11-10 `CHANGELOG.md` entry and the latest report
   in `tests/reports/`.

5. **数据不可外传。** `data/raw/` 的 CSMAR 三表与巨潮年报 PDF 受授权限制，仅限本课程作业使用；
   演示或外发时只带 `outputs/` 与版权声明页 `Copyright notice.pdf`。
   The data must not be redistributed. The CSMAR statements and CNINFO annual reports in `data/raw/` are licensed for
   this coursework only; share `outputs/` and the `Copyright notice.pdf` page instead.

---

## 8. 待组内确认 · To be confirmed by the team

- 提交版是根目录论文 docx 还是 `outputs/manuscript/Group12A2_Final_EN.docx`（见第 7 节第 3 条）。
  Which file is the submitted version: the root paper docx or `outputs/manuscript/Group12A2_Final_EN.docx`（see 7, item 3）.
- 评分要求写「小组最多 3 人」，现署 4 人，需与教授确认（见 [manuscript_assembly_checklist.md](docs/manuscript_assembly_checklist.md) 风险条）。
  The requirements cap groups at three members; four are listed. Confirm with the instructor（see the risk note in
  `docs/manuscript_assembly_checklist.md`）.
- 演示结果页尚未誊到 PPT（[team_handoff.md](docs/team_handoff.md) 第三节，唯一剩余待办）。
  The results slide has not yet been moved into the deck — the only outstanding task（`docs/team_handoff.md`, section 3）.
