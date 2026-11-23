# -*- coding: utf-8 -*-
"""
revision_reports.py
Author: Group12A2 DSW Team
Purpose: Render the v0.3 revision evidence (strict timing and lexicon control)
         as Markdown that mirrors the tables written next to it.
Module: src.reporting

Revision History
----------------
2026-11-24  initial version: timing report and lexicon-control appendix
            extracted from run_07c and run_08.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

__all__ = ["append_lexicon_report", "write_timing_report"]


def _first(block: pd.DataFrame) -> pd.Series | None:
    return None if block.empty else block.iloc[0]


def write_timing_report(
    path: str | Path,
    ranking: pd.DataFrame,
    supervised: pd.DataFrame,
    diagnostics: pd.DataFrame,
    window_days: int | None,
) -> Path:
    """Write Part 1 of the revision evidence file."""
    gate = "no upper lag bound" if window_days is None else f"within {window_days} days"
    lines = [
        "# Strict t+1 event timing and v0.1 lexicon control",
        "",
        "## Part 1 - disclosure-date gated t+1 labels",
        "",
        "The original label counts an announcement as forward-looking when its",
        "calendar year equals fiscal year + 1. The strict label also requires the",
        "announcement date to fall strictly after the annual-report disclosure date",
        f"of fiscal year t ({gate}).",
        "",
        "| Label | Loose n | Strict n | Dropped | Share dropped |",
        "| --- | --- | --- | --- | --- |",
    ]
    for _, row in diagnostics.iterrows():
        lines.append(
            f"| {row['label']} | {int(row['n_loose']):,} | {int(row['n_strict']):,} | "
            f"{int(row['n_dropped']):,} | {row['share_dropped']:.1%} |"
        )
    lines += [
        "",
        "Firm-years without a usable disclosure date keep no strict label and are",
        "counted in the diagnostics table: "
        f"{int(diagnostics['n_firm_years_without_report_date'].iloc[0]):,} rows.",
        "",
        "### Ranking quality on the strict labels",
        "",
        "| Label | Score | AUC [95% CI] | Lift top-10% [95% CI] |",
        "| --- | --- | --- | --- |",
    ]
    for _, row in ranking.iterrows():
        lines.append(
            f"| {row['label']} | {row['model']} | "
            f"{row['auc']:.3f} [{row['auc_lo']:.3f}, {row['auc_hi']:.3f}] | "
            f"{row['lift_10pct']:.2f} [{row['lift_10pct_lo']:.2f}, {row['lift_10pct_hi']:.2f}] |"
        )
    lines += [
        "",
        "### Supervised comparison on the strict labels",
        "",
        "| Label | Model | Feature set | OOF AUC [95% CI] |",
        "| --- | --- | --- | --- |",
    ]
    for _, row in supervised.iterrows():
        lines.append(
            f"| {row['label']} | {row['model']} | {row['feature_set']} | "
            f"{row['oof_auc']:+.3f} [{row['oof_auc_lo']:+.3f}, {row['oof_auc_hi']:+.3f}] |"
        )

    strict_any = _first(ranking[(ranking["label"] == "violation_any_t1_strict") & (ranking["model"] == "finance-only IF")])
    loose_any = _first(ranking[(ranking["label"] == "violation_any_t1") & (ranking["model"] == "finance-only IF")])
    strict_disclosure = _first(
        ranking[(ranking["label"] == "violation_disclosure_t1_strict") & (ranking["model"] == "fused IF")]
    )
    lines += ["", "### Reading", ""]
    if strict_any is not None and loose_any is not None:
        lines.append(
            f"- The finance-only score ranks any-violation risk at AUC "
            f"{strict_any['auc']:.3f} on the strict label versus {loose_any['auc']:.3f} "
            f"on the loose label; the gate moves the number by "
            f"{strict_any['auc'] - loose_any['auc']:+.3f} and the substantive reading is "
            "unchanged: finance-only ranking carries most of the signal, the text block "
            "adds little, and the M-Score points the wrong way."
        )
    if strict_disclosure is not None:
        lines.append(
            f"- The fused score on the strict disclosure label reaches AUC "
            f"{strict_disclosure['auc']:.3f} "
            f"[{strict_disclosure['auc_lo']:.3f}, {strict_disclosure['auc_hi']:.3f}]."
        )
    lines += [
        "",
        "Rows marked `delta_*_vs_finance` are paired AUC differences against the",
        "finance-only baseline; an interval covering zero means no detectable extra",
        "rank information.",
        "",
    ]
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def append_lexicon_report(
    path: str | Path,
    control: pd.DataFrame,
    overlap: pd.DataFrame,
    diagnostics: pd.DataFrame,
) -> Path:
    """Append Part 2 of the revision evidence file."""
    def value(spec: str, model: str, column: str) -> float:
        block = control[(control["spec"] == spec) & (control["model"] == model)]
        return float(block.iloc[0][column])

    def top10(pair: str) -> float:
        block = overlap[overlap["pair"] == pair]
        return float(block.iloc[0]["top10_overlap"])

    row = diagnostics.iloc[0]
    lines = [
        "",
        "## Part 2 - v0.1 lexicon control on the repaired financial data",
        "",
        f"Both variants are fitted on the same {int(row['n_rows']):,} firm-years with the",
        "same six financial features, the same preprocessing and the same Isolation",
        "Forest settings; only the three text features change (current dictionary",
        "versus the archived v0.1 values).",
        "",
        "| Text measurement | Text-only rho | Text-only calibrated lift-10% | Fused rho | Fused calibrated lift-10% |",
        "| --- | --- | --- | --- | --- |",
    ]
    for spec, caption in (("current_lexicon", "Current dictionary"), ("v0.1_lexicon", "v0.1 dictionary")):
        lines.append(
            f"| {caption} | {value(spec, 'if_text', 'spearman_rho'):+.3f} | "
            f"{value(spec, 'if_text', 'enrichment_calibrated_k10'):.2f} | "
            f"{value(spec, 'if_fused', 'spearman_rho'):+.3f} | "
            f"{value(spec, 'if_fused', 'enrichment_calibrated_k10'):.2f} |"
        )
    lines += [
        "",
        f"Top-decile overlap between the two text rankings: {top10('text_current_vs_v01'):.3f};",
        f"between the two fused rankings: {top10('fused_current_vs_v01'):.3f}.",
        "",
        "Corpus check: the archived and the current text features agree on the token",
        f"count for {float(row['share_identical_token_count']):.1%} of the shared rows, with",
        f"correlations of {float(row['corr_readability']):.3f} (readability), "
        f"{float(row['corr_sentiment']):.3f} (sentiment) and",
        f"{float(row['corr_uncertainty']):.3f} (uncertainty).",
        "",
        "Reading: the text block stays close to uncorrelated with the Beneish proxy",
        "under either dictionary, so the near-zero text correlation in the main",
        "results is not an artefact of the dictionary upgrade; the movement documented",
        "in the appendix came from the financial-data repair and the benchmark change,",
        "not from the lexicon.",
        "",
    ]
    path = Path(path)
    prefix = path.read_text(encoding="utf-8") if path.exists() else ""
    path.write_text(prefix + "\n".join(lines), encoding="utf-8")
    return path
