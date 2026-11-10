#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Build the twelve-slide course presentation from the released result tables.

File:        scripts/build_slides.py
Author:      Jinyu Wang
Purpose:     Generate outputs/slides/Group12A2_Deck.pptx (16:9, 12 slides) directly
             from outputs/tables/* so the deck can never drift from the manuscript.
Module role: presentation assembly (manuscript assembly family).

Revision history
----------------
2026-11-11  Created: twelve-slide generator with real numbers, SHAP bars, overlap matrix.
"""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Pt

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "outputs" / "slides" / "Group12A2_Deck.pptx"

PX = 9525  # 96 dpi -> EMU
BG = RGBColor(0xF7, 0xF9, 0xFC)
INK = RGBColor(0x10, 0x2A, 0x43)
PRIMARY = RGBColor(0x0B, 0x5C, 0xAB)
ACCENT = RGBColor(0x2D, 0x8C, 0x7A)
HIGHLIGHT = RGBColor(0xF5, 0x9E, 0x0B)
CARD = RGBColor(0xFF, 0xFF, 0xFF)
BORDER = RGBColor(0xD9, 0xE2, 0xEC)
MUTED = RGBColor(0x62, 0x7D, 0x8A)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
FONT = "Arial"
PRESENTATION_DATE = "December 2025"
MEMBERS = [
    ("Jinyu Wang", "MC644879", "Data pipeline & finance features"),
    ("Wenyuan Chen", "MC644700", "MD&A extraction & text features"),
    ("Mingxuan Wu", "MC637835", "Modelling, evaluation & SHAP"),
    ("Kolawole Sunday O.", "MC650023", "Literature, writing & slides"),
]


def _load_builder():
    path = ROOT / "scripts" / "build_section5.py"
    spec = importlib.util.spec_from_file_location("build_section5", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def pct(value: float, digits: int = 1) -> str:
    return f"{value * 100:.{digits}f}%"


def num3(value: float) -> str:
    return f"{value:.3f}"


# --------------------------------------------------------------------------- drawing helpers


def _blank(prs: Presentation):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = BG
    return slide


def _text(slide, x, y, w, h, runs, size=15, bold=False, color=INK,
          align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, spacing=1.15):
    """Add a textbox; ``runs`` is a string, a list of strings or a list of (text, dict)."""
    box = slide.shapes.add_textbox(Emu(x * PX), Emu(y * PX), Emu(w * PX), Emu(h * PX))
    frame = box.text_frame
    frame.word_wrap = True
    frame.vertical_anchor = anchor
    frame.margin_left = frame.margin_right = Emu(0)
    frame.margin_top = frame.margin_bottom = Emu(0)
    items = runs if isinstance(runs, list) else [runs]
    if items and isinstance(items[0], list):
        items = [entry for group in items for entry in group]
    for index, item in enumerate(items):
        text, overrides = (item, {}) if isinstance(item, str) else item
        para = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
        para.alignment = overrides.get("align", align)
        para.line_spacing = spacing
        if "space_before" in overrides:
            para.space_before = Pt(overrides["space_before"])
        run = para.add_run()
        run.text = text
        font = run.font
        font.name = FONT
        font.size = Pt(overrides.get("size", size))
        font.bold = overrides.get("bold", bold)
        font.color.rgb = overrides.get("color", color)
        if overrides.get("italic"):
            font.italic = True
    return box


def _card(slide, x, y, w, h, fill=CARD, line=BORDER, radius=0.06):
    shape = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, Emu(x * PX), Emu(y * PX), Emu(w * PX), Emu(h * PX)
    )
    shape.adjustments[0] = radius
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill
    shape.line.color.rgb = line
    shape.line.width = Pt(1)
    shape.shadow.inherit = False
    shape.text_frame.word_wrap = True
    return shape


def _bar(slide, x, y, w, h, colour=PRIMARY):
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Emu(x * PX), Emu(y * PX), Emu(w * PX), Emu(h * PX))
    shape.fill.solid()
    shape.fill.fore_color.rgb = colour
    shape.line.fill.background()
    shape.shadow.inherit = False
    return shape


def _footer(slide, page: int):
    _bar(slide, 48, 496, 864, 2, BORDER)
    _text(slide, 48, 506, 420, 20, "Group 12A2 · Intro FinTech", size=11, color=MUTED)
    _text(slide, 780, 506, 132, 20, str(page), size=11, color=MUTED, align=PP_ALIGN.RIGHT)


def _heading(slide, title: str, kicker: str | None = None):
    y = 46
    if kicker:
        _text(slide, 48, 30, 600, 18, kicker, size=11, bold=True, color=ACCENT)
    _text(slide, 48, y, 864, 40, title, size=28, bold=True, color=INK)
    _bar(slide, 48, y + 46, 72, 4, HIGHLIGHT)


def _table(slide, x, y, w, rows, col_widths, header=True, size=11):
    height = 30 * len(rows)
    shape = slide.shapes.add_table(
        len(rows), len(rows[0]), Emu(x * PX), Emu(y * PX), Emu(w * PX), Emu(height * PX)
    )
    table = shape.table
    total = sum(col_widths)
    for index, width in enumerate(col_widths):
        table.columns[index].width = Emu(int(w * PX * width / total))
    for r, row in enumerate(rows):
        for c, value in enumerate(row):
            cell = table.cell(r, c)
            cell.text = str(value)
            cell.margin_left = cell.margin_right = Emu(6 * PX)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.fill.solid()
            cell.fill.fore_color.rgb = PRIMARY if (header and r == 0) else CARD
            para = cell.text_frame.paragraphs[0]
            para.alignment = PP_ALIGN.CENTER if c else PP_ALIGN.LEFT
            for run in para.runs:
                run.font.name = FONT
                run.font.size = Pt(size)
                run.font.bold = header and r == 0
                run.font.color.rgb = WHITE if (header and r == 0) else INK
    return table


# --------------------------------------------------------------------------- slides


def slide_title(prs, num):
    slide = _blank(prs)
    _bar(slide, 0, 0, 960, 6, PRIMARY)
    _text(slide, 48, 104, 620, 108, "Screening Financial Disclosure Risk", size=36, bold=True, color=INK, spacing=1.06)
    _text(slide, 48, 232, 600, 64,
          "Textual–Financial Feature Fusion and Explainable Anomaly Detection",
          size=20, color=PRIMARY, spacing=1.2)
    _text(slide, 48, 318, 600, 26,
          "Evidence from Chinese A-share Manufacturing Firms, 2021–2023",
          size=14, color=MUTED)
    _bar(slide, 48, 368, 120, 3, HIGHLIGHT)
    _text(slide, 48, 398, 560, 60,
          [[("Group 12A2 · Intro FinTech", {"bold": True, "size": 13})],
           [(PRESENTATION_DATE, {"size": 12, "color": MUTED})]])
    layers = [("DATA", "CSMAR statements\n+ CNINFO reports"), ("FEATURES", "6 financial\n3 MD&A text"),
              ("RANKING", "Isolation Forest\n+ SHAP")]
    top = 118
    for index, (label, body) in enumerate(layers):
        y = top + index * 104
        _card(slide, 700, y, 208, 84, fill=CARD)
        _bar(slide, 700, y, 5, 84, [PRIMARY, ACCENT, HIGHLIGHT][index])
        _text(slide, 722, y + 14, 170, 18, label, size=11, bold=True, color=[PRIMARY, ACCENT, HIGHLIGHT][index])
        _text(slide, 722, y + 36, 170, 40, body, size=12, color=INK, spacing=1.15)
    _footer(slide, 1)


def slide_questions(prs, num):
    slide = _blank(prs)
    _heading(slide, "Three research questions", "MOTIVATION")
    questions = [
        ("01", "Does MD&A text add detection value beyond financial features?",
         "Fused versus finance-only ranking against the same benchmark."),
        ("02", "Which feature group drives the ranking?",
         "Global and local SHAP attribution on the fused model."),
        ("03", "Is the ranking stable across models and thresholds?",
         "Autoencoder robustness, threshold sensitivity, list overlap."),
    ]
    for index, (label, main, sub) in enumerate(questions):
        y = 118 + index * 108
        _card(slide, 48, y, 864, 92)
        _text(slide, 70, y + 24, 60, 40, label, size=30, bold=True, color=HIGHLIGHT)
        _text(slide, 148, y + 18, 720, 26, main, size=16, bold=True, color=INK)
        _text(slide, 148, y + 50, 720, 24, sub, size=13, color=MUTED)
    _footer(slide, 2)


def slide_data(prs, num):
    slide = _blank(prs)
    _heading(slide, "Data: statements, reports, one benchmark", "SAMPLE CONSTRUCTION")
    columns = [
        ("STRUCTURED DATA", "CSMAR 2020–2023", ["Six statement ratios", "Balance-sheet and income items"]),
        ("DISCLOSURE TEXT", "CNINFO 2021–2023", ["Annual report PDFs", "MD&A section located per report"]),
        ("EVALUATION BENCHMARK", "Beneish M-Score", ["Evaluation only", "Never used in training"]),
    ]
    for index, (title, sub, bullets) in enumerate(columns):
        x = 48 + index * 292
        _card(slide, x, 118, 272, 132)
        _text(slide, x + 20, 134, 232, 18, title, size=11, bold=True, color=ACCENT)
        _text(slide, x + 20, 156, 232, 22, sub, size=15, bold=True, color=INK)
        _text(slide, x + 20, 186, 232, 52, bullets, size=12, color=MUTED, spacing=1.25)
    _card(slide, 48, 272, 864, 122, fill=RGBColor(0x0B, 0x5C, 0xAB))
    _text(slide, 72, 286, 380, 22, "SAMPLE FRAME", size=11, bold=True, color=RGBColor(0xCB, 0xDC, 0xEF))
    _text(slide, 72, 308, 400, 30, f"{num['frame_firms']:,} firms · {num['frame_years']:,} firm-years",
          size=19, bold=True, color=WHITE)
    _text(slide, 72, 344, 420, 24,
          f"Complete features: {num['n']:,} firm-years ({pct(num['share'])})",
          size=12, color=RGBColor(0xE3, 0xEE, 0xF8))
    _text(slide, 72, 366, 420, 22,
          f"across {num['n_firms']:,} firms",
          size=12, color=RGBColor(0xE3, 0xEE, 0xF8))
    _text(slide, 520, 284, 370, 88,
          ["PDF coverage 98.8% of the frame", "MD&A usable text " +
           f"{pct(min(num['year_share_text'].values()))}–{pct(max(num['year_share_text'].values()))} by year",
           "Missing files are pre-listing NEEQ years"],
          size=12, color=WHITE, spacing=1.3)
    _text(slide, 48, 414, 864, 60,
          [("Frame 10,172 firm-years, usable sample 8,140.", {"bold": True, "size": 13}),
           ("Balanced across 2021 (" + f"{num['by_year'][2021]:,}), 2022 ({num['by_year'][2022]:,}) and 2023 ({num['by_year'][2023]:,}).",
            {"size": 13, "color": MUTED})], spacing=1.35)
    _footer(slide, 3)


def slide_pipeline(prs, num):
    slide = _blank(prs)
    _heading(slide, "Pipeline: five reproducible steps", "METHOD OVERVIEW")
    steps = ["Ingest", "Extract MD&A", "Construct 9 features", "Rank anomalies", "Evaluate & explain"]
    for index, label in enumerate(steps):
        x = 48 + index * 176
        _card(slide, x, 150, 156, 92, fill=CARD)
        _text(slide, x + 16, 166, 124, 18, f"STEP {index + 1}", size=10, bold=True, color=HIGHLIGHT)
        _text(slide, x + 16, 190, 124, 44, label, size=14, bold=True, color=INK)
        if index < len(steps) - 1:
            _text(slide, x + 152, 178, 24, 26, "→", size=18, bold=True, color=PRIMARY)
    notes = [("Versioned inputs", "Raw CSMAR workbooks and CNINFO PDFs are hashed and logged."),
             ("Checkpointed extraction", "MD&A extraction writes after every 500 reports."),
             ("Single command", "The whole chain runs from one entry script.")]
    for index, (title, body) in enumerate(notes):
        x = 48 + index * 292
        _text(slide, x, 286, 272, 20, title, size=13, bold=True, color=ACCENT)
        _text(slide, x, 310, 272, 56, body, size=12, color=MUTED, spacing=1.3)
    _card(slide, 48, 392, 864, 58, fill=RGBColor(0xFF, 0xF7, 0xE6), line=HIGHLIGHT)
    _text(slide, 72, 410, 820, 26, "No benchmark variable enters model training.",
          size=15, bold=True, color=INK)
    _footer(slide, 4)


def slide_features(prs, num):
    slide = _blank(prs)
    _heading(slide, "Nine features, two groups", "FEATURE SYSTEM")
    _card(slide, 48, 118, 424, 250)
    _text(slide, 72, 134, 380, 22, "6 FINANCIAL FEATURES", size=11, bold=True, color=PRIMARY)
    financial = ["roa", "leverage", "revenue_growth", "ocf_to_assets",
                 "receivables_turnover", "accruals_to_assets"]
    for index, name in enumerate(financial):
        y = 166 + index * 32
        _bar(slide, 72, y + 6, 4, 16, PRIMARY)
        _text(slide, 88, y, 360, 24, name, size=14, color=INK)
    _card(slide, 488, 118, 424, 250)
    _text(slide, 512, 134, 380, 22, "3 MD&A TEXT FEATURES", size=11, bold=True, color=ACCENT)
    textual = [("readability", "characters per sentence proxy"),
               ("sentiment_balance", "(pos − neg) / (pos + neg)"),
               ("uncertainty_ratio", "uncertainty words / tokens")]
    for index, (name, note) in enumerate(textual):
        y = 168 + index * 62
        _bar(slide, 512, y + 6, 4, 16, ACCENT)
        _text(slide, 528, y, 360, 22, name, size=14, bold=True, color=INK)
        _text(slide, 528, y + 24, 360, 22, note, size=12, color=MUTED)
    _card(slide, 48, 390, 864, 58, fill=RGBColor(0xF0, 0xF7, 0xF4), line=ACCENT)
    _text(slide, 72, 408, 820, 26,
          "Winsorise 1% / 99% · subindustry-year z-score · token-level lexicon match",
          size=14, bold=True, color=INK)
    _footer(slide, 5)


def slide_model(prs, num):
    slide = _blank(prs)
    _heading(slide, "Unsupervised screening, four rankings", "MODEL DESIGN")
    _card(slide, 330, 122, 300, 96, fill=RGBColor(0x10, 0x2A, 0x43), line=RGBColor(0x10, 0x2A, 0x43))
    _text(slide, 350, 142, 260, 26, "Isolation Forest", size=20, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    _text(slide, 350, 176, 260, 24, "primary ranking model", size=12, color=RGBColor(0xB9, 0xCC, 0xDD),
          align=PP_ALIGN.CENTER)
    variants = ["Finance-only", "Text-only", "Fused"]
    for index, label in enumerate(variants):
        x = 48 + index * 200
        _card(slide, x, 246, 176, 54)
        _text(slide, x + 10, 260, 156, 24, label, size=14, bold=True, color=PRIMARY, align=PP_ALIGN.CENTER)
    _card(slide, 648, 246, 264, 54)
    _text(slide, 658, 260, 244, 24, "Autoencoder 16–8–16", size=14, bold=True, color=ACCENT,
          align=PP_ALIGN.CENTER)
    params = [("500", "trees"), ("256", "max samples"), ("42", "seed"), ("10%", "review queue")]
    for index, (value, label) in enumerate(params):
        x = 48 + index * 208
        _card(slide, x, 326, 184, 76)
        _text(slide, x + 14, 340, 156, 30, value, size=22, bold=True, color=INK)
        _text(slide, x + 14, 372, 156, 20, label, size=11, color=MUTED)
    _text(slide, 48, 424, 864, 50,
          ["Identical features, sample and evaluation for every ranking.",
           ("Scores are review-priority signals, not fraud verdicts.", {"color": MUTED})], spacing=1.35)
    _footer(slide, 6)


def slide_rq1(prs, num):
    slide = _blank(prs)
    _heading(slide, "RQ1: text adds no detection value", "MAIN RESULT")
    _text(slide, 48, 106, 500, 22, "Spearman rank agreement with the Beneish M-Score", size=13,
          bold=True, color=MUTED)
    cards = [("Finance-only", num["rho_if_finance"], PRIMARY),
             ("Text-only", num["rho_if_text"], MUTED),
             ("Fused", num["rho_if_fused"], ACCENT)]
    for index, (label, value, colour) in enumerate(cards):
        x = 48 + index * 200
        _card(slide, x, 136, 180, 104)
        _text(slide, x + 16, 150, 148, 20, label, size=12, bold=True, color=colour)
        _text(slide, x + 16, 174, 148, 40, num3(value), size=30, bold=True, color=INK)
        _text(slide, x + 16, 212, 148, 20, f"rho, n = {num['n']:,}", size=10, color=MUTED)
    _card(slide, 648, 136, 264, 104, fill=RGBColor(0xFF, 0xF7, 0xE6), line=HIGHLIGHT)
    _text(slide, 666, 150, 228, 20, "AUTOENCODER", size=10, bold=True, color=HIGHLIGHT)
    _text(slide, 666, 172, 228, 40, num3(num["rho_ae_fused"]), size=28, bold=True, color=INK)
    _text(slide, 666, 212, 228, 20,
          f"not significant (p = {num['p_ae_fused']:.2f})", size=10, color=MUTED)
    rows = [["Review queue", "Finance-only", "Fused"],
            ["top 5%", num3(num["en_legacy_if_finance_5"]), num3(num["en_legacy_if_fused_5"])],
            ["top 10%", num3(num["en_legacy_if_finance_10"]), num3(num["en_legacy_if_fused_10"])],
            ["top 15%", num3(num["en_legacy_if_finance_15"]), num3(num["en_legacy_if_fused_15"])]]
    _text(slide, 48, 258, 420, 22, "Enrichment under the literal −1.78 cut-off", size=13, bold=True, color=MUTED)
    _table(slide, 48, 284, 420, rows, [3, 2, 2], size=11)
    _text(slide, 492, 258, 420, 22, "Recalibrated (sample top decile)", size=13, bold=True, color=MUTED)
    rows2 = [["Review queue", "Finance-only", "Fused"],
             ["top 5%", num3(num["en_calibrated_if_finance_5"]), num3(num["en_calibrated_if_fused_5"])],
             ["top 10%", num3(num["en_calibrated_if_finance_10"]), num3(num["en_calibrated_if_fused_10"])],
             ["top 15%", num3(num["en_calibrated_if_finance_15"]), num3(num["en_calibrated_if_fused_15"])]]
    _table(slide, 492, 284, 420, rows2, [3, 2, 2], size=11)
    _text(slide, 48, 414, 864, 66,
          [("Answer: no. Adding the three MD&A features does not improve the ranking "
            f"({num3(num['rho_if_fused'])} vs {num3(num['rho_if_finance'])}); the text-only ranking is "
            f"{'essentially uncorrelated' if abs(num['rho_if_text']) < 0.05 else 'weakly correlated'} "
            f"(rho = {num3(num['rho_if_text'])}).", {"size": 14}),
           ("The negative result holds under both benchmark definitions.", {"size": 12, "color": MUTED})],
          spacing=1.3)
    _footer(slide, 7)


def slide_rq2(prs, num):
    slide = _blank(prs)
    _heading(slide, "RQ2: financial features dominate", "EXPLAINABILITY")
    _text(slide, 48, 106, 420, 22, "Global SHAP contribution", size=13, bold=True, color=MUTED)
    bars = [("Financial group", num["shap_finance"], PRIMARY), ("Textual group", num["shap_text"], ACCENT)]
    for index, (label, value, colour) in enumerate(bars):
        y = 146 + index * 84
        _text(slide, 48, y, 250, 22, label, size=13, bold=True, color=INK)
        _text(slide, 300, y, 90, 22, pct(value), size=13, bold=True, color=colour)
        _bar(slide, 48, y + 30, 320, 20, BORDER)
        _bar(slide, 48, y + 30, max(6, int(320 * value)), 20, colour)
    _text(slide, 48, 314, 420, 22, "Three most important global features", size=13, bold=True, color=MUTED)
    for index, (name, value) in enumerate(num["shap_top3"]):
        y = 342 + index * 24
        _text(slide, 48, y, 250, 20, f"{index + 1}. {name}", size=11, color=INK)
        _text(slide, 300, y, 70, 20, num3(value), size=11, bold=True, color=PRIMARY, align=PP_ALIGN.RIGHT)
    _card(slide, 492, 106, 420, 292)
    _text(slide, 516, 124, 372, 20, "LOCAL EXPLANATION", size=11, bold=True, color=HIGHLIGHT)
    _text(slide, 516, 150, 372, 26, f"Top-ranked firm-year {num['top1_symbol']} ({num['top1_year']})",
          size=15, bold=True, color=INK)
    _text(slide, 516, 182, 372, 22, f"Subindustry {num['top1_industry']} · anomaly score {num3(num['top1_score'])}",
          size=12, color=MUTED)
    _text(slide, 516, 216, 372, 22, "Main local drivers", size=12, bold=True, color=ACCENT)
    for index, name in enumerate(num["top1_drivers"]):
        y = 242 + index * 28
        _text(slide, 516, y, 360, 22, f"· {name}", size=12, color=INK)
    _text(slide, 516, 336, 372, 50,
          f"M-Score {num['top1_mscore']:,.1f} makes this an extreme observation, "
          "not a confirmed case of misconduct.", size=11, color=MUTED, spacing=1.25)
    _card(slide, 48, 414, 864, 58, fill=RGBColor(0xF0, 0xF7, 0xF4), line=ACCENT)
    _text(slide, 72, 432, 820, 26,
          "Screening signals support review; they do not prove misconduct.",
          size=14, bold=True, color=INK)
    _footer(slide, 8)


def slide_rq3(prs, num):
    slide = _blank(prs)
    _heading(slide, "RQ3: stable lists, fragile ranking", "ROBUSTNESS")
    _text(slide, 48, 106, 400, 22, "Top-10% list overlap (Jaccard)", size=13, bold=True, color=MUTED)
    labels = ["Fin", "Txt", "Fused", "AE"]
    keys = ["if_finance", "if_text", "if_fused", "ae_fused"]
    matrix = [[""] + labels]
    for row_key, row_label in zip(keys, labels):
        row = [row_label]
        for col_key in keys:
            row.append("—" if row_key == col_key else num3(num["overlap"][(row_key, col_key)]))
        matrix.append(row)
    _table(slide, 48, 136, 400, matrix, [1, 1, 1, 1, 1], size=12)
    _card(slide, 492, 106, 420, 200)
    _text(slide, 516, 124, 372, 20, "AUTOENCODER ROBUSTNESS", size=11, bold=True, color=ACCENT)
    _text(slide, 516, 150, 372, 34, f"rho = {num3(num['rho_ae_fused'])}", size=24, bold=True, color=INK)
    _text(slide, 516, 188, 372, 62,
          "The fused autoencoder does not reproduce the Isolation Forest ranking, "
          "so the headline result is model-dependent.", size=11, color=MUTED, spacing=1.25)
    _text(slide, 516, 258, 372, 22,
          f"Finance–fused overlap {num3(num['overlap_fin_fused'])}",
          size=11, color=INK)
    _text(slide, 516, 278, 372, 22,
          f"Finance–text overlap {num3(num['overlap_fin_text'])}",
          size=11, color=INK)
    _text(slide, 48, 330, 420, 22, "Threshold sensitivity", size=13, bold=True, color=MUTED)
    rows = [["Queue", "Legacy", "Recalibrated"],
            ["5%", num3(num["en_legacy_if_fused_5"]), num3(num["en_calibrated_if_fused_5"])],
            ["10%", num3(num["en_legacy_if_fused_10"]), num3(num["en_calibrated_if_fused_10"])],
            ["15%", num3(num["en_legacy_if_fused_15"]), num3(num["en_calibrated_if_fused_15"])]]
    _table(slide, 48, 356, 400, rows, [1, 2, 2], size=11)
    _text(slide, 48, 474, 864, 20,
          "Fused-model enrichment at 5%, 10% and 15% review queues; the ranking order does not change.",
          size=11, color=MUTED)
    _footer(slide, 9)


def slide_limits(prs, num):
    slide = _blank(prs)
    _heading(slide, "Limits we report ourselves", "INTERPRETATION")
    cards = [("Dictionary sentiment is a proxy",
              "A published financial lexicon matched token by token; nuance and context are lost."),
             ("Extraction coverage is incomplete",
              f"Scanned or unreadable reports are excluded; usable text is {pct(min(num['year_share_text'].values()))}–"
              f"{pct(max(num['year_share_text'].values()))} by year."),
             ("M-Score is an imperfect benchmark",
              f"The literal cut-off flags {pct(num['legacy_share'])} of this sample, so we also report a "
              "sample-calibrated decile.")]
    for index, (title, body) in enumerate(cards):
        x = 48 + index * 292
        _card(slide, x, 118, 272, 220)
        _bar(slide, x, 118, 272, 4, [PRIMARY, ACCENT, HIGHLIGHT][index])
        _text(slide, x + 20, 140, 232, 44, title, size=15, bold=True, color=INK)
        _text(slide, x + 20, 194, 232, 120, body, size=12, color=MUTED, spacing=1.3)
    _card(slide, 48, 362, 864, 76, fill=RGBColor(0xFF, 0xF7, 0xE6), line=HIGHLIGHT)
    _text(slide, 72, 376, 820, 50,
          [("Outputs are review-priority signals, not misconduct labels.", {"bold": True, "size": 15}),
           ("No fraud, violation or disclosure-quality verdict is claimed anywhere in the paper.",
            {"size": 12, "color": MUTED})], spacing=1.3)
    _footer(slide, 10)


def slide_repro(prs, num):
    slide = _blank(prs)
    _heading(slide, "Reproducible by construction", "OPEN SCIENCE")
    checks = [("Seed fixed", "SEED = 42 in every stochastic step"),
              ("Versioned scripts", "Numbered run_0x scripts, one job each"),
              ("Versioned intermediates", "Every CSV table in outputs/tables is released"),
              ("Checkpointed extraction", "Downloads and MD&A parsing resume after interruption"),
              ("One command", "run_99_full_pipeline.py rebuilds every table and figure")]
    for index, (title, body) in enumerate(checks):
        y = 112 + index * 52
        _bar(slide, 48, y + 6, 18, 18, ACCENT)
        _text(slide, 78, y, 300, 22, title, size=14, bold=True, color=INK)
        _text(slide, 78, y + 24, 460, 22, body, size=11, color=MUTED)
    _card(slide, 592, 112, 320, 190, fill=RGBColor(0x10, 0x2A, 0x43), line=RGBColor(0x10, 0x2A, 0x43))
    _text(slide, 612, 130, 280, 20, "FULL REBUILD", size=10, bold=True, color=RGBColor(0xB9, 0xCC, 0xDD))
    _text(slide, 612, 156, 280, 90,
          ["python scripts/", "run_99_full_pipeline.py"], size=13, color=WHITE, spacing=1.4)
    _text(slide, 612, 256, 280, 36, "Deterministic output, documented in the reproducibility guide.",
          size=11, color=RGBColor(0xB9, 0xCC, 0xDD))
    _text(slide, 592, 326, 320, 96,
          ["Manuscript §5 is generated from the same tables by a single assembly script,",
           "so numbers in the paper cannot drift from the released results."],
          size=12, color=MUTED, spacing=1.3)
    _footer(slide, 11)


def slide_conclusion(prs, num):
    slide = _blank(prs)
    _heading(slide, "Conclusion", "TAKEAWAYS")
    _card(slide, 48, 114, 864, 84, fill=RGBColor(0x0B, 0x5C, 0xAB), line=RGBColor(0x0B, 0x5C, 0xAB))
    _text(slide, 72, 132, 816, 52,
          f"Financial features carry a weak but significant screening signal "
          f"(rho = {num3(num['rho_if_finance'])}); MD&A text features add none.",
          size=16, bold=True, color=WHITE, spacing=1.25)
    points = [("What we deliver", "A reproducible, explainable screening pipeline built on public data."),
              ("What we find", "Text-only and fused rankings fail to improve on finance-only."),
              ("What it means", "Textual disclosure risk is not captured by simple lexicon measures here."),
              ("What is next", "Inquiry letters, restatements and audit opinions as outcome benchmarks.")]
    for index, (title, body) in enumerate(points):
        x = 48 + (index % 2) * 440
        y = 212 + (index // 2) * 72
        _text(slide, x, y, 400, 20, title, size=12, bold=True, color=ACCENT)
        _text(slide, x, y + 20, 400, 40, body, size=11, color=INK, spacing=1.2)
    _text(slide, 48, 352, 864, 20, "GROUP 12A2", size=10, bold=True, color=HIGHLIGHT)
    for index, (name, sid, role) in enumerate(MEMBERS):
        x = 48 + index * 220
        _text(slide, x, 374, 208, 20, name, size=12, bold=True, color=INK)
        _text(slide, x, 394, 208, 18, sid, size=10, color=MUTED)
        _text(slide, x, 412, 208, 30, role, size=10, color=MUTED, spacing=1.15)
    _text(slide, 48, 452, 864, 26, "Thank you · Questions", size=18, bold=True, color=PRIMARY)
    _footer(slide, 12)


def overlap_matrix() -> dict[tuple[str, str], float]:
    """Read the pairwise top-10% list overlap into a symmetric lookup."""
    import pandas as pd

    table = pd.read_csv(ROOT / "outputs" / "tables" / "ranking_overlap.csv")
    overlaps: dict[tuple[str, str], float] = {}
    for row in table.itertuples(index=False):
        value = float(row.top10_overlap)
        overlaps[(row.model_a, row.model_b)] = value
        overlaps[(row.model_b, row.model_a)] = value
    return overlaps


def build(out: Path) -> Path:
    builder = _load_builder()
    num = builder.collect_numbers()
    num["overlap"] = overlap_matrix()
    prs = Presentation()
    prs.slide_width = Emu(960 * PX)
    prs.slide_height = Emu(540 * PX)
    for function in (slide_title, slide_questions, slide_data, slide_pipeline, slide_features,
                     slide_model, slide_rq1, slide_rq2, slide_rq3, slide_limits, slide_repro,
                     slide_conclusion):
        function(prs, num)
    out.parent.mkdir(parents=True, exist_ok=True)
    prs.save(out)
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the 12-slide course deck from result tables.")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    path = build(args.out)
    print(f"deck written: {path}")


if __name__ == "__main__":
    main()
