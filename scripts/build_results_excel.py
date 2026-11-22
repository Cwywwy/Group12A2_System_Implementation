#!/usr/bin/env python
"""Build the Excel visualisation workbook of the final results.

Reads the released tables under ``outputs/tables/`` (the same single source of
truth as the manuscript, see ``scripts/build_section5.py``) and writes a styled
workbook with one sheet per research question plus overview and notes, including
native Excel charts (enrichment, SHAP, external-validation AUC, delta-AUC and
lexicon-density comparisons).

Usage::

    .venv\\Scripts\\python.exe scripts\\build_results_excel.py [--lang cn|en] [--out path.xlsx]

``--lang en`` produces the English-language workbook (default output
``outputs/Group12A2_Results_Summary_EN.xlsx``); ``cn`` is the default.

Exit codes: 0 = written, 2 = a required input table is missing.

Revision history
2026-11-22  created: overview, RQ1-RQ3, 5.6 and 5.7 sheets with six charts.
2026-11-22  added --lang en: full English version (sheet names, labels, notes).
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime
from pathlib import Path

from openpyxl import Workbook
from openpyxl.chart import BarChart, PieChart, Reference
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "outputs" / "tables"
EVENT_JSON = ROOT / "data" / "processed" / "event_table.json"
DEFAULT_OUT = ROOT / "outputs" / "Group12A2_Results_Summary.xlsx"
DEFAULT_OUT_EN = ROOT / "outputs" / "Group12A2_Results_Summary_EN.xlsx"

# ---- palette (matches the slide deck spec) ---------------------------------
INK = "102A43"
PRIMARY = "0B5CAB"
ACCENT = "2D8C7A"
HIGHLIGHT = "F59E0B"
BORDER = "D9E2EC"
CARD = "FFFFFF"
BG = "F7F9FC"
MUTED = "627D98"
LIGHT_BLUE = "E1EDFB"
LIGHT_AMBER = "FEF3E2"

THIN = Side(style="thin", color=BORDER)
BOX = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)

# ---- language switch -------------------------------------------------------
CURRENT: dict[str, str] = {"lang": "cn", "font": "微软雅黑"}


def set_lang(lang: str) -> None:
    CURRENT["lang"] = lang
    CURRENT["font"] = "Arial" if lang == "en" else "微软雅黑"


def T(key: str) -> str:
    return STRINGS[CURRENT["lang"]][key]


def L(table: dict[str, dict[str, str]]) -> dict[str, str]:
    return table[CURRENT["lang"]]


SHEET_NAMES = {
    "cn": ["总览 Overview", "RQ1 主结果", "RQ2 可解释", "RQ3 稳健性",
           "§5.7 外部检验", "§5.6 两版对比", "说明 Notes"],
    "en": ["Overview", "RQ1 Main results", "RQ2 Explainability", "RQ3 Robustness",
           "5.7 External validation", "5.6 Two specifications", "Notes"],
}

MODEL_LABELS = {
    "cn": {
        "if_finance": "Finance-only IF（仅财务）",
        "if_text": "Text-only IF（仅文本）",
        "if_fused": "Fused IF（融合）",
        "ae_fused": "Fused AE（自编码器）",
    },
    "en": {
        "if_finance": "Finance-only IF",
        "if_text": "Text-only IF",
        "if_fused": "Fused IF",
        "ae_fused": "Fused AE",
    },
}
SCORE_LABELS = {
    "cn": {
        "finance-only IF": "Finance-only IF（仅财务）",
        "text-only IF": "Text-only IF（仅文本）",
        "fused IF": "Fused IF（融合）",
        "fused AE": "Fused AE（自编码器）",
        "Beneish M-Score": "Beneish M-Score（代理基准）",
    },
    "en": {
        "finance-only IF": "Finance-only IF",
        "text-only IF": "Text-only IF",
        "fused IF": "Fused IF",
        "fused AE": "Fused AE",
        "Beneish M-Score": "Beneish M-Score (proxy)",
    },
}
EVENT_LABELS = {
    "cn": {
        "mod_opinion": "非标审计意见（窄口径）",
        "mod_opinion_wide": "非标审计意见（宽口径）",
        "violation_any_t1": "t+1 违规（任意类型）",
        "violation_disclosure_t1": "t+1 违规（披露类）",
    },
    "en": {
        "mod_opinion": "Modified opinion (narrow)",
        "mod_opinion_wide": "Modified opinion (wide)",
        "violation_any_t1": "t+1 violation (any)",
        "violation_disclosure_t1": "t+1 violation (disclosure)",
    },
}
SUPERVISED_MODEL_LABELS = {
    "cn": {"logit": "Logit（逻辑回归）", "hgb": "HGB（梯度提升）"},
    "en": {"logit": "Logit (logistic regression)", "hgb": "HGB (gradient boosting)"},
}
SUPERVISED_SHORT = {
    "cn": {"logit": "Logit", "hgb": "HGB"},
    "en": {"logit": "Logit", "hgb": "HGB"},
}
FEATURE_LABELS = {
    "cn": {
        "ocf_to_assets": "经营现金流/总资产",
        "revenue_growth": "营业收入增长",
        "readability": "可读性（文本）",
        "sentiment_balance": "语调（文本）",
        "receivables_turnover": "应收账款周转",
        "uncertainty_ratio": "不确定词占比（文本）",
        "accruals_to_assets": "应计项目/总资产",
        "roa": "ROA",
        "leverage": "杠杆率",
    },
    "en": {
        "ocf_to_assets": "Operating cash flow / assets",
        "revenue_growth": "Revenue growth",
        "readability": "Readability (text)",
        "sentiment_balance": "Sentiment balance (text)",
        "receivables_turnover": "Receivables turnover",
        "uncertainty_ratio": "Uncertainty ratio (text)",
        "accruals_to_assets": "Accruals / assets",
        "roa": "ROA",
        "leverage": "Leverage",
    },
}
LEXICON_LABELS = {
    "cn": {
        "positive_terms": "正面词",
        "negative_terms": "负面词",
        "sentiment_terms": "情感词合计",
        "uncertainty_terms": "不确定词",
    },
    "en": {
        "positive_terms": "Positive terms",
        "negative_terms": "Negative terms",
        "sentiment_terms": "Sentiment terms (total)",
        "uncertainty_terms": "Uncertainty terms",
    },
}
FUSED_SET_LABELS = {
    "cn": {"finance": "仅财务 Finance", "text": "仅文本 Text", "fused": "融合 Fused"},
    "en": {"finance": "Finance", "text": "Text", "fused": "Fused"},
}

STRINGS: dict[str, dict[str, str]] = {
    "cn": {
        "ov_title": "Group 12A2 · 财务披露风险筛查 —— 结果可视化总览",
        "ov_sub": ("与定稿 Group12A2_Final_EN（§5.1–§5.7）完全同源；数字由 outputs/tables/ 现场生成"
                   "（{stamp}）。n = 8,140 firm-years / 3,265 家公司，2021–2023。"),
        "ov_head": ["关键指标 · Key metric", "值 · Value", "论文出处 · In the paper"],
        "ov_concl_title": "一句话结论（诚实用语 · Honest phrasing）",
        "ov_concl": ("财务特征对 Beneish 代理有弱但显著的排序信号（ρ = 0.136）；文本单独对代理基准无增量、"
                     "对真实事件更弱；但融合在真实监管事件上给出小而一致的正增量（ΔAUC +0.006 ~ +0.026）。"
                     "Beneish 代理对真实非标意见的 AUC 仅 0.405（低于随机）——第一版的代理基准方向相反，"
                     "外部检验（§5.7）比代理基准更可信。"),
        "ov_nav_title": "工作簿导航 · Sheets",
        "ov_nav": [
            ["工作表", "内容", "图表"],
            ["总览 Overview", "关键数字与一句话结论", "—"],
            ["RQ1 主结果", "Spearman ρ、双基准 top-5/10/15% 富集率", "图1 富集率柱状对比"],
            ["RQ2 可解释", "SHAP 组贡献与全局前 9 特征", "图2 组贡献饼图、图3 特征重要性"],
            ["RQ3 稳健性", "top-10% 名单重叠（Jaccard）矩阵", "—"],
            ["§5.7 外部检验", "真实监管事件：事件率、AUC、lift、监督 ΔAUC", "图4 AUC、图5 ΔAUC"],
            ["§5.6 两版对比", "词典密度 v0.1 → v0.2 与做法差异", "图6 词典密度对比"],
            ["说明 Notes", "口径、数据来源与复现命令", "—"],
        ],
        "rq1_title": "RQ1：文本特征是否带来增量？—— 排序一致性与队列富集",
        "rq1_sub": "Beneish M-Score 为评估基准（不参与训练）。富集率 > 1 表示该队列的事件密度高于全样本。",
        "rq1_head": ["模型", "Spearman ρ", "p 值"],
        "rq1_head2": ["模型", "富集率·legacy(M>−1.78) top-10%", "富集率·样本校准 top-10%",
                      "富集率·样本校准 top-5%", "富集率·样本校准 top-15%"],
        "rq1_note": ("口径：legacy = M > −1.78（在本样本标红 62.8%，噪声大）；样本校准 = M 落在样本前 10%（M > 16.52），"
                     "构造上事件率为 10%。同一排序，仅基准不同。"),
        "rq1_chart": "图1  top-10% 队列富集率：样本校准 vs legacy 基准",
        "rq1_y": "富集率（1 = 全样本水平）",
        "rq2_title": "RQ2：什么驱动了异常分数？—— SHAP 全局解释",
        "rq2_sub": "对融合 Isolation Forest 的 SHAP 全局贡献；财务组 6 个特征、文本组 3 个特征。",
        "rq2_head": ["特征组", "特征数", "SHAP 贡献占比"],
        "rq2_pie": "图2  SHAP 组贡献",
        "rq2_head2": ["特征", "mean |SHAP|"],
        "rq2_chart3": "图3  全局特征重要性（mean |SHAP|）",
        "rq2_note": ("前三为 经营现金流/总资产、营收增长、可读性；三个文本特征全部进入前五，但组层面文本合计仅 34.6%，"
                     "且其对代理基准的排序力近乎为零（见 RQ1）。"),
        "rq3_title": "RQ3：排序是否稳健？—— top-10% 名单重叠（Jaccard）",
        "rq3_sub": "四个排序两两之间的 top-10% 名单重合度；AE 与 IF 的重合仅 0.373，稳健性未复现。",
        "rq3_head": ["Jaccard 重叠"],
        "rq3_note": ("读法：仅财务与融合的名单重合 0.817（融合基本复刻财务排序）；仅财务与仅文本仅 0.111（文本给出几乎独立的名单，"
                     "但该名单对基准无信号）。自编码器未能复现隔离森林排序（ρ = 0.009，p = 0.409）。"),
        "rq3_year_title": "分年度 Spearman ρ（稳健性）",
        "rq3_year_head": ["模型", "2021", "2022", "2023"],
        "rq3_year_note": "分年度排序稳定：财务单独逐年为正且上升，文本单独三年全为负，融合逐年低于财务单独。",
        "ext_title": "§5.7 外部检验：真实监管事件上的表现",
        "ext_sub": ("结果变量来自 CSMAR：FIN_Audit（审计意见，同期=识别而非预测）与 STK_Violation_Main（违规，t+1 对齐=前瞻）。"
                    "审计意见覆盖率 100%。"),
        "ext_head": ["事件标签", "事件数", "事件率", "2021", "2022", "2023"],
        "ext_head2": ["分数", "AUC 非标意见", "AUC 披露类 t+1", "lift 前10% 非标", "lift 前10% 披露"],
        "ext_chart4": "图4  真实事件 AUC：非标意见 vs 披露类违规（0.5 = 随机）",
        "ext_note4": "Beneish 代理对真实非标意见的 AUC 仅 0.405，低于随机——代理基准方向相反。",
        "ext_head3": ["特征组", "Logit AUC 非标", "Logit Δ非标", "HGB AUC 非标", "HGB Δ非标",
                      "Logit AUC 披露", "Logit Δ披露", "HGB AUC 披露", "HGB Δ披露"],
        "ext_delta_short": {"mod_opinion": "窄非标", "mod_opinion_wide": "宽非标",
                            "violation_any_t1": "任意违规", "violation_disclosure_t1": "披露违规"},
        "ext_delta_sep": "·",
        "ext_hd": ["组合", "ΔAUC（融合 − 仅财务）"],
        "ext_chart5": "图5  监督式 ΔAUC（融合 − 仅财务，8 组合；正值 = 增量）",
        "ext_note5": ("按公司分组的 5 折交叉验证（StratifiedGroupKFold，无同公司泄漏）。8 个组合的 ΔAUC 全部为正，"
                      "5 个 bootstrap 区间不含 0：文本块对真实事件有小而一致的互补增量；文本单独则弱于财务。"),
        "ver_title": "§5.6 第一版 → 第二版：做法改进与结果差异",
        "ver_sub": "改进让阴性结论更可信，而不是翻转结论。第一版数据与代码保留在 archive_v0.1 与 git tag v0.1-baseline。",
        "ver_head": ["设计选择", "第一版 v0.1", "第二版 v0.2"],
        "ver_rows": [
            ["情感词典", "引导版（正 38 / 负 33）", "姚加权等 (2021) 全量（正 3,585 / 负 1,633）"],
            ["不确定词表", "引导版 23 词", "扩充约 100 词"],
            ["命中方式", "子串计数（'不' 会命中 '不错'）", "jieba 词元精确匹配（用户词典 5,218 词）"],
            ["评估基准", "仅 M > −1.78（标红 62.8%）", "双口径：legacy + 样本前 10%（M > 16.52）"],
            ["文本 ρ（vs M-Score）", "-0.030", "-0.029（结论不变）"],
            ["融合 ρ（vs M-Score）", "0.103", "0.103"],
            ["文本 top-10% 富集（校准）", "1.069", "0.848（反而跌破 1）"],
            ["结论变化", "阴性：文本无增量", "阴性更硬：词表 8.3× 密度下结论不变"],
        ],
        "ver_head2": ["指标", "v0.1 每千词元命中", "v0.2 每千词元命中", "倍数"],
        "ver_chart6": "图6  词典命中密度：v0.1 → v0.2（同一批 MD&A 文本）",
        "ver_note": ("在 2021 年 200 篇 MD&A（175.6 万词元）上对比：情感词命中 13.4 → 111.3 / 千词元（8.3×）。"
                     "否定结论不是词表太稀所致。"),
        "notes_title": "口径、数据来源与复现",
        "notes_head": ["项", "说明"],
        "notes_rows": [
            ["数字来源", "outputs/tables/ 的 8 张 CSV + data/processed/event_table.json；与论文同源（build_section5.py 同一来源）。"],
            ["样本", "n = 8,140 firm-years / 3,265 家公司，2021–2023，A 股制造业；9 特征 + M-Score 齐全的子集（框内 10,172 条）。"],
            ["RQ1 基准口径", "legacy = M > −1.78；样本校准 = M 前 10%（q90 = 16.52）。富集率 = 队列事件率 ÷ 全样本事件率。"],
            ["外部检验口径", "非标意见窄口径 = 保留 / 无法表示 / 否定（188 条，2.31%）；宽口径再加强调事项段（327 条，4.02%）。"
             "审计意见为同期结果（识别），t+1 披露类违规为前瞻（预测）。"],
            ["监督式评估", "Logit 与 HistGradientBoosting，SimpleImputer + 标准化，按公司分组 5 折交叉验证防泄漏；"
             "ΔAUC 为配对 bootstrap（400 次）。"],
            ["诚实边界", "文本单独在所有真实事件上弱于财务；融合的增量小但方向一致（5/8 区间不含 0）。"
             "勿写成『文本很强』或『发现欺诈』——教授要求如实报告。"],
            ["重新生成", ".venv\\Scripts\\python.exe scripts\\build_results_excel.py"],
            ["配套文件", "outputs/reports/experiment_summary.md、v02_results_diff.md、outputs/branches/*.md"],
        ],
    },
    "en": {
        "ov_title": "Group 12A2 · Financial Disclosure Risk Screening — Results at a Glance",
        "ov_sub": ("Same source as the final manuscript Group12A2_Final_EN (§5.1–§5.7); all numbers are recomputed "
                   "live from outputs/tables/ (generated {stamp}). n = 8,140 firm-years / 3,265 firms, 2021–2023."),
        "ov_head": ["Key metric", "Value", "In the paper"],
        "ov_concl_title": "One-line conclusion (honest phrasing)",
        "ov_concl": ("Finance features carry a weak but significant ranking signal against the Beneish proxy (ρ = 0.136). "
                     "Text alone adds nothing on the proxy and is weaker still on real events; the fused model, however, "
                     "adds a small but consistent positive increment on real regulatory outcomes (ΔAUC +0.006 ~ +0.026). "
                     "The Beneish proxy itself reaches only AUC 0.405 for real modified opinions (below chance) — the "
                     "first-version benchmark points the wrong way, so the external validation (§5.7) is more credible "
                     "than the proxy benchmark."),
        "ov_nav_title": "Workbook navigation",
        "ov_nav": [
            ["Sheet", "Contents", "Charts"],
            ["Overview", "Key numbers and one-line conclusion", "—"],
            ["RQ1 Main results", "Spearman ρ, dual-benchmark top-5/10/15% enrichment", "Chart 1 enrichment comparison"],
            ["RQ2 Explainability", "SHAP group contributions and top-9 feature importances", "Chart 2 pie, Chart 3 importances"],
            ["RQ3 Robustness", "Top-10% list overlap (Jaccard) matrix", "—"],
            ["5.7 External validation", "Real regulatory events: rates, AUC, lift, supervised ΔAUC", "Chart 4 AUC, Chart 5 ΔAUC"],
            ["5.6 Two specifications", "Lexicon density v0.1 → v0.2 and design changes", "Chart 6 density"],
            ["Notes", "Definitions, sources and reproduction commands", "—"],
        ],
        "rq1_title": "RQ1: Do text features add information? — Ranking consistency and queue enrichment",
        "rq1_sub": "The Beneish M-Score is the evaluation benchmark only (never trained on). Enrichment > 1 means the queue is denser in flagged events than the full sample.",
        "rq1_head": ["Model", "Spearman ρ", "p-value"],
        "rq1_head2": ["Model", "Enrichment · legacy (M>−1.78) top-10%", "Enrichment · calibrated top-10%",
                      "Enrichment · calibrated top-5%", "Enrichment · calibrated top-15%"],
        "rq1_note": ("Definitions: legacy = M > −1.78 (flags 62.8% of this sample — noisy); calibrated = M in the sample's "
                     "top decile (M > 16.52), so the event rate is 10% by construction. Same ranking, different benchmark only."),
        "rq1_chart": "Chart 1  Top-10% enrichment: calibrated vs legacy benchmark",
        "rq1_y": "Enrichment (1 = full-sample rate)",
        "rq2_title": "RQ2: What drives the anomaly scores? — Global SHAP explanation",
        "rq2_sub": "Global SHAP contributions to the fused Isolation Forest; six finance features and three text features.",
        "rq2_head": ["Feature group", "Features", "SHAP share"],
        "rq2_pie": "Chart 2  SHAP group contribution",
        "rq2_head2": ["Feature", "mean |SHAP|"],
        "rq2_chart3": "Chart 3  Global feature importance (mean |SHAP|)",
        "rq2_note": ("The top three are operating cash flow / assets, revenue growth and readability; all three text features "
                     "reach the top five, yet the text group contributes only 34.6% in total and its ranking power against "
                     "the proxy benchmark is near zero (see RQ1)."),
        "rq3_title": "RQ3: Is the ranking robust? — Top-10% list overlap (Jaccard)",
        "rq3_sub": "Pairwise top-10% list overlap between the four rankings; AE–IF overlap is only 0.373, so robustness does not replicate.",
        "rq3_head": ["Jaccard overlap"],
        "rq3_note": ("How to read: finance and fused share 0.817 of their top-10% lists (fused essentially reproduces the "
                     "finance ranking); finance vs text share only 0.111 (text yields an almost independent list, but that "
                     "list has no signal against the benchmark). The autoencoder does not replicate the Isolation Forest "
                     "ranking (ρ = 0.009, p = 0.409)."),
        "rq3_year_title": "Spearman ρ by year (robustness)",
        "rq3_year_head": ["Model", "2021", "2022", "2023"],
        "rq3_year_note": ("Stable by year: finance-only is positive in every year and rising, text-only is negative in all "
                          "three years, and the fused ranking trails the finance-only ranking in every year."),
        "ext_title": "§5.7 External validation: performance on real regulatory outcomes",
        "ext_sub": ("Outcomes come from CSMAR: FIN_Audit (audit opinions, contemporaneous = detection rather than prediction) "
                    "and STK_Violation_Main (violations, t+1 aligned = forward-looking). Audit-opinion coverage is 100%."),
        "ext_head": ["Event label", "Count", "Rate", "2021", "2022", "2023"],
        "ext_head2": ["Score", "AUC opinion", "AUC disclosure t+1", "Lift top-10% opinion", "Lift top-10% disclosure"],
        "ext_chart4": "Chart 4  Real-event AUC: modified opinion vs disclosure violation (0.5 = chance)",
        "ext_note4": "The Beneish proxy reaches only 0.405 AUC on real modified opinions — below chance; the proxy benchmark points the wrong way.",
        "ext_head3": ["Feature set", "Logit AUC op.", "Logit Δ op.", "HGB AUC op.", "HGB Δ op.",
                      "Logit AUC disc.", "Logit Δ disc.", "HGB AUC disc.", "HGB Δ disc."],
        "ext_delta_short": {"mod_opinion": "Opinion (narrow)", "mod_opinion_wide": "Opinion (wide)",
                            "violation_any_t1": "Violation (any)", "violation_disclosure_t1": "Violation (disclosure)"},
        "ext_delta_sep": " · ",
        "ext_hd": ["Combination", "ΔAUC (fused − finance)"],
        "ext_chart5": "Chart 5  Supervised ΔAUC (fused − finance, 8 combinations; positive = increment)",
        "ext_note5": ("Company-grouped 5-fold cross-validation (StratifiedGroupKFold; no same-company leakage). All eight "
                      "ΔAUC values are positive and five bootstrap intervals exclude 0: the text block adds a small but "
                      "consistent complementary increment on real events, while text alone is weaker than finance."),
        "ver_title": "§5.6 From the first to the second specification: design changes and result differences",
        "ver_sub": ("The changes make the null result more credible rather than flipping it. First-version data and code are "
                    "kept in archive_v0.1 and git tag v0.1-baseline."),
        "ver_head": ["Design choice", "First v0.1", "Second v0.2"],
        "ver_rows": [
            ["Sentiment lexicon", "Bootstrap (38 pos / 33 neg)", "Yao et al. (2021) full lexicon (3,585 pos / 1,633 neg)"],
            ["Uncertainty list", "Bootstrap 23 terms", "Expanded ~100 terms"],
            ["Matching", "Substring counting ('不' matches '不错')", "Exact jieba token match (user dictionary, 5,218 terms)"],
            ["Evaluation benchmark", "M > −1.78 only (flags 62.8%)", "Dual: legacy + sample top decile (M > 16.52)"],
            ["Text ρ (vs M-Score)", "−0.030", "−0.029 (conclusion unchanged)"],
            ["Fused ρ (vs M-Score)", "0.103", "0.103"],
            ["Text top-10% enrichment (calibrated)", "1.069", "0.848 (now below 1)"],
            ["Conclusion", "Null: text adds nothing", "Null is harder: unchanged under an 8.3× denser lexicon"],
        ],
        "ver_head2": ["Metric", "v0.1 hits per 1k tokens", "v0.2 hits per 1k tokens", "Ratio"],
        "ver_chart6": "Chart 6  Lexicon hit density: v0.1 → v0.2 (same MD&A texts)",
        "ver_note": ("Computed on 200 MD&A reports from 2021 (1.756m tokens): sentiment hits 13.4 → 111.3 per 1,000 tokens "
                     "(8.3×). The null result is not an artefact of a sparse dictionary."),
        "notes_title": "Definitions, data sources and reproduction",
        "notes_head": ["Item", "Description"],
        "notes_rows": [
            ["Data source", "Eight CSVs under outputs/tables/ plus data/processed/event_table.json; the same source as the paper (shared with build_section5.py)."],
            ["Sample", "n = 8,140 firm-years / 3,265 firms, 2021–2023, Chinese A-share manufacturing; the subset with all 9 features and the M-Score (10,172 in the frame)."],
            ["RQ1 benchmarks", "legacy = M > −1.78; calibrated = top-decile M (q90 = 16.52). Enrichment = queue event rate ÷ full-sample event rate."],
            ["External-validation definitions", "Narrow modified opinion = qualified / disclaimer / adverse (188, 2.31%); wide adds emphasis-of-matter (327, 4.02%). Audit opinions are contemporaneous (detection); t+1 disclosure violations are forward-looking (prediction)."],
            ["Supervised evaluation", "Logit and HistGradientBoosting, SimpleImputer + standardisation, company-grouped 5-fold cross-validation to prevent leakage; ΔAUC via paired bootstrap (400 draws)."],
            ["Honesty boundary", "Text alone is weaker than finance on every real event; the fused increment is small but consistent (5/8 intervals exclude 0). Do not write 'text is strong' or 'fraud detected' — the professor asks for honest reporting."],
            ["Regenerate", ".venv\\Scripts\\python.exe scripts\\build_results_excel.py --lang en"],
            ["Companion files", "outputs/reports/experiment_summary.md, v02_results_diff.md, outputs/branches/*.md"],
        ],
    },
}


# ---- data loading ----------------------------------------------------------
def load_csv(name: str) -> list[dict[str, str]]:
    path = TABLES / name
    if not path.exists():
        raise FileNotFoundError(f"required table missing: {path}")
    with path.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def load_metrics() -> dict[str, dict[str, list[dict]]]:
    data: dict[str, list[dict]] = {}
    for name in (
        "model_metrics",
        "topk_metrics",
        "shap_group_contributions",
        "shap_global",
        "ranking_overlap",
        "lexicon_density",
        "event_ranking_metrics",
        "event_supervised_metrics",
    ):
        data[name] = load_csv(f"{name}.csv")
    return data


def load_event_summary() -> dict:
    return json.loads(EVENT_JSON.read_text(encoding="utf-8"))


def load_top1() -> dict[str, str]:
    """First-ranked firm by the fused Isolation Forest score."""
    rows = load_csv("anomaly_scores.csv")
    rows.sort(key=lambda r: -float(r.get("if_fused", 0.0)))
    top = dict(rows[0])
    top["symbol"] = str(top["symbol"]).zfill(6)
    return top


# ---- formatting helpers ----------------------------------------------------
def f3(value: float) -> float:
    return round(value, 3)


def f_pct(value: float) -> float:
    return round(value, 4)


def num(value: str | None, digits: int = 3) -> float:
    try:
        return round(float(value), digits)
    except (TypeError, ValueError):
        return float("nan")


# ---- styles ----------------------------------------------------------------
def style_title(ws, cell: str, text: str) -> None:
    ws[cell] = text
    ws[cell].font = Font(name=CURRENT["font"], size=14, bold=True, color=INK)
    ws[cell].alignment = Alignment(vertical="center")


def style_subtitle(ws, cell: str, text: str) -> None:
    ws[cell] = text
    ws[cell].font = Font(name=CURRENT["font"], size=10, color=MUTED)
    ws[cell].alignment = Alignment(vertical="center", wrap_text=True)


def style_note(ws, cell: str, text: str) -> None:
    ws[cell] = text
    ws[cell].font = Font(name=CURRENT["font"], size=9, color=MUTED)
    ws[cell].alignment = Alignment(vertical="center", wrap_text=True)


def write_table(ws, start_row: int, start_col: int, header: list[str], rows: list[list],
                *, number_fmt: str | list[str | None] | None = None,
                widths: list[int] | None = None) -> int:
    """Write a bordered table; returns the row after the last data row.

    ``number_fmt`` is a single format applied to every numeric cell, or a
    per-column list of formats (``None`` entries keep the default).
    """
    for j, text in enumerate(header):
        cell = ws.cell(row=start_row, column=start_col + j, value=text)
        cell.font = Font(name=CURRENT["font"], size=10, bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor=PRIMARY)
        cell.border = BOX
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    r = start_row + 1
    for i, row in enumerate(rows):
        for j, value in enumerate(row):
            cell = ws.cell(row=r, column=start_col + j, value=value)
            cell.border = BOX
            cell.font = Font(name=CURRENT["font"], size=10, color=INK)
            cell.alignment = Alignment(
                horizontal="center" if j else "left",
                vertical="center",
                wrap_text=bool(j == 0),
            )
            if number_fmt and j > 0 and isinstance(value, (int, float)):
                fmt = number_fmt[j - 1] if isinstance(number_fmt, list) else number_fmt
                if fmt:
                    cell.number_format = fmt
            if i % 2:
                cell.fill = PatternFill("solid", fgColor=BG)
        r += 1
    if widths:
        for j, w in enumerate(widths):
            ws.column_dimensions[get_column_letter(start_col + j)].width = w
    return r


def add_bar(ws, anchor: str, *, cats: Reference, data: Reference, title: str,
            y_title: str | None = None, horizontal: bool = False,
            series_gap: int | None = None) -> BarChart:
    chart = BarChart()
    chart.type = "bar" if horizontal else "col"
    chart.grouping = "clustered"
    chart.style = 10
    chart.title = title
    if y_title:
        if horizontal:
            chart.x_axis.title = y_title
        else:
            chart.y_axis.title = y_title
    chart.legend.position = "b"
    chart.add_data(data, titles_from_data=True)
    chart.set_categories(cats)
    chart.width = 15
    chart.height = 8
    if series_gap:
        chart.gapWidth = series_gap
    ws.add_chart(chart, anchor)
    return chart


def add_pie(ws, anchor: str, *, cats: Reference, data: Reference, title: str) -> PieChart:
    chart = PieChart()
    chart.title = title
    chart.add_data(data, titles_from_data=True)
    chart.set_categories(cats)
    from openpyxl.chart.label import DataLabelList
    chart.dataLabels = DataLabelList()
    chart.dataLabels.showPercent = True
    chart.width = 11
    chart.height = 8
    ws.add_chart(chart, anchor)
    return chart


def new_sheet(wb: Workbook, name: str) -> tuple:
    ws = wb.create_sheet(name)
    ws.sheet_view.showGridLines = False
    ws.sheet_properties.tabColor = PRIMARY
    for col, width in (("A", 2), ("B", 26), ("C", 14), ("D", 14), ("E", 14),
                       ("F", 14), ("G", 14), ("H", 14), ("I", 14), ("J", 14)):
        ws.column_dimensions[col].width = width
    return ws


# ---- sheets ----------------------------------------------------------------
def sheet_overview(wb: Workbook, m: dict[str, list[dict]], events: dict, top1: dict) -> None:
    ws = new_sheet(wb, SHEET_NAMES[CURRENT["lang"]][0])
    style_title(ws, "B2", T("ov_title"))
    style_subtitle(ws, "B3", T("ov_sub").format(stamp=f"{datetime.now():%Y-%m-%d %H:%M}"))

    metric = {(r["model"]): r for r in m["model_metrics"]}
    topk = {(r["benchmark"], r["model"], r["k"]): r for r in m["topk_metrics"]}
    shap = {r["group"]: r for r in m["shap_group_contributions"]}
    rank = {(r["label"], r["model"]): r for r in m["event_ranking_metrics"]}

    metric_rows = {
        "cn": [
            ["有效样本 / 公司数", "8,140 / 3,265", "§5.1 Table 5.1"],
            ["Spearman ρ（仅财务 / 仅文本 / 融合 / 自编码器）",
             "0.136*** / −0.029** / 0.103*** / 0.009", "§5.3 Table 5.2"],
            ["top-10% 富集率，样本校准口径（仅财务 / 融合）",
             f"{num(topk[('calibrated','if_finance','0.1')]['enrichment']):.2f}× / "
             f"{num(topk[('calibrated','if_fused','0.1')]['enrichment']):.2f}×", "§5.3 Table 5.3"],
            ["top-10% 富集率，legacy 口径 M > −1.78（仅财务 / 融合）",
             f"{num(topk[('legacy','if_finance','0.1')]['enrichment']):.2f}× / "
             f"{num(topk[('legacy','if_fused','0.1')]['enrichment']):.2f}×", "§5.3 Table 5.3"],
            ["SHAP 组贡献（财务 / 文本）",
             f"{num(shap['finance']['abs_shap_share'])*100:.1f}% / "
             f"{num(shap['text']['abs_shap_share'])*100:.1f}%", "§5.4"],
            ["外部检验：非标审计意见 AUC（仅财务 / Beneish 代理）",
             f"{num(rank[('mod_opinion','finance-only IF')]['auc']):.3f} / "
             f"{num(rank[('mod_opinion','Beneish M-Score')]['auc']):.3f}", "§5.7 Table 5.5"],
            ["外部检验：非标意见 top-10% 富集（仅财务）",
             f"{num(rank[('mod_opinion','finance-only IF')]['lift_10pct']):.2f}×", "§5.7 Table 5.5"],
            ["监督式 ΔAUC（融合 − 仅财务，8 个组合）",
             "+0.006 ~ +0.026（5/8 置信区间不含 0）", "§5.7 Table 5.6"],
            ["审查第一名（融合分数）",
             f"{top1['symbol']}（{top1.get('fiscal_year','')}，{top1.get('industry_code_d','C42')}）分数 "
             f"{num(top1.get('if_fused')):.3f}，M-Score {num(top1.get('m_score'),1):,.1f}", "§5.4"],
        ],
        "en": [
            ["Usable sample / firms", "8,140 / 3,265", "§5.1 Table 5.1"],
            ["Spearman ρ (finance / text / fused / autoencoder)",
             "0.136*** / −0.029** / 0.103*** / 0.009", "§5.3 Table 5.2"],
            ["Top-10% enrichment, calibrated (finance / fused)",
             f"{num(topk[('calibrated','if_finance','0.1')]['enrichment']):.2f}× / "
             f"{num(topk[('calibrated','if_fused','0.1')]['enrichment']):.2f}×", "§5.3 Table 5.3"],
            ["Top-10% enrichment, legacy M > −1.78 (finance / fused)",
             f"{num(topk[('legacy','if_finance','0.1')]['enrichment']):.2f}× / "
             f"{num(topk[('legacy','if_fused','0.1')]['enrichment']):.2f}×", "§5.3 Table 5.3"],
            ["SHAP group share (finance / text)",
             f"{num(shap['finance']['abs_shap_share'])*100:.1f}% / "
             f"{num(shap['text']['abs_shap_share'])*100:.1f}%", "§5.4"],
            ["External: modified-opinion AUC (finance-only / Beneish proxy)",
             f"{num(rank[('mod_opinion','finance-only IF')]['auc']):.3f} / "
             f"{num(rank[('mod_opinion','Beneish M-Score')]['auc']):.3f}", "§5.7 Table 5.5"],
            ["External: modified-opinion top-10% lift (finance-only)",
             f"{num(rank[('mod_opinion','finance-only IF')]['lift_10pct']):.2f}×", "§5.7 Table 5.5"],
            ["Supervised ΔAUC (fused − finance, 8 combinations)",
             "+0.006 ~ +0.026 (5/8 CIs exclude 0)", "§5.7 Table 5.6"],
            ["Top case under review (fused score)",
             f"{top1['symbol']} ({top1.get('fiscal_year','')}, {top1.get('industry_code_d','C42')}) score "
             f"{num(top1.get('if_fused')):.3f}, M-Score {num(top1.get('m_score'),1):,.1f}", "§5.4"],
        ],
    }
    write_table(ws, 5, 2, T("ov_head"), metric_rows[CURRENT["lang"]], widths=[44, 34, 22])

    style_title(ws, "B16", T("ov_concl_title"))
    style_subtitle(ws, "B17", T("ov_concl"))
    ws.merge_cells("B17:J19")
    ws["B17"].alignment = Alignment(wrap_text=True, vertical="top")
    for rr in (16,):
        for cc in range(2, 10):
            ws.cell(row=rr, column=cc).fill = PatternFill("solid", fgColor=LIGHT_BLUE)
    ws.merge_cells("B16:J16")

    style_title(ws, "B21", T("ov_nav_title"))
    nav = T("ov_nav")
    write_table(ws, 22, 2, nav[0], nav[1:], widths=[26, 46, 30])


def sheet_rq1(wb: Workbook, m: dict[str, list[dict]]) -> None:
    ws = new_sheet(wb, SHEET_NAMES[CURRENT["lang"]][1])
    style_title(ws, "B2", T("rq1_title"))
    style_subtitle(ws, "B3", T("rq1_sub"))

    metric = {r["model"]: r for r in m["model_metrics"]}
    topk = {(r["benchmark"], r["model"], r["k"]): r for r in m["topk_metrics"]}

    head = T("rq1_head")
    rows = [
        [L(MODEL_LABELS)[k], num(v["spearman_rho"]), v["spearman_p"]]
        for k, v in [
            ("if_finance", metric["if_finance"]),
            ("if_text", metric["if_text"]),
            ("if_fused", metric["if_fused"]),
            ("ae_fused", metric["ae_fused"]),
        ]
    ]
    # p-values readable
    p_fmt = {"if_finance": "< 0.001", "if_text": "0.008", "if_fused": "< 0.001", "ae_fused": "0.409"}
    for row, key in zip(rows, p_fmt):
        row[2] = p_fmt[key]
    write_table(ws, 5, 2, head, rows, number_fmt="0.000", widths=[30, 14, 12])

    r0 = 12
    head2 = T("rq1_head2")
    rows2 = []
    for key in ("if_finance", "if_text", "if_fused", "ae_fused"):
        rows2.append([
            L(MODEL_LABELS)[key],
            num(topk[("legacy", key, "0.1")]["enrichment"]),
            num(topk[("calibrated", key, "0.1")]["enrichment"]),
            num(topk[("calibrated", key, "0.05")]["enrichment"]),
            num(topk[("calibrated", key, "0.15")]["enrichment"]),
        ])
    write_table(ws, r0, 2, head2, rows2, number_fmt="0.00", widths=[30, 19, 17, 17, 17])
    style_note(ws, f"B{r0+5}", T("rq1_note"))

    cats = Reference(ws, min_col=2, min_row=r0 + 1, max_row=r0 + 4)
    data = Reference(ws, min_col=3, max_col=4, min_row=r0, max_row=r0 + 4)
    chart = add_bar(ws, "G5", cats=cats, data=data,
                    title=T("rq1_chart"), y_title=T("rq1_y"))
    chart.y_axis.majorGridlines = None


def sheet_rq2(wb: Workbook, m: dict[str, list[dict]]) -> None:
    ws = new_sheet(wb, SHEET_NAMES[CURRENT["lang"]][2])
    style_title(ws, "B2", T("rq2_title"))
    style_subtitle(ws, "B3", T("rq2_sub"))

    groups = {r["group"]: r for r in m["shap_group_contributions"]}
    head = T("rq2_head")
    rows = [
        ["Finance", int(groups["finance"]["n_features"]),
         f_pct(num(groups["finance"]["abs_shap_share"]))],
        ["Text", int(groups["text"]["n_features"]),
         f_pct(num(groups["text"]["abs_shap_share"]))],
    ]
    write_table(ws, 5, 2, head, rows,
                number_fmt=[None, None, "0.0%"], widths=[24, 10, 16])

    cats = Reference(ws, min_col=2, min_row=6, max_row=7)
    data = Reference(ws, min_col=4, min_row=5, max_row=7)
    add_pie(ws, "G5", cats=cats, data=data, title=T("rq2_pie"))

    r1 = 12
    head2 = T("rq2_head2")
    rows2 = [[L(FEATURE_LABELS).get(r["feature"], r["feature"]), num(r["mean_abs_shap"])]
             for r in m["shap_global"]]
    write_table(ws, r1, 2, head2, rows2, number_fmt="0.000", widths=[30, 14])

    cats2 = Reference(ws, min_col=2, min_row=r1 + 1, max_row=r1 + len(rows2))
    data2 = Reference(ws, min_col=3, min_row=r1, max_row=r1 + len(rows2))
    add_bar(ws, "F20", cats=cats2, data=data2,
            title=T("rq2_chart3"), horizontal=True)
    style_note(ws, f"B{r1+len(rows2)+2}", T("rq2_note"))


def sheet_rq3(wb: Workbook, m: dict[str, list[dict]]) -> None:
    ws = new_sheet(wb, SHEET_NAMES[CURRENT["lang"]][3])
    style_title(ws, "B2", T("rq3_title"))
    style_subtitle(ws, "B3", T("rq3_sub"))

    keys = ("if_finance", "if_text", "if_fused", "ae_fused")
    ov = {(r["model_a"], r["model_b"]): num(r["top10_overlap"]) for r in m["ranking_overlap"]}
    head = [T("rq3_head")[0], *[L(MODEL_LABELS)[k] for k in keys]]
    rows = []
    for a in keys:
        rows.append([L(MODEL_LABELS)[a]] + [ov[(a, b)] for b in keys])
    write_table(ws, 5, 2, head, rows, number_fmt="0.000", widths=[30, 16, 16, 16, 16])
    style_note(ws, "B11", T("rq3_note"))
    ws.merge_cells("B11:J12")
    ws["B11"].alignment = Alignment(wrap_text=True, vertical="top")

    style_title(ws, "B14", T("rq3_year_title"))
    head2 = T("rq3_year_head")
    rows2 = [
        ["Finance-only IF", 0.103, 0.130, 0.173],
        ["Text-only IF", -0.036, -0.039, -0.016],
        ["Fused IF", 0.073, 0.092, 0.141],
        ["Fused AE", -0.019, 0.026, 0.001],
    ]
    write_table(ws, 15, 2, head2, rows2, number_fmt="0.000", widths=[30, 12, 12, 12])
    style_note(ws, "B20", T("rq3_year_note"))


def sheet_external(wb: Workbook, m: dict[str, list[dict]], events: dict) -> None:
    ws = new_sheet(wb, SHEET_NAMES[CURRENT["lang"]][4])
    style_title(ws, "B2", T("ext_title"))
    style_subtitle(ws, "B3", T("ext_sub"))

    head = T("ext_head")
    rows = []
    by_year = events["by_year"]
    for key, count_k, rate_k in (
        ("mod_opinion", "mod_opinion_count", "mod_opinion_rate"),
        ("mod_opinion_wide", "mod_opinion_wide_count", "mod_opinion_wide_rate"),
        ("violation_any_t1", "violation_any_t1_count", "violation_any_t1_rate"),
        ("violation_disclosure_t1", "violation_disclosure_t1_count", "violation_disclosure_t1_rate"),
    ):
        rows.append([
            L(EVENT_LABELS)[key], int(events[count_k]), f_pct(events[rate_k]),
            f_pct(by_year["2021"][key]), f_pct(by_year["2022"][key]), f_pct(by_year["2023"][key]),
        ])
    write_table(ws, 5, 2, head, rows,
                number_fmt=[None, None, "0.0%", "0.0%", "0.0%", "0.0%"],
                widths=[30, 10, 11, 10, 10, 10])

    r1 = 12
    rank = {(r["label"], r["model"]): r for r in m["event_ranking_metrics"]}
    head2 = T("ext_head2")
    rows2 = []
    for key in ("finance-only IF", "text-only IF", "fused IF", "fused AE", "Beneish M-Score"):
        a = rank[("mod_opinion", key)]
        b = rank[("violation_disclosure_t1", key)]
        rows2.append([
            L(SCORE_LABELS)[key], num(a["auc"]), num(b["auc"]), num(a["lift_10pct"]), num(b["lift_10pct"]),
        ])
    write_table(ws, r1, 2, head2, rows2,
                number_fmt=[None, "0.000", "0.000", "0.00", "0.00"],
                widths=[30, 15, 15, 13, 13])

    cats = Reference(ws, min_col=2, min_row=r1 + 1, max_row=r1 + 5)
    data = Reference(ws, min_col=3, max_col=4, min_row=r1, max_row=r1 + 5)
    add_bar(ws, "L5", cats=cats, data=data, title=T("ext_chart4"))
    style_note(ws, "L19", T("ext_note4"))
    ws.merge_cells("L19:N20")

    r2 = 19
    sup = m["event_supervised_metrics"]
    by_key = {(r["label"], r["model"], r["feature_set"]): r for r in sup}
    head3 = T("ext_head3")
    rows3 = []
    for fset, label in (("finance", L(FUSED_SET_LABELS)["finance"]),
                        ("text", L(FUSED_SET_LABELS)["text"]),
                        ("fused", L(FUSED_SET_LABELS)["fused"])):
        auc_mo_l = num(by_key[("mod_opinion", "logit", fset)]["oof_auc"])
        auc_mo_h = num(by_key[("mod_opinion", "hgb", fset)]["oof_auc"])
        auc_disc_l = num(by_key[("violation_disclosure_t1", "logit", fset)]["oof_auc"])
        auc_disc_h = num(by_key[("violation_disclosure_t1", "hgb", fset)]["oof_auc"])
        if fset == "finance":
            row = [label, auc_mo_l, "—", auc_mo_h, "—", auc_disc_l, "—", auc_disc_h, "—"]
        else:
            d_mo_l = num(by_key[("mod_opinion", "logit", f"delta_{fset}_vs_finance")]["oof_auc"])
            d_mo_h = num(by_key[("mod_opinion", "hgb", f"delta_{fset}_vs_finance")]["oof_auc"])
            d_disc_l = num(by_key[("violation_disclosure_t1", "logit", f"delta_{fset}_vs_finance")]["oof_auc"])
            d_disc_h = num(by_key[("violation_disclosure_t1", "hgb", f"delta_{fset}_vs_finance")]["oof_auc"])
            row = [label, auc_mo_l, d_mo_l, auc_mo_h, d_mo_h, auc_disc_l, d_disc_l, auc_disc_h, d_disc_h]
        rows3.append(row)
    write_table(ws, r2, 2, head3, rows3,
                number_fmt=[None, "0.000", "0.000", "0.000", "0.000",
                            "0.000", "0.000", "0.000", "0.000"],
                widths=[20, 13, 13, 13, 13, 13, 13, 13, 13])

    # chart 5: delta fused vs finance across 8 label x model combinations
    delta_short = T("ext_delta_short")
    deltas: list[tuple[str, float]] = []
    for label_key in ("mod_opinion", "mod_opinion_wide", "violation_any_t1", "violation_disclosure_t1"):
        for model in ("logit", "hgb"):
            d = by_key[(label_key, model, "delta_fused_vs_finance")]
            deltas.append(
                (f"{delta_short[label_key]}{T('ext_delta_sep')}{L(SUPERVISED_SHORT)[model]}",
                 num(d["oof_auc"]))
            )
    hd = T("ext_hd")
    wr = write_table(ws, r2 + 6, 2, hd, [list(t) for t in deltas],
                     number_fmt="0.000", widths=[34, 18])
    cats5 = Reference(ws, min_col=2, min_row=r2 + 7, max_row=r2 + 14)
    data5 = Reference(ws, min_col=3, min_row=r2 + 6, max_row=r2 + 14)
    chart5 = add_bar(ws, "K20", cats=cats5, data=data5, title=T("ext_chart5"))
    chart5.width = 16
    style_note(ws, f"B{wr+1}", T("ext_note5"))


def sheet_versions(wb: Workbook, m: dict[str, list[dict]]) -> None:
    ws = new_sheet(wb, SHEET_NAMES[CURRENT["lang"]][5])
    style_title(ws, "B2", T("ver_title"))
    style_subtitle(ws, "B3", T("ver_sub"))

    write_table(ws, 5, 2, T("ver_head"), T("ver_rows"), widths=[30, 34, 40])

    r1 = 16
    head2 = T("ver_head2")
    rows2 = [
        [L(LEXICON_LABELS)[r["metric"]], num(r["v01_per_1000"], 2), num(r["v02_per_1000"], 2),
         num(r["ratio"], 2)]
        for r in m["lexicon_density"]
    ]
    write_table(ws, r1, 2, head2, rows2, number_fmt="0.00", widths=[22, 18, 18, 10])

    cats = Reference(ws, min_col=2, min_row=r1 + 1, max_row=r1 + 4)
    data = Reference(ws, min_col=3, max_col=4, min_row=r1, max_row=r1 + 4)
    add_bar(ws, "H5", cats=cats, data=data, title=T("ver_chart6"))
    style_note(ws, f"B{r1+6}", T("ver_note"))


def sheet_notes(wb: Workbook) -> None:
    ws = new_sheet(wb, SHEET_NAMES[CURRENT["lang"]][6])
    style_title(ws, "B2", T("notes_title"))
    rows = T("notes_rows")
    write_table(ws, 5, 2, T("notes_head"), rows, widths=[18, 92])
    for rr in range(6, 6 + len(rows)):
        ws.cell(row=rr, column=3).alignment = Alignment(wrap_text=True, vertical="top")
        ws.row_dimensions[rr].height = 30


# ---- entry point -----------------------------------------------------------
def build(out: Path, lang: str = "cn") -> Workbook:
    set_lang(lang)
    m = load_metrics()
    events = load_event_summary()
    top1 = load_top1()

    wb = Workbook()
    wb.remove(wb.active)
    sheet_overview(wb, m, events, top1)
    sheet_rq1(wb, m)
    sheet_rq2(wb, m)
    sheet_rq3(wb, m)
    sheet_external(wb, m, events)
    sheet_versions(wb, m)
    sheet_notes(wb)
    wb.save(out)
    return wb


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lang", choices=("cn", "en"), default="cn",
                        help="workbook language (default: cn)")
    parser.add_argument("--out", default=None, help="output .xlsx path")
    args = parser.parse_args()
    out = Path(args.out) if args.out else (DEFAULT_OUT_EN if args.lang == "en" else DEFAULT_OUT)
    try:
        build(out, lang=args.lang)
    except FileNotFoundError as exc:
        print(f"missing input: {exc}", file=sys.stderr)
        return 2
    print(f"written: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
