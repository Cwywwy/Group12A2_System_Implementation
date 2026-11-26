# 给复审 AI 的交接说明（Group 12A2 · FinTech 2026 · Option 2）

> 文件：`docs/ai_review_brief.md` ｜ 作者：Group12A2 DSW Team ｜ 分支：`main3`
> 用途：让第二个 AI 在不读聊天记录的前提下，**独立判断这篇论文的数据与结论是否站得住**。
> 阅读顺序建议：§2 结论一览 → §7 可核验断言 → §9 复审清单（那里列了 10 个最值得怀疑的点）。
> 文中每个数字都标了来源文件；§7 的每条断言都给了可直接运行的复核命令。
> 最后一次核验：2026-11-26，108 项检查 0 失败（`outputs/reports/audit_2026-11-26.md`）。

---

## 1. 项目与本次改动的来龙去脉

**论文题目**：Screening Financial Disclosure Risk through Textual-Financial Feature Fusion and Explainable Anomaly Detection: Evidence from Chinese A-share Manufacturing Firms, 2021–2025

**课程要求**：12–15 页研究型稿件（Introduction / Literature Review / Methodology / Experiments with Results），可投 Q2 以上期刊；12 月 15 日截止。**附录不计入页数**（导师口径），故篇幅以正文 11 页计。

**导师四条意见（原话）与本次对应改动**：

| # | 导师意见 | 本次改动 | 证据 |
|---|---|---|---|
| 1 | 更像管理/金融类文章，建议采用管理类参考文献风格 | 24 条参考文献全部改为 APA 7，正文 44 处方括号编号改为作者—年份 | `src/reporting/references_apa.py`、`tests/test_references_apa.py` |
| 2 | 数据是否有可能包含 2024 与 2025 | 面板由 2021–2023 扩到 **2021–2025**，样本 9,239 → 16,408 企业年 | §5.1、`data/processed/feature_table.csv` |
| 3 | 考虑简化或重组第 3、4 部分 | §3 由 755 词改为 750 词（吸收评估设计为 3.4），§4 由 1,231 词压到 379 词 | `src/reporting/manuscript_v04_text.py` |
| 4 | 考虑使用图表，给读者清晰图像 | 图由 3 张增至 5 张（新增研究流程图 4.1、Beneish 临界值漂移图 5.3） | `outputs/figures/manuscript/` |

**上一版（v0.3 / main2）与本版（v0.5 / main3）的核心差别**：样本窗口由三年扩到五年。这带来一个必须知道的后果——**前瞻违规标签在 2024、2025 年不可用**（见 §5）。本版没有回避，而是把「可用窗口止于 2023」变成一个显式的闸门，并在正文写清方向性影响。

---

## 2. 结论一览（与论文 §5 完全一致）

**主结果（n = 16,408 企业年 / 3,773 家；占比 93.2%）**

| 排序 | Spearman ρ（对 Beneish M-Score） | AUC vs 非标审计意见 | 前 10% 富集（校准后） |
|---|---|---|---|
| 仅财务孤立森林 | **−0.033**（p = 2.1e-5） | **0.787** [0.762, 0.809] | 2.54 |
| 仅文本孤立森林 | −0.021（p = 0.008） | 0.524 [0.488, 0.556] | 0.92 |
| 融合孤立森林 | −0.019（p = 0.014） | 0.759 [0.729, 0.787] | 2.23 |
| 融合自编码器 | −0.026（p = 0.001） | 0.696 [0.663, 0.723] | 2.01 |
| Beneish M-Score（基准） | — | **0.263** [0.233, 0.298] | 0.65 |

**两个需要复审者重点看的结论**

1. **Beneish M-Score 在这套样本里是「反向」的**：AUC 0.263 显著低于 0.5，即它判定为「可能操纵」的年份，带非标审计意见的概率反而更低。五种口径（窄/宽意见、任意/披露违规、严格时点）下方向一致。
2. **文本块几乎没有增量**：监督式折外 AUC，logit 仅财务 0.8646 → 融合 0.8641（**Δ = −0.0005**），GBM 0.8591 → 0.8629（**Δ = +0.0038**），八个 bootstrap 区间**没有一个排除零**。论文把这条写成了「诚实的零结果」，不是遗漏。

---

## 3. 数据来源与链路（每一步都可查）

