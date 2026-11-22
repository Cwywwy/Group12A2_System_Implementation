# Group12A2 · 财务披露风险筛查（文本-财务特征融合 + 可解释异常检测）

> Screening Financial Disclosure Risk through Textual-Financial Feature Fusion and Explainable Anomaly Detection:
> Evidence from Chinese A-share Manufacturing Firms, 2021–2023

Group 12A2《Introduction to FinTech》课程论文（Option 2：Research Manuscript）的可复现研究管线与全部交付物。

以中国 A 股制造业上市公司 **2021–2023** 年为样本（基期 2020），融合 6 个财务特征与 3 个 MD&A 文本特征，
用 Isolation Forest（主模型）与 autoencoder（稳健排名）做无监督异常检测，以 SHAP 提供全局与局部解释，
先用 Beneish M-Score 作代理基准，再用 **CSMAR 真实监管事件（非标审计意见、违规处理）** 做外部检验。
论文正文中的全部数字均由管线脚本产出，可逐层复现。

## 从哪里开始

| 你想做什么 · What you want | 打开 · Open |
| --- | --- |
| 找某个文件在哪 · find a file | [`docs/project_layout.md`](docs/project_layout.md)（项目文件地图：数据源 / 第一版 / 第二版 / 各分支 / 定稿） |
| 查某个结果或命令 · look up a result or command | [`GUIDE.md`](GUIDE.md)（中英双语查阅指南） |
| 从零复现 · reproduce | [`docs/reproducibility_guide.md`](docs/reproducibility_guide.md) |
| 看还差什么 · outstanding work | [`docs/team_handoff.md`](docs/team_handoff.md) |
| 看改了什么 · change history | [`CHANGELOG.md`](CHANGELOG.md) |

## 仓库内容

- **定稿**：`outputs/manuscript/`（`Group12A2_Final_EN` / `_CN` 的 docx 与 pdf，英文 15 页 / 中文 9 页；`source/` 是不含表格的母版）
- **结果汇总工作簿**：`outputs/Group12A2_Results_Summary.xlsx`（中文）与 [`outputs/Group12A2_Results_Summary_EN.xlsx`](outputs/Group12A2_Results_Summary_EN.xlsx)（英文）——各 7 张表 + 6 张原生 Excel 图表，数字与论文 §5 同源，由 `scripts/build_results_excel.py --lang cn|en` 生成
- **演示稿**：`outputs/slides/`（`Group12A2_Deck.pptx` / `.pdf`，12 页）
- **当前结果（第二版）**：`outputs/tables/`、`outputs/figures/`、`outputs/reports/`
- **各分支调研**：`outputs/branches/`（换结果变量可行性、Beneish 分量探针、问询函爬虫规格、真实事件检验）
- **第一版归档**：`outputs/archive_v0.1/`（结果）与 `data/archive_v0.1/`（数据），代码见 `git tag v0.1-baseline`
- **数据源**：`data/raw/`（巨潮年报 PDF、CSMAR 三表、CSMAR 事件表，不入库）
- **源码**：`src/`（数据接入、特征工程、模型、评估、报告）
- **编排脚本**：`scripts/`（`run_00`–`run_14` 分阶段入口 + `run_99_full_pipeline.py` 一键流程 + `build_section5.py` / `build_slides.py` / `build_results_excel.py` 组装）
- **测试**：`tests/`（126 个 pytest 用例）
- **课程材料**：`course_materials/`（评分要求、原始 Univer 文档、版权声明）

## 复现

详见 [`docs/reproducibility_guide.md`](docs/reproducibility_guide.md)。简要步骤：

```powershell
python -m venv .venv
& ".venv\Scripts\python.exe" -m pip install -r requirements.txt
& ".venv\Scripts\python.exe" -m pytest -q
```

## 数据说明

原始数据（CSMAR 三表与事件表、巨潮年报 PDF、巨潮公司信息表）体量大且受授权限制，**未纳入本仓库**（`data/` 目录）。
数据获取与目录结构见 `docs/csmar_download_guide.md`、`docs/csmar_event_data_guide.md` 与 `docs/cninfo_download_guide.md`。

## 成员

Group 12A2 · Introduction to FinTech · 2026

## English

Reproducible research pipeline and all deliverables for the Group 12A2 *Introduction to FinTech* course paper
(Option 2: Research Manuscript): *Screening Financial Disclosure Risk through Textual-Financial Feature Fusion
and Explainable Anomaly Detection — Evidence from Chinese A-share Manufacturing Firms, 2021–2023*.

| Deliverable · English version | Location |
| --- | --- |
| Final manuscript (English, 15 pages, Table 5.1–5.6) | [`outputs/manuscript/Group12A2_Final_EN.pdf`](outputs/manuscript/Group12A2_Final_EN.pdf) / [`.docx`](outputs/manuscript/Group12A2_Final_EN.docx) |
| Final manuscript (Chinese, 9 pages) | [`outputs/manuscript/Group12A2_Final_CN.pdf`](outputs/manuscript/Group12A2_Final_CN.pdf) / [`.docx`](outputs/manuscript/Group12A2_Final_CN.docx) |
| Results summary workbook (English, 7 sheets + 6 native charts) | [`outputs/Group12A2_Results_Summary_EN.xlsx`](outputs/Group12A2_Results_Summary_EN.xlsx) |
| Results summary workbook (Chinese, 7 sheets + 6 native charts) | [`outputs/Group12A2_Results_Summary.xlsx`](outputs/Group12A2_Results_Summary.xlsx) |
| Twelve-slide deck | [`outputs/slides/Group12A2_Deck.pdf`](outputs/slides/Group12A2_Deck.pdf) / [`.pptx`](outputs/slides/Group12A2_Deck.pptx) |
| Bilingual reference guide | [`GUIDE.md`](GUIDE.md) |
| Reproduction guide | [`docs/reproducibility_guide.md`](docs/reproducibility_guide.md) |

All headline numbers are computed by the pipeline scripts from the released tables under `outputs/tables/`
— the manuscript (§5), the deck and both workbooks share the same single source of truth.

```powershell
# Regenerate the result-summary workbooks (Chinese / English)
& ".venv\Scripts\python.exe" scripts\build_results_excel.py
& ".venv\Scripts\python.exe" scripts\build_results_excel.py --lang en
```

Raw data (CSMAR tables, CNINFO annual-report PDFs) is large and licence-restricted, so the `data/` directory
is not part of this repository; see `docs/csmar_download_guide.md`, `docs/csmar_event_data_guide.md` and
`docs/cninfo_download_guide.md`.
