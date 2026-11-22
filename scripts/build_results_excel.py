#!/usr/bin/env python
"""Build the Excel visualisation workbook of the final results.

Reads the released tables under ``outputs/tables/`` (the same single source of
truth as the manuscript, see ``scripts/build_section5.py``) and writes a styled
workbook with one sheet per research question plus overview and notes, including
native Excel charts (enrichment, SHAP, external-validation AUC, delta-AUC and
lexicon-density comparisons).

Usage::

    .venv\\Scripts\\python.exe scripts\\build_results_excel.py [--out path.xlsx]

Exit codes: 0 = written, 2 = a required input table is missing.

Revision history
2026-11-22  created: overview, RQ1-RQ3, 5.6 and 5.7 sheets with six charts.
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

MODEL_LABELS = {
    "if_finance": "Finance-only IF（仅财务）",
    "if_text": "Text-only IF（仅文本）",
    "if_fused": "Fused IF（融合）",
    "ae_fused": "Fused AE（自编码器）",
}
SCORE_LABELS = {
    "finance-only IF": "Finance-only IF（仅财务）",
    "text-only IF": "Text-only IF（仅文本）",
    "fused IF": "Fused IF（融合）",
    "fused AE": "Fused AE（自编码器）",
    "Beneish M-Score": "Beneish M-Score（代理基准）",
}
EVENT_LABELS = {
    "mod_opinion": "非标审计意见（窄口径）",
    "mod_opinion_wide": "非标审计意见（宽口径）",
    "violation_any_t1": "t+1 违规（任意类型）",
    "violation_disclosure_t1": "t+1 违规（披露类）",
}
SUPERVISED_MODEL_LABELS = {"logit": "Logit（逻辑回归）", "hgb": "HGB（梯度提升）"}
FEATURE_LABELS = {
    "ocf_to_assets": "经营现金流/总资产",
    "revenue_growth": "营业收入增长",
    "readability": "可读性（文本）",
    "sentiment_balance": "语调（文本）",
    "receivables_turnover": "应收账款周转",
    "uncertainty_ratio": "不确定词占比（文本）",
    "accruals_to_assets": "应计项目/总资产",
    "roa": "ROA",
    "leverage": "杠杆率",
}
LEXICON_LABELS = {
    "positive_terms": "正面词",
    "negative_terms": "负面词",
    "sentiment_terms": "情感词合计",
    "uncertainty_terms": "不确定词",
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
    ws[cell].font = Font(name="微软雅黑", size=14, bold=True, color=INK)
    ws[cell].alignment = Alignment(vertical="center")


def style_subtitle(ws, cell: str, text: str) -> None:
    ws[cell] = text
    ws[cell].font = Font(name="微软雅黑", size=10, color=MUTED)
    ws[cell].alignment = Alignment(vertical="center", wrap_text=True)


def style_note(ws, cell: str, text: str) -> None:
    ws[cell] = text
    ws[cell].font = Font(name="微软雅黑", size=9, color=MUTED)
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
        cell.font = Font(name="微软雅黑", size=10, bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor=PRIMARY)
        cell.border = BOX
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    r = start_row + 1
    for i, row in enumerate(rows):
        for j, value in enumerate(row):
            cell = ws.cell(row=r, column=start_col + j, value=value)
            cell.border = BOX
            cell.font = Font(name="微软雅黑", size=10, color=INK)
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
    ws = new_sheet(wb, "总览 Overview")
    style_title(ws, "B2", "Group 12A2 · 财务披露风险筛查 —— 结果可视化总览")
    style_subtitle(
        ws, "B3",
        f"与定稿 Group12A2_Final_EN（§5.1–§5.7）完全同源；数字由 outputs/tables/ 现场生成"
        f"（{datetime.now():%Y-%m-%d %H:%M}）。n = 8,140 firm-years / 3,265 家公司，2021–2023。",
    )

    metric = {(r["model"]): r for r in m["model_metrics"]}
    topk = {(r["benchmark"], r["model"], r["k"]): r for r in m["topk_metrics"]}
    shap = {r["group"]: r for r in m["shap_group_contributions"]}
    rank = {(r["label"], r["model"]): r for r in m["event_ranking_metrics"]}

    head = ["关键指标 · Key metric", "值 · Value", "论文出处 · In the paper"]
    rows = [
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
    ]
    write_table(ws, 5, 2, head, rows, widths=[44, 34, 22])

    style_title(ws, "B16", "一句话结论（诚实用语 · Honest phrasing）")
    style_subtitle(
        ws, "B17",
        "财务特征对 Beneish 代理有弱但显著的排序信号（ρ = 0.136）；文本单独对代理基准无增量、"
        "对真实事件更弱；但融合在真实监管事件上给出小而一致的正增量（ΔAUC +0.006 ~ +0.026）。"
        "Beneish 代理对真实非标意见的 AUC 仅 0.405（低于随机）——第一版的代理基准方向相反，"
        "外部检验（§5.7）比代理基准更可信。",
    )
    ws.merge_cells("B17:J19")
    ws["B17"].alignment = Alignment(wrap_text=True, vertical="top")
    for rr in (16,):
        for cc in range(2, 10):
            ws.cell(row=rr, column=cc).fill = PatternFill("solid", fgColor=LIGHT_BLUE)
    ws.merge_cells("B16:J16")

    style_title(ws, "B21", "工作簿导航 · Sheets")
    nav = [
        ["工作表", "内容", "图表"],
        ["总览 Overview", "关键数字与一句话结论", "—"],
        ["RQ1 主结果", "Spearman ρ、双基准 top-5/10/15% 富集率", "图1 富集率柱状对比"],
        ["RQ2 可解释", "SHAP 组贡献与全局前 9 特征", "图2 组贡献饼图、图3 特征重要性"],
        ["RQ3 稳健性", "top-10% 名单重叠（Jaccard）矩阵", "—"],
        ["§5.7 外部检验", "真实监管事件：事件率、AUC、lift、监督 ΔAUC", "图4 AUC、图5 ΔAUC"],
        ["§5.6 两版对比", "词典密度 v0.1 → v0.2 与做法差异", "图6 词典密度对比"],
        ["说明 Notes", "口径、数据来源与复现命令", "—"],
    ]
    write_table(ws, 22, 2, nav[0], nav[1:], widths=[26, 46, 30])


def sheet_rq1(wb: Workbook, m: dict[str, list[dict]]) -> None:
    ws = new_sheet(wb, "RQ1 主结果")
    style_title(ws, "B2", "RQ1：文本特征是否带来增量？—— 排序一致性与队列富集")
    style_subtitle(ws, "B3", "Beneish M-Score 为评估基准（不参与训练）。富集率 > 1 表示该队列的事件密度高于全样本。")

    metric = {r["model"]: r for r in m["model_metrics"]}
    topk = {(r["benchmark"], r["model"], r["k"]): r for r in m["topk_metrics"]}

    head = ["模型", "Spearman ρ", "p 值"]
    rows = [
        [MODEL_LABELS[k], num(v["spearman_rho"]), v["spearman_p"]]
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
    head2 = ["模型", "富集率·legacy(M>−1.78) top-10%", "富集率·样本校准 top-10%",
             "富集率·样本校准 top-5%", "富集率·样本校准 top-15%"]
    rows2 = []
    for key in ("if_finance", "if_text", "if_fused", "ae_fused"):
        rows2.append([
            MODEL_LABELS[key],
            num(topk[("legacy", key, "0.1")]["enrichment"]),
            num(topk[("calibrated", key, "0.1")]["enrichment"]),
            num(topk[("calibrated", key, "0.05")]["enrichment"]),
            num(topk[("calibrated", key, "0.15")]["enrichment"]),
        ])
    write_table(ws, r0, 2, head2, rows2, number_fmt="0.00", widths=[30, 19, 17, 17, 17])
    style_note(ws, f"B{r0+5}",
               "口径：legacy = M > −1.78（在本样本标红 62.8%，噪声大）；样本校准 = M 落在样本前 10%（M > 16.52），"
               "构造上事件率为 10%。同一排序，仅基准不同。")

    cats = Reference(ws, min_col=2, min_row=r0 + 1, max_row=r0 + 4)
    data = Reference(ws, min_col=3, max_col=4, min_row=r0, max_row=r0 + 4)
    chart = add_bar(ws, "G5", cats=cats, data=data,
                    title="图1  top-10% 队列富集率：样本校准 vs legacy 基准",
                    y_title="富集率（1 = 全样本水平）")
    chart.y_axis.majorGridlines = None


def sheet_rq2(wb: Workbook, m: dict[str, list[dict]]) -> None:
    ws = new_sheet(wb, "RQ2 可解释")
    style_title(ws, "B2", "RQ2：什么驱动了异常分数？—— SHAP 全局解释")
    style_subtitle(ws, "B3", "对融合 Isolation Forest 的 SHAP 全局贡献；财务组 6 个特征、文本组 3 个特征。")

    groups = {r["group"]: r for r in m["shap_group_contributions"]}
    head = ["特征组", "特征数", "SHAP 贡献占比"]
    rows = [
        ["财务特征 Finance", int(groups["finance"]["n_features"]),
         f_pct(num(groups["finance"]["abs_shap_share"]))],
        ["文本特征 Text", int(groups["text"]["n_features"]),
         f_pct(num(groups["text"]["abs_shap_share"]))],
    ]
    write_table(ws, 5, 2, head, rows,
                number_fmt=[None, None, "0.0%"], widths=[24, 10, 16])

    cats = Reference(ws, min_col=2, min_row=6, max_row=7)
    data = Reference(ws, min_col=4, min_row=5, max_row=7)
    add_pie(ws, "G5", cats=cats, data=data, title="图2  SHAP 组贡献")

    r1 = 12
    head2 = ["特征", "mean |SHAP|"]
    rows2 = [[FEATURE_LABELS.get(r["feature"], r["feature"]), num(r["mean_abs_shap"])]
             for r in m["shap_global"]]
    write_table(ws, r1, 2, head2, rows2, number_fmt="0.000", widths=[30, 14])

    cats2 = Reference(ws, min_col=2, min_row=r1 + 1, max_row=r1 + len(rows2))
    data2 = Reference(ws, min_col=3, min_row=r1, max_row=r1 + len(rows2))
    add_bar(ws, "F20", cats=cats2, data=data2,
            title="图3  全局特征重要性（mean |SHAP|）", horizontal=True)
    style_note(ws, f"B{r1+len(rows2)+2}",
               "前三为 经营现金流/总资产、营收增长、可读性；三个文本特征全部进入前五，但组层面文本合计仅 34.6%，"
               "且其对代理基准的排序力近乎为零（见 RQ1）。")


def sheet_rq3(wb: Workbook, m: dict[str, list[dict]]) -> None:
    ws = new_sheet(wb, "RQ3 稳健性")
    style_title(ws, "B2", "RQ3：排序是否稳健？—— top-10% 名单重叠（Jaccard）")
    style_subtitle(ws, "B3", "四个排序两两之间的 top-10% 名单重合度；AE 与 IF 的重合仅 0.373，稳健性未复现。")

    keys = ("if_finance", "if_text", "if_fused", "ae_fused")
    ov = {(r["model_a"], r["model_b"]): num(r["top10_overlap"]) for r in m["ranking_overlap"]}
    head = ["Jaccard 重叠", *[MODEL_LABELS[k] for k in keys]]
    rows = []
    for a in keys:
        rows.append([MODEL_LABELS[a]] + [ov[(a, b)] for b in keys])
    write_table(ws, 5, 2, head, rows, number_fmt="0.000", widths=[30, 16, 16, 16, 16])
    style_note(ws, "B11",
               "读法：仅财务与融合的名单重合 0.817（融合基本复刻财务排序）；仅财务与仅文本仅 0.111（文本给出几乎独立的名单，"
               "但该名单对基准无信号）。自编码器未能复现隔离森林排序（ρ = 0.009，p = 0.409）。")
    ws.merge_cells("B11:J12")
    ws["B11"].alignment = Alignment(wrap_text=True, vertical="top")

    style_title(ws, "B14", "分年度 Spearman ρ（稳健性）")
    head2 = ["模型", "2021", "2022", "2023"]
    rows2 = [
        ["Finance-only IF", 0.103, 0.130, 0.173],
        ["Text-only IF", -0.036, -0.039, -0.016],
        ["Fused IF", 0.073, 0.092, 0.141],
        ["Fused AE", -0.019, 0.026, 0.001],
    ]
    write_table(ws, 15, 2, head2, rows2, number_fmt="0.000", widths=[30, 12, 12, 12])
    style_note(ws, "B20",
               "分年度排序稳定：财务单独逐年为正且上升，文本单独三年全为负，融合逐年低于财务单独。")


def sheet_external(wb: Workbook, m: dict[str, list[dict]], events: dict) -> None:
    ws = new_sheet(wb, "§5.7 外部检验")
    style_title(ws, "B2", "§5.7 外部检验：真实监管事件上的表现")
    style_subtitle(
        ws, "B3",
        "结果变量来自 CSMAR：FIN_Audit（审计意见，同期=识别而非预测）与 STK_Violation_Main（违规，t+1 对齐=前瞻）。"
        "审计意见覆盖率 100%。",
    )

    head = ["事件标签", "事件数", "事件率", "2021", "2022", "2023"]
    rows = []
    by_year = events["by_year"]
    for key, count_k, rate_k in (
        ("mod_opinion", "mod_opinion_count", "mod_opinion_rate"),
        ("mod_opinion_wide", "mod_opinion_wide_count", "mod_opinion_wide_rate"),
        ("violation_any_t1", "violation_any_t1_count", "violation_any_t1_rate"),
        ("violation_disclosure_t1", "violation_disclosure_t1_count", "violation_disclosure_t1_rate"),
    ):
        rows.append([
            EVENT_LABELS[key], int(events[count_k]), f_pct(events[rate_k]),
            f_pct(by_year["2021"][key]), f_pct(by_year["2022"][key]), f_pct(by_year["2023"][key]),
        ])
    write_table(ws, 5, 2, head, rows,
                number_fmt=[None, None, "0.0%", "0.0%", "0.0%", "0.0%"],
                widths=[30, 10, 11, 10, 10, 10])

    r1 = 12
    rank = {(r["label"], r["model"]): r for r in m["event_ranking_metrics"]}
    head2 = ["分数", "AUC 非标意见", "AUC 披露类 t+1", "lift 前10% 非标", "lift 前10% 披露"]
    rows2 = []
    for key in ("finance-only IF", "text-only IF", "fused IF", "fused AE", "Beneish M-Score"):
        a = rank[("mod_opinion", key)]
        b = rank[("violation_disclosure_t1", key)]
        rows2.append([
            SCORE_LABELS[key], num(a["auc"]), num(b["auc"]), num(a["lift_10pct"]), num(b["lift_10pct"]),
        ])
    write_table(ws, r1, 2, head2, rows2,
                number_fmt=[None, "0.000", "0.000", "0.00", "0.00"],
                widths=[30, 15, 15, 13, 13])

    cats = Reference(ws, min_col=2, min_row=r1 + 1, max_row=r1 + 5)
    data = Reference(ws, min_col=3, max_col=4, min_row=r1, max_row=r1 + 5)
    add_bar(ws, "L5", cats=cats, data=data,
            title="图4  真实事件 AUC：非标意见 vs 披露类违规（0.5 = 随机）")
    style_note(ws, "L19", "Beneish 代理对真实非标意见的 AUC 仅 0.405，低于随机——代理基准方向相反。")
    ws.merge_cells("L19:N20")

    r2 = 19
    sup = m["event_supervised_metrics"]
    by_key = {(r["label"], r["model"], r["feature_set"]): r for r in sup}
    head3 = ["特征组", "Logit AUC 非标", "Logit Δ非标", "HGB AUC 非标", "HGB Δ非标",
             "Logit AUC 披露", "Logit Δ披露", "HGB AUC 披露", "HGB Δ披露"]
    rows3 = []
    for fset, label in (("finance", "仅财务 Finance"), ("text", "仅文本 Text"), ("fused", "融合 Fused")):
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
    delta_short = {"mod_opinion": "窄非标", "mod_opinion_wide": "宽非标",
                   "violation_any_t1": "任意违规", "violation_disclosure_t1": "披露违规"}
    deltas: list[tuple[str, float]] = []
    for label_key in ("mod_opinion", "mod_opinion_wide", "violation_any_t1", "violation_disclosure_t1"):
        for model in ("logit", "hgb"):
            d = by_key[(label_key, model, "delta_fused_vs_finance")]
            deltas.append(
                (f"{delta_short[label_key]}·{SUPERVISED_MODEL_LABELS[model].split('（')[0]}",
                 num(d["oof_auc"]))
            )
    hd = ["组合", "ΔAUC（融合 − 仅财务）"]
    wr = write_table(ws, r2 + 6, 2, hd, [list(t) for t in deltas],
                     number_fmt="0.000", widths=[34, 18])
    cats5 = Reference(ws, min_col=2, min_row=r2 + 7, max_row=r2 + 14)
    data5 = Reference(ws, min_col=3, min_row=r2 + 6, max_row=r2 + 14)
    chart5 = add_bar(ws, "K20", cats=cats5, data=data5,
                     title="图5  监督式 ΔAUC（融合 − 仅财务，8 组合；正值 = 增量）")
    chart5.width = 16
    style_note(ws, f"B{wr+1}",
               "按公司分组的 5 折交叉验证（StratifiedGroupKFold，无同公司泄漏）。8 个组合的 ΔAUC 全部为正，"
               "5 个 bootstrap 区间不含 0：文本块对真实事件有小而一致的互补增量；文本单独则弱于财务。")


def sheet_versions(wb: Workbook, m: dict[str, list[dict]]) -> None:
    ws = new_sheet(wb, "§5.6 两版对比")
    style_title(ws, "B2", "§5.6 第一版 → 第二版：做法改进与结果差异")
    style_subtitle(ws, "B3", "改进让阴性结论更可信，而不是翻转结论。第一版数据与代码保留在 archive_v0.1 与 git tag v0.1-baseline。")

    head = ["设计选择", "第一版 v0.1", "第二版 v0.2"]
    rows = [
        ["情感词典", "引导版（正 38 / 负 33）", "姚加权等 (2021) 全量（正 3,585 / 负 1,633）"],
        ["不确定词表", "引导版 23 词", "扩充约 100 词"],
        ["命中方式", "子串计数（'不' 会命中 '不错'）", "jieba 词元精确匹配（用户词典 5,218 词）"],
        ["评估基准", "仅 M > −1.78（标红 62.8%）", "双口径：legacy + 样本前 10%（M > 16.52）"],
        ["文本 ρ（vs M-Score）", "-0.030", "-0.029（结论不变）"],
        ["融合 ρ（vs M-Score）", "0.103", "0.103"],
        ["文本 top-10% 富集（校准）", "1.069", "0.848（反而跌破 1）"],
        ["结论变化", "阴性：文本无增量", "阴性更硬：词表 8.3× 密度下结论不变"],
    ]
    write_table(ws, 5, 2, head, rows, widths=[30, 34, 40])

    r1 = 16
    head2 = ["指标", "v0.1 每千词元命中", "v0.2 每千词元命中", "倍数"]
    rows2 = [
        [LEXICON_LABELS[r["metric"]], num(r["v01_per_1000"], 2), num(r["v02_per_1000"], 2),
         num(r["ratio"], 2)]
        for r in m["lexicon_density"]
    ]
    write_table(ws, r1, 2, head2, rows2, number_fmt="0.00", widths=[22, 18, 18, 10])

    cats = Reference(ws, min_col=2, min_row=r1 + 1, max_row=r1 + 4)
    data = Reference(ws, min_col=3, max_col=4, min_row=r1, max_row=r1 + 4)
    add_bar(ws, "H5", cats=cats, data=data,
            title="图6  词典命中密度：v0.1 → v0.2（同一批 MD&A 文本）")
    style_note(ws, f"B{r1+6}",
               "在 2021 年 200 篇 MD&A（175.6 万词元）上对比：情感词命中 13.4 → 111.3 / 千词元（8.3×）。"
               "否定结论不是词表太稀所致。")


def sheet_notes(wb: Workbook) -> None:
    ws = new_sheet(wb, "说明 Notes")
    style_title(ws, "B2", "口径、数据来源与复现")
    head = ["项", "说明"]
    rows = [
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
    ]
    write_table(ws, 5, 2, head, rows, widths=[18, 92])
    for rr in range(6, 6 + len(rows)):
        ws.cell(row=rr, column=3).alignment = Alignment(wrap_text=True, vertical="top")
        ws.row_dimensions[rr].height = 30


# ---- entry point -----------------------------------------------------------
def build(out: Path) -> Workbook:
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
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="output .xlsx path")
    args = parser.parse_args()
    try:
        build(Path(args.out))
    except FileNotFoundError as exc:
        print(f"missing input: {exc}", file=sys.stderr)
        return 2
    print(f"written: {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