```
CSMAR 财务报表 (xlsx)  +  CSMAR 审计意见/违规 (xlsx)  +  CNINFO 年报 PDF
        ↓ run_03                    ↓ run_03b                   ↓ run_02 / run_04 / run_05
data/interim/finance_intermediate.csv (30,861 行, FY2020–FY2025)
        ↓ run_06
data/processed/feature_table.csv  (17,600 企业年, 3,893 家, 9 个特征)
data/processed/event_table.csv    (16,408 企业年的事件标签)
        ↓ run_07 (孤立森林/自编码器)  ↓ run_07b (外部结果)  ↓ run_07c (严格时点)
outputs/tables/*.csv
        ↓ build_section5 → patch_section5_v06
outputs/manuscript/Group12A2_Final_EN_v0.5.docx
```

| 文件 | 行数 | 关键内容 | 备注 |
|---|---|---|---|
| `data/raw/csmar/FS_Combas.xlsx` | 259,511 × 154 | 资产负债表，含 FY2020–FY2025 | 3 行表头；A/B 两套 Typrep 行需按列合并，不能只筛 A |
| `data/raw/csmar/FS_Comins.xlsx` / `FS_Comscfd.xlsx` | — | 利润表 / 现金流量表 | 直接法现金流**没有折旧行**，故 DEPI 中性化为 1.0 |
| `data/raw/csmar_events/FIN_Audit.xlsx` | FY2020–2025: 4,250 / 4,762 / 5,135 / 5,354 / 5,400 / 5,494 | 审计意见（Audittyp） | 下载于 2026-11-10 |
| `data/raw/csmar_events/STK_Violation_Main.xlsx` | 全 A 股 | 违规公告（DeclareDate、ViolationType） | 最后一条 DeclareDate = **2026-10-20**，这是闸门的快照依据 |
| `data/raw/cninfo/2021…2025/` | 4,697 / 5,060 / 5,277 / 5,114 / **3,762** | 年报 PDF | 2025 年为样本框全量 3,762 份 |
| `data/interim/finance_intermediate.csv` | 30,861 | 逐年 4,496 / 4,922 / 5,193 / 5,355 / 5,401 / 5,494 | FY2020 只作为基期（算增长与 Beneish） |
| `data/processed/feature_table.csv` | 17,600 | 财务完整 16,641；文本 ok 17,349 / suspicious 16 / missing 235 | 逐年 3,165 / 3,404 / 3,603 / 3,666 / 3,762 |
| `data/processed/event_table.csv` | 16,408 | 窄非标 322、宽非标 593；违规 1,965 / 1,337（仅 9,239 行窗口） | 含 announce_date |
| `outputs/tables/anomaly_scores.csv` | 16,408 | 四个排序分数 | 逐年 2,732 / 3,124 / 3,383 / 3,531 / 3,638 |

---

## 4. 口径定义（复审时最容易出分歧的部分）

**九个特征**
- 财务六项：`roa`、`leverage`、`revenue_growth`、`ocf_to_assets`、`receivables_turnover`、`accruals_to_assets`
- 文本三项：`readability`（中文可读性）、`sentiment_balance`（情感均衡度）、`uncertainty_ratio`（不确定性比率）
- 预处理：1%/99% 分位缩尾 → 在「制造业二级行业 × 年度」单元格内标准化（单元格 < 20 个观测时退回全样本标准化）

**模型**
- 主模型：Isolation Forest，500 棵树，`max_samples = 256`，`seed = 42`；三类矩阵（仅财务 / 仅文本 / 融合）分别估计
- 稳健模型：自编码器 16-8-16，ReLU，Adam，`seed = 42`，以重构误差为分数
- 解释：SHAP，在上限 2,000 行的子样本上计算；财务块占 65.7%，文本块 34.3%

**评估**
- 主相关：各排序分数与 Beneish M-Score 的 Spearman ρ（**负数代表与「高 M 值 = 高风险」的方向相反**）
- 外部结果一：非标审计意见（同期，标签来自同一份年报的审计意见）
- 外部结果二：t+1 违规（前瞻，仅 2021–2023 可用，理由见 §5）
- 富集：前 10% 的事件率 ÷ 基准率，两个基准（历史 M > −1.78 固定阈值 / 样本内 q90 校准）
- 监督式对照：`StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42)`，**按 symbol 分组**（保证同一公司不跨折），logit 用 balanced 权重

---

## 5. 关键设计决策与理由（这些是「选择」，不是「发现」）

