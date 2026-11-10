# Group12A2 汇报幻灯片规格（12 页）

> 用途：为课程论文 Option 2 的 12 分钟展示生成可编辑 PowerPoint 骨架。最终数值页只使用真实 `run_07` 输出替换占位符；不得把当前 demo 数据当作正式结果。
>
> 状态：已落地。`scripts/build_slides.py` 按本规格生成 `outputs/slides/Group12A2_Deck.pptx`（12 页 16:9，同名 PDF 一并输出），第 7–9、12 页的数字全部由 `outputs/tables/` 现算，改版式请改脚本而不是手改 pptx。

## 全局视觉规范

| 项目 | 规范 |
| --- | --- |
| 页面 | 16:9，960 × 540 px |
| 主背景 | `#F7F9FC` |
| 深色文字 | `#102A43` |
| 主色 | `#0B5CAB` |
| 辅助色 | `#2D8C7A` |
| 强调色 | `#F59E0B` |
| 浅卡片 | `#FFFFFF`，边框 `#D9E2EC` |
| 字体 | Aptos / Arial；标题 28 pt，正文 15 pt，图表标签 11 pt |
| 页脚 | 左：`Group 12A2 · Intro FinTech`；右：页码；深蓝细线 |

## 页码与精确文案

| 页 | 核心信息 | 布局与文案 |
| --- | --- | --- |
| 1 | 题名与研究承诺 | 左 60% 标题，右侧三层流程装饰。Title: `Screening Financial Disclosure Risk` / subtitle: `Textual–Financial Feature Fusion and Explainable Anomaly Detection` / footer: `Chinese A-share Manufacturing Firms, 2021–2023` / `Group 12A2 · Intro FinTech · {PRESENTATION DATE}` |
| 2 | 三个研究问题 | 左侧问题，右侧编号 01–03 卡片。`Does MD&A text add detection value beyond financial features?`；`Which feature group drives the ranking?`；`Is the ranking stable across models and thresholds?` |
| 3 | 数据范围 | 三列来源→样本→基准。`CSMAR statements (2020–2023)`、`CNINFO annual reports (2021–2023)`、`3,694 firms / 10,172 firm-years`、`Beneish M-Score: evaluation only`。标注 `{FINAL QC COVERAGE}`。 |
| 4 | 研究流程 | 五步水平箭头：`Ingest`、`Extract MD&A`、`Construct 9 features`、`Rank anomalies`、`Evaluate & explain`。页脚小字：`No benchmark variable enters model training.` |
| 5 | 特征体系 | 左卡片 `6 financial features`：ROA, leverage, revenue growth, OCF/assets, receivables turnover, accruals/assets；右卡片 `3 textual features`：readability, sentiment balance, uncertainty ratio；底部 `Winsorise 1%/99% · subindustry-year z-score`。 |
| 6 | 模型设计 | 中心深色卡 `Isolation Forest`；两侧 `Finance-only` / `Text-only` / `Fused`；下方 robustness：`Autoencoder (16–8–16)`；参数：`500 trees · max_samples=256 · seed=42 · top 10% review queue`。 |
| 7 | RQ1 主结果 | 左：`Rank agreement with Beneish M-Score`；右三个预留值卡：`Finance-only: {RHO_FINANCE}`、`Text-only: {RHO_TEXT}`、`Fused: {RHO_FUSED}`。结论框：`{STATE ONLY AFTER REAL RUN: whether fused exceeds finance-only.}` |
| 8 | RQ2 可解释性 | 双栏：`Global SHAP feature group share` 预留 finance/text 条形占位；`Local explanation` 预留 top firm-year / top driver。底部 `Screening signals support review; they do not prove misconduct.` |
| 9 | RQ3 稳健性 | 左：top-10% overlap 矩阵占位；右：`Autoencoder robustness`，预留 `{AE_RHO}`；底部：`Sensitivity thresholds: 5%, 10%, 15%.` |
| 10 | 限制与边界 | 三张卡：`Dictionary sentiment is a proxy`、`PDF extraction coverage`、`M-Score is an imperfect benchmark`；底部 `Outputs are review-priority signals, not misconduct labels.` |
| 11 | 可复现性 | checklist：`SEED=42`、`versioned scripts & CSV intermediates`、`checkpointed downloads/extraction`、`one-command workflow`。右侧命令卡：`python scripts/run_99_full_pipeline.py`。 |
| 12 | 结论与分工 | `Conclusion: {FINAL ONE-SENTENCE FINDING}`；四成员、职责占位表；收尾 `Thank you · Questions`。 |

## 结果页替换规则

1. 只有在 `data/raw/csmar/FS_Comins.xlsx`、`data/raw/csmar/FS_Comscfd.xlsx` 到位并完成 `run_03`、`run_06`、`run_07`、`run_12` 后，才替换第 7–9、12 页花括号内容。
2. 第 7 页 rho 与第 8 页 SHAP 值从 `outputs/tables/` 读取；第 9 页 overlap / autoencoder 值同源读取。
3. 数据不支持的结论必须保留中性表述；绝不把 demo 数值写入终稿或演示。
