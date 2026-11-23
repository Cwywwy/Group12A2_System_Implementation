# -*- coding: utf-8 -*-
"""
revision_checks.py
Author: Group12A2 DSW Team
Purpose: Verify that every v0.3 number quoted in the manuscript still matches
         the table it was taken from, so prose and artifacts cannot drift.
Module: src.reporting

Revision History
----------------
2026-11-24  initial version: Phase 2 number audit extracted from the patcher.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.config import TABLES

__all__ = ["check_v03_numbers"]

TOLERANCE = 5e-4


def _expect(problems: list[str], name: str, got, want, tolerance: float = TOLERANCE) -> None:
    try:
        close = abs(float(got) - float(want)) <= tolerance
    except (TypeError, ValueError):
        close = False
    if not close:
        problems.append(f"{name}: table says {got}, text says {want}")


def check_v03_numbers(tables_dir: str | Path = TABLES) -> list[str]:
    """Return a list of mismatches; an empty list means the quotes are current."""
    tables = Path(tables_dir)
    problems: list[str] = []

    diagnostics = pd.read_csv(tables / "event_strict_diagnostics.csv")
    for label, loose, strict, dropped in (
        ("violation_any_t1_strict", 1965, 1543, 422),
        ("violation_disclosure_t1_strict", 1337, 1040, 297),
    ):
        row = diagnostics[diagnostics["label"] == label]
        if row.empty:
            problems.append(f"diagnostics row missing for {label}")
            continue
        _expect(problems, f"{label} loose n", row["n_loose"].iloc[0], loose, 0)
        _expect(problems, f"{label} strict n", row["n_strict"].iloc[0], strict, 0)
        _expect(problems, f"{label} dropped n", row["n_dropped"].iloc[0], dropped, 0)

    ranking = pd.read_csv(tables / "event_ranking_metrics_strict.csv")
    for label, model, auc, lo, hi in (
        ("violation_disclosure_t1_strict", "finance-only IF", 0.6005, 0.5837, 0.6193),
        ("violation_disclosure_t1_strict", "fused IF", 0.5904, None, None),
        ("violation_disclosure_t1_loose", "finance-only IF", 0.5955, None, None),
    ):
        row = ranking[(ranking["label"] == label) & (ranking["model"] == model)]
        if row.empty:
            problems.append(f"ranking row missing for {label}/{model}")
            continue
        _expect(problems, f"{label}/{model} auc", row["auc"].iloc[0], auc)
        if lo is not None:
            _expect(problems, f"{label}/{model} auc_lo", row["auc_lo"].iloc[0], lo)
        if hi is not None:
            _expect(problems, f"{label}/{model} auc_hi", row["auc_hi"].iloc[0], hi)

    supervised = pd.read_csv(tables / "event_supervised_metrics_strict.csv")
    fused = supervised[supervised["feature_set"] == "delta_fused_vs_finance"]
    _expect(problems, "count of positive fused deltas", int((fused["oof_auc"] > 0).sum()), 6, 0)
    _expect(problems, "count of fused deltas", len(fused), 8, 0)
    for model, delta in (("logit", -0.0025), ("hgb", -0.0006)):
        row = fused[ (fused["label"] == "violation_disclosure_t1_strict") & (fused["model"] == model)]
        if row.empty:
            problems.append(f"supervised row missing for strict disclosure/{model}")
        else:
            _expect(problems, f"strict disclosure fused delta ({model})", row["oof_auc"].iloc[0], delta)

    control = pd.read_csv(tables / "lexicon_control_v01.csv")
    for spec, model, rho in (
        ("current_lexicon", "if_fused", -0.0176),
        ("current_lexicon", "if_text", -0.0259),
        ("v0.1_lexicon", "if_fused", -0.0211),
        ("v0.1_lexicon", "if_text", -0.0478),
    ):
        row = control[(control["spec"] == spec) & (control["model"] == model)]
        if row.empty:
            problems.append(f"control row missing for {spec}/{model}")
        else:
            _expect(problems, f"lexicon control {spec}/{model} rho", row["spearman_rho"].iloc[0], rho)

    return problems