| 决策 | 内容 | 理由 | 若换一种做法的后果 |
|---|---|---|---|
| D1 | 面板 2021–2025，FY2020 作基期 | 导师要求含 2024/2025；2020 是疫情年，DSRI/GMI/AQI/TATA 会被机械扭曲，故只当基期不做观测 | 若把 2020 作为观测年，Beneish 各分量的可比性会被削弱 |
| D2 | **违规标签只用于 2021–2023** | `VIOLATION_SNAPSHOT = (2026, 10, 20)`；t+1 全年必须落在快照之前（再留一年供应商滞后） | 若强行用 2024/2025：t+1 违规率从约 21% 掉到 13.5% / 1.0%，AUC 会被系统性压低 |
| D3 | 闸门的方向性已披露 | 若把五年全计入，Beneish 违规 AUC 反而**升**到 0.439（本文 0.407）、仅财务**降**到 0.594（本文 0.598） | 这说明剔除对基准不利、对本文有利，正文 §5.6 已明写 |
| D4 | 置信区间按「企业年」独立重抽 | 与流水线一致的常规做法 | 按整家公司重抽会放宽约 1/3：[0.762, 0.809] → [0.753, 0.820]；已写入 §5.6 |
| D5 | Beneish 用两个基准 | 固定 −1.78 是文献阈值，q90 是样本内校准 | 文献阈值在本样本的错误率高（2024 年富集仅 0.20–0.34），故两个都报 |
| D6 | DEPI 中性化为 1.0 | CSMAR 直接法现金流无折旧行（30,861 行全缺） | 这是一个**已知的近似**，会让 M-Score 与使用间接法的文献略有不可比；附录已披露 |
| D7 | §3 保留 750 词、§4 压到 379 词 | §3 吸收了原 §4.5 的评估设计，删掉的是重复复述 | 若同时压缩 §3，方法细节会不足 |
| D8 | 中文稿只做翻译 | 避免两稿论证漂移 | 中文稿没有任何新增论断 |
| D9 | 论文内不写修订说明 | 交付物是论文本身 | 导师回复单独进行 |

---

## 6. 五年 vs 三年：为什么最终选五年

三年版（main1/main2，n = 9,239）的头部非标意见 AUC 是 0.8015，五年版是 0.7869。**看似三年更好，但这是样本更容易，不是模型更好**：

- 两个区间 [0.774, 0.833] 与 [0.762, 0.809] 大幅重叠，统计上不可区分；
- 逐年仅财务 AUC 为 0.838 / 0.800 / 0.772 / 0.726 / 0.778，对应事件数 76 / 68 / 60 / 52 / 66——2024 年最低，但该年只有 52 个非标意见，这一年本身也最不确定（不要把 0.726 当作稳定估计）；
- 三年版四个相关系数里**两个不显著**（融合 p = 0.091、自编码器 p = 0.53），五年版四个全部显著（2.1e-5 / 0.008 / 0.014 / 0.001）；
- 事件数 204 → 322，Beneish 的区间宽度 0.081 → 0.065；
- 五年样本暴露了三年样本看不到的结构性证据：**Beneish 的 q90 临界值逐年下移 −1.26 → −1.44 → −1.63 → −1.68 → −1.85**，而它的 AUC 始终在随机线以下。

论文没有隐藏三年数字：附录表 A.1 并列 2021–2023（0.802 / 0.242）、2021–2024（0.791 / 0.248）、2021–2025（0.787 / 0.263）。

---

## 7. 可核验断言（复审的核心表）

