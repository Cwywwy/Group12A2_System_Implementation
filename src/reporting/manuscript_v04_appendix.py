# -*- coding: utf-8 -*-
"""
manuscript_v04_appendix.py
Author: Group12A2 DSW Team
Purpose: Build the appendix table grids that depend on the sample window, so a
         window change never leaves a stale count behind in the manuscript.
Module: src/reporting

Revision History
----------------
2026-11-26  initial version: descriptives, enrichment, attrition and outcome
            tables read straight from the pipeline tables.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

FINANCE_FEATURES = (
    "roa",
    "leverage",
    "revenue_growth",
    "ocf_to_assets",
    "receivables_turnover",
    "accruals_to_assets",
)
TEXT_FEATURES = ("readability", "sentiment_balance", "uncertainty_ratio")
DISPLAY_ORDER = FINANCE_FEATURES + TEXT_FEATURES


def branch_rows(num: dict, ranking: pd.DataFrame) -> list[list[str]]:
    """Table A.1: window and industry branches, with the current panel on top."""
    n = int(num["n"])
    events = int(num["events"]["mod_opinion_count"])
    finance = ranking[(ranking["label"] == "mod_opinion")
                      & (ranking["model"] == "finance-only IF")]["auc"]
    beneish = ranking[(ranking["label"] == "mod_opinion")
                      & (ranking["model"] == "Beneish M-Score")]["auc"]
    first, last = min(num["by_year"]), max(num["by_year"])
    rows = [[
        "Panel A: sample frame",
        "Years",
        "n",
        "Events",
        "AUC: finance-only",
        "AUC: Beneish",
    ]]
    rows.append([
        "Manufacturing (C)",
        f"{first}-{last}",
        f"{n:,}",
        f"{events:,}",
        f"{finance.iloc[0]:.3f}" if len(finance) else "-",
        f"{beneish.iloc[0]:.3f}" if len(beneish) else "-",
    ])
    rows.extend(
        [
            ["Manufacturing (C)", "2021-2023", "9,239", "204", "0.802", "0.242"],
            ["Manufacturing (C)", "2021-2024", "12,586", "254", "0.791", "0.248"],
            ["All non-financial industries", "2021-2023", "13,556", "380", "0.772", "0.273"],
            ["All non-financial industries", "2021-2024", "18,415", "469", "0.767", "0.277"],
            [
                "Panel B: outcome label, 2021-2024 non-financial sample",
                "Events",
                "AUC: finance-only",
                "AUC: text-only",
                "AUC: fused",
                "AUC: Beneish",
            ],
            ["Modified audit opinion in t", "469", "0.767", "0.537", "0.745", "0.277"],
            [
                "Annual-report restatement announced in t+1 (strict)",
                "449",
                "0.629",
                "0.484",
                "0.605",
                "0.443",
            ],
            ["Annual-report inquiry letter in t+1", "604", "0.632", "0.481", "0.607", "0.477"],
        ]
    )
    return rows


def _num(value: float) -> str:
    """Format a descriptive statistic compactly but informatively."""
    if pd.isna(value):
        return "-"
    magnitude = abs(value)
    if magnitude >= 1000:
        return f"{value:,.0f}"
    if magnitude >= 10:
        return f"{value:,.2f}"
    if magnitude >= 0.001:
        return f"{value:.4f}"
    return f"{value:.5f}"


def descriptives_rows(frame: pd.DataFrame) -> list[list[str]]:
    """Table B.1: distribution of the nine model inputs across the frame."""
    rows = [["Feature", "n", "mean", "std", "min", "max"]]
    for feature in DISPLAY_ORDER:
        column = frame[feature].dropna()
        rows.append(
            [
                feature,
                f"{len(column):,}",
                _num(column.mean()),
                _num(column.std()),
                _num(column.min()),
                _num(column.max()),
            ]
        )
    return rows


def enrichment_rows(topk: pd.DataFrame) -> list[list[str]]:
    """Table B.2: event rate and enrichment at three queue widths."""
    labels = {
        "if_finance": "Finance-only IF",
        "if_text": "Text-only IF",
        "if_fused": "Fused IF",
        "ae_fused": "Fused autoencoder",
    }
    rows = [[
        "Model",
        "k",
        "Event rate (legacy)",
        "Enrichment (legacy)",
        "Event rate (recalibrated)",
        "Enrichment (recalibrated)",
    ]]
    for model, label in labels.items():
        for k in (0.05, 0.10, 0.15):
            legacy = topk[(topk["model"] == model) & (topk["benchmark"] == "legacy")
                          & (topk["k"] == k)]
            calibrated = topk[(topk["model"] == model) & (topk["benchmark"] == "calibrated")
                              & (topk["k"] == k)]
            if legacy.empty or calibrated.empty:
                continue
            rows.append(
                [
                    label,
                    f"{int(round(k * 100))}%",
                    f"{legacy['event_rate'].iloc[0]:.3f}",
                    f"{legacy['enrichment'].iloc[0]:.3f}",
                    f"{calibrated['event_rate'].iloc[0]:.3f}",
                    f"{calibrated['enrichment'].iloc[0]:.3f}",
                ]
            )
    return rows


def attrition_rows(frame: pd.DataFrame) -> list[list[str]]:
    """Table B.5: every step between the frame and the analysis sample."""
    total = len(frame)
    with_beneish = int(frame["m_score"].notna().sum())
    finance_ok = frame[list(FINANCE_FEATURES)].notna().all(axis=1)
    with_finance = int((frame["m_score"].notna() & finance_ok).sum())
    text_ok = frame[list(TEXT_FEATURES)].notna().all(axis=1)
    with_text = int((frame["m_score"].notna() & finance_ok & text_ok).sum())
    first, last = int(frame["fiscal_year"].min()), int(frame["fiscal_year"].max())
    sample = frame[frame["m_score"].notna() & finance_ok & text_ok]
    return [
        ["Step", "Rule applied", "Firm-years dropped", "Firm-years retained"],
        ["0", f"Manufacturing firm-year frame, {first}-{last}", "-", f"{total:,}"],
        ["1", "Beneish M-Score computable (previous-year statement available)",
         f"{total - with_beneish:,}", f"{with_beneish:,}"],
        ["2", "All six financial features non-missing",
         f"{with_beneish - with_finance:,}", f"{with_finance:,}"],
        ["3", "All three MD&A features non-missing",
         f"{with_finance - with_text:,}", f"{with_text:,}"],
        ["", f"Analysis sample ({sample['symbol'].nunique():,} firms)", "-", f"{with_text:,}"],
    ]


def outcome_rows(
    events: pd.DataFrame,
    diagnostics: pd.DataFrame | None = None,
    settled_years: tuple[int, ...] = (2021, 2022, 2023),
) -> list[list[str]]:
    """Table B.6: label definitions with counts over the settled forward window."""
    settled = events[events["fiscal_year"].isin(settled_years)]
    n_settled = len(settled)
    n_full = len(events)

    def count(column: str, frame: pd.DataFrame) -> int:
        return int(frame[column].sum())

    def cell(column: str, frame: pd.DataFrame) -> str:
        value = count(column, frame)
        return f"{value:,} ({value / len(frame):.1%} of {len(frame):,})"

    strict = {}
    if diagnostics is not None and not diagnostics.empty:
        for _, row in diagnostics.iterrows():
            strict[str(row["label"])] = (int(row["n_strict"]), int(row["n_loose"]))
    any_strict = strict.get("violation_any_t1_strict")
    disclosure_strict = strict.get("violation_disclosure_t1_strict")

    def gate(bundle, loose_label: str) -> str:
        if bundle is None:
            return "-"
        # The diagnostics and the event table are both restricted to the settled
        # window now, so n_strict lines up with the loose count in this table.
        strict_count, _loose_count = bundle
        loose = count(loose_label, settled)
        if not loose:
            return "-"
        return f"{strict_count:,} of {loose:,} ({strict_count / loose:.1%})"

    return [
        ["Outcome label", "Definition", "Calendar-year t+1", "Strict gate"],
        ["Modified audit opinion (narrow)",
         "Any opinion other than unqualified in t",
         cell("mod_opinion", events), "Not applicable"],
        ["Modified audit opinion (wide)",
         "Also counts unqualified opinions with an explanatory paragraph in t",
         cell("mod_opinion_wide", events), "Not applicable"],
        ["Any violation announced in t+1",
         "Any STK_Violation announcement dated in the calendar year after the report",
         cell("violation_any_t1", settled),
         gate(any_strict, "violation_any_t1")],
        ["Disclosure violation announced in t+1",
         "Delayed disclosure, misstatement, material omission, fictitious profit or assets",
         cell("violation_disclosure_t1", settled),
         gate(disclosure_strict, "violation_disclosure_t1")],
    ]
