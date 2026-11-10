# Group12A2 · 财务披露风险筛查（文本-财务特征融合 + 可解释异常检测）

> Screening Financial Disclosure Risk through Textual-Financial Feature Fusion and Explainable Anomaly Detection: Evidence from Chinese A-share Manufacturing Firms

Group 12A2《Introduction to FinTech》课程论文（Option 2：Research Manuscript）的可复现研究管线与全部交付物。

以中国 A 股制造业上市公司 **2021–2023** 年为样本（基期 2020），融合 6 个财务特征与 3 个 MD&A 文本特征，
用 Isolation Forest（主模型）与 autoencoder（稳健排名）做无监督异常检测，并以 SHAP 提供全局与局部解释，
Beneish M-Score 作为评估基准。论文正文中的全部数字均由管线脚本产出，可逐层复现。

## 仓库内容

- **查阅指南**：[`GUIDE.md`](GUIDE.md)——想找什么、去哪里找（中英双语，先看这个）
- **论文正文**：`Group12A2 Screening Financial Disclosure Risk through Textual-Financial Feature Fusion and Explainable Anomaly Detection Evidence from Chinese A-share Manufacturing Firms, 2021–2023.docx`
- **系统实现报告**：`outputs/manuscript/Group12A2_System_Implementation_EN/CN.docx` 及 PDF
- **终稿**：`outputs/manuscript/Group12A2_Final_EN/CN.docx` 及 PDF
- **源码**：`src/`（数据接入、特征工程、模型、评估、报告，模块划分见 `.github/plans/course_paper_pipeline_plan.md`）
- **编排脚本**：`scripts/`（`run_01`–`run_13` 分阶段入口 + `run_99_full_pipeline.py` 一键流程）
- **测试**：`tests/`（77 个 pytest 用例）+ `tests/reports/`
- **结果产物**：`outputs/tables/`、`outputs/figures/`、`outputs/reports/`
- **文档**：`docs/`（复现指南、下载指引、特征字典、手稿分节等）

## 复现

详见 [`docs/reproducibility_guide.md`](docs/reproducibility_guide.md)。简要步骤：

```powershell
python -m venv .venv
& ".venv\Scripts\python.exe" -m pip install -r requirements.txt
& ".venv\Scripts\python.exe" -m pytest -q
```

## 数据说明

原始数据（CSMAR 三表、巨潮 cninfo 年报 PDF、巨潮公司信息表）体量大且受授权限制，**未纳入本仓库**（`data/` 目录）。
数据获取与目录结构见 `docs/csmar_download_guide.md` 与 `docs/cninfo_download_guide.md`。

## 成员

Group 12A2 · Introduction to FinTech · 2026