| # | 断言 | 证据文件 | 复核方式 |
|---|---|---|---|
| 1 | 样本框 17,600 企业年 / 3,893 家，逐年 3,165 / 3,404 / 3,603 / 3,666 / 3,762 | `data/processed/feature_table.csv` | 按 `fiscal_year` 计数 |
| 2 | 分析样本 16,408 / 3,773，损耗链 17,600 → 16,641 → 16,640 → 16,408 | 表 B.5 | `anomaly_scores.csv` 行数 + `symbol` 去重数 |
| 3 | 窄非标 322（1.96%）、宽非标 593（3.6%） | `event_table.csv` | 从 `FIN_Audit.xlsx` 重算 Audittyp 分类 |
| 4 | 违规 1,965 / 1,337，窗口 9,239 行 | 表 B.6 | 从 `STK_Violation_Main.xlsx` 按 `declare_year = fiscal_year + 1` 重算 |
| 5 | ρ = −0.033 / −0.021 / −0.019 / −0.026 及四个 p 值 | `outputs/tables/model_metrics.csv` | scipy `spearmanr` |
| 6 | 五个非标意见 AUC（0.787 / 0.524 / 0.759 / 0.696 / 0.263） | `event_ranking_metrics.csv` | `roc_auc_score` |
| 7 | 四个违规 AUC（0.598 / 0.499 / 0.581 / 0.561 / 0.407） | 同上 | 注意必须**只在 2021–2023 上算** |
| 8 | 八个富集值 | `topk_metrics.csv` | 前 10% 事件率 ÷ 基准率 |
| 9 | 监督式 0.8646 / 0.8641（logit）、0.8591 / 0.8629（GBM） | `event_supervised_metrics.csv` | 重跑同一 5 折（`run_17_audit_results.py` 已实现） |
| 10 | 论文十张表逐格与 CSV 一致；中英文稿数字集合完全相同 | `Group12A2_Final_EN_v0.5.docx` / `_CN.docx` | `run_17_audit_results.py` 的 D 组 |

**一条命令跑完以上全部**：

```powershell
.\.venv\Scripts\python.exe scripts\run_17_audit_results.py
# 期望：108 checks, 0 failures；报告写 outputs/reports/audit_2026-11-26.md
```

---

## 8. 复现方式

```powershell
# 环境：Python 3.12.14，仓库根目录下的 .venv
.\.venv\Scripts\python.exe -m pytest -q            # 期望 203 passed

# 全链路（需要 data/ 与 41 GB 原始数据，仓库不含）
.\.venv\Scripts\python.exe scripts\run_01_sample.py
.\.venv\Scripts\python.exe scripts\run_03_build_finance_intermediate.py
.\.venv\Scripts\python.exe scripts\run_06_build_feature_table.py
.\.venv\Scripts\python.exe scripts\run_07_experiment.py
.\.venv\Scripts\python.exe scripts\run_07b_event_models.py

# 稿件重建
.\.venv\Scripts\python.exe scripts\patch_section5_v06.py
.\.venv\Scripts\python.exe scripts\assemble_chinese_draft.py
.\.venv\Scripts\python.exe scripts\run_13_build_chinese_docx.py
```

注意：`data/` 与 `STK_*` 在 `.gitignore` 中（授权数据，约 41 GB），所以**从 GitHub 克隆后无法直接重跑**；能跑的是测试与核验脚本中对已提交表格的部分。

---

## 9. 复审清单：最值得怀疑的 10 个点

请按「结论 → 依据 → 我的辩护」的顺序逐条判断，不要默认辩护成立。

1. **Beneish AUC 0.263 低于随机，是不是标签或方向搞反了？**
   辩护：违规口径（前瞻、公告）同样低于随机边缘（0.407，接近 0.5 但方向仍低）；且逐年 5 次重复一致。可查 `event_ranking_metrics.csv` 五条 Beneish 行。

2. **违规标签只用 2021–2023，是不是「挑对自己有利的年份」？**
   辩护：闸门规则在看结果之前由数据可得性决定（snapshot 2026-10-20）；且已量化方向——纳入 2024/2025 会让基准更好、本文更差。若仍认为可疑，正确做法是要求作者报出 ungated 值（已给：0.4394 / 0.5935）。

3. **DEPI 中性化会不会让「Beneish 失效」这一结论站不住？**
   辩护：DEPI 只是八分量之一，中性化后 M-Score 仍与文献高度相关；且失效主要表现为**方向颠倒**而非噪声，中性化不会导致符号翻转。这是全篇最需要外部判断的一处。

4. **非标意见是同期标签，0.787 的 AUC 是否只是「识别已被审计师标记的报告」？**
   辩护：是，论文明确写了这一点（§5.5、§5.6 caveat）；前瞻证据只有违规那一列，水平更低（0.598）。不构成预测能力的证据。

5. **文本特征用的是词典与可读性，不是大模型，会不会低估文本价值？**
   辩护：属设计选择，论文把结论限定为「在这套中文 MD&A 特征下没有增量」；附录 B.3 有词典替换的对照实验（Yao et al. 2021 全表替代），结论不变。

6. **0.787 与 0.802（三年版）的差异是否被过度解读？**
   辩护：论文没有解读，只在附录并列；正文主结论用的是显著性而非点估计。

7. **区间是不是太窄？**
   辩护：确实偏窄，原因是按企业年独立重抽。已披露按公司整群重抽的结果（[0.753, 0.820]）。若审稿要求，应改为主区间用整群。

8. **2024 年文本特征来自另一个仓库（DSW_all），是否有可比性？**
   辩护：同一脚本、同一字段、同一词典版本，行数与 2024 年报数吻合（5,114 → 5,118）；但这是**唯一没有在本次会话内重新抽取的一年**，属于已知边界。

9. **2021 年 63 个 920xxx 代码取不到年报，是否造成选择偏差？**
   辩护：这些是北交所新代码，其旧代码（8xxxxx）期间的年报无法用新代码检索；属技术性损耗（约占 2021 年 2%），且北交所公司规模小、非标率未必系统性不同。未做敏感性分析——这是一个可以要求补的点。

10. **页数 19 页，会不会超出 12–15 页的要求？**
    事实：PDF 合计 19 页 = 正文 1–11 页 + 附录 12–19 页（References 与 Appendix A 都从第 11 页起）。导师已明确**附录不计入文章总页数**，故计入篇幅的是正文 11 页，篇幅问题按导师口径结案，不再作为待办。若日后需要正文更接近 12 页下限，做法是把附录 B.2 的解释性段落移回 §5.4（只搬文字、不动数字），而不是加新分析。

---

## 10. 文件清单

**交付件**
- `outputs/manuscript/Group12A2_Final_EN_v0.5.docx` / `.pdf`（19 页 = 正文 11 + 附录 8）
- `outputs/manuscript/Group12A2_Final_CN.docx` / `.pdf`（22 页）
- `outputs/Group12A2_Results_Summary.xlsx`（中文，6 表 + 6 图）/ `_EN.xlsx`
- `outputs/reports/audit_2026-11-26.md`（108 项核验）

**结果表**：`outputs/tables/` 下 `anomaly_scores.csv`、`model_metrics.csv`、`event_ranking_metrics.csv`、`event_supervised_metrics.csv`、`topk_metrics.csv`、`ranking_overlap.csv`、`shap_global.csv`、`shap_group_contributions.csv`、`shap_local_top1.csv`、`audit_intervals.json`

**图表源**：`scripts/build_report_figures.py` → `outputs/figures/manuscript/figure_4_1_pipeline(_cn).png`、`figure_5_1_sample.png`、`figure_5_2_spearman.png`、`figure_5_3_enrichment.png`、`figure_5_7_year_diagnostics.png`、`figure_5_5_external_auc.png`

**正文生成**：`src/reporting/manuscript_v04_text.py`（§3/§4）、`manuscript_v04_section5.py`（§5、摘要、结论）、`manuscript_v04_appendix.py`（附录 A1、B1–B6）、`references_apa.py`（参考文献）

**关键脚本**：`scripts/run_17_audit_results.py`（独立核验）、`scripts/run_00_coverage_gate.py`（覆盖率闸门）、`scripts/run_07b_event_models.py`（含标签闸门）、`scripts/patch_section5_v06.py`（稿件装配）

**测试**：`tests/` 共 203 项，含 `test_cninfo_client.py`（18）、`test_event_label_window.py`（5）、`test_references_apa.py`（12）、`test_patch_manuscript_v05.py`（5）、`test_build_results_excel.py`（14）

---

## 11. 环境与版本

| 项 | 值 |
|---|---|
| 仓库 | `https://github.com/Cwywwy/Group12A2_System_Implementation` |
| 分支 | `main3`（本次）、`main2`（v0.3 三年版）、`main`（15 页压缩版） |
| Python | 3.12.14（`.venv`） |
| 关键依赖 | pandas、numpy、scipy、scikit-learn、matplotlib、python-docx、openpyxl、pypdf、PyMuPDF（仅用于渲染检查） |
| 随机种子 | 全局 42（IF、AE、5 折、bootstrap 均固定） |
| 核验日期 | 2026-11-26 |

---

## 12. 给复审 AI 的一句话请求

请优先回答一个问题：**「Beneish 反向」与「文本无增量」这两个结论，在上述证据强度下是否成立？** 若不成立，指出最薄弱的一环以及需要补的最小实验；若成立，指出论文中仍应加写的一句限定。
