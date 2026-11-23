# -*- coding: utf-8 -*-
"""
timing_eval.py
Author: Group12A2 DSW Team
Purpose: Build and evaluate the disclosure-date gated t+1 event labels that
         back the strict-timing robustness block.
Module: src.evaluation

The published t+1 label counts a violation as forward-looking when its calendar
year equals fiscal year + 1. Because annual reports are published in April of
t+1, an announcement dated January-March of t+1 precedes the accounts the
screening model sees. This module keeps the data preparation, the diagnostics
and the two evaluation blocks in one place so that the runner script holds no
analysis logic.

Revision History
----------------
2026-11-24  initial version: strict label frame, diagnostics, ranking and
            supervised blocks extracted from run_07c.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.config import ALL_FEATURES, FINANCE_FEATURES, TEXT_FEATURES
from src.data_ingestion.event_parser import (
    parse_audit_opinions,
    parse_violations,
    strict_forward_labels,
)
from src.evaluation.event_eval import (
    bootstrap_auc,
    oof_predictions,
    paired_delta_auc,
    ranking_metrics,
)

__all__ = [
    "FEATURE_SETS",
    "LABELS",
    "MODEL_KINDS",
    "SCORE_COLUMNS",
    "build_labelled_frame",
    "ranking_block",
    "strict_diagnostics",
    "supervised_block",
]

# (label, human description, loose counterpart or None)
LABELS = (
    ("mod_opinion", "Modified audit opinion (narrow)", None),
    ("mod_opinion_wide", "Modified audit opinion (wide)", None),
    ("violation_any_t1_strict", "Any violation announced after the report (t+1)", "violation_any_t1"),
    (
        "violation_disclosure_t1_strict",
        "Disclosure violation announced after the report (t+1)",
        "violation_disclosure_t1",
    ),
)

SCORE_COLUMNS = {
    "finance-only IF": "if_finance",
    "text-only IF": "if_text",
    "fused IF": "if_fused",
    "fused AE": "ae_fused",
    "Beneish M-Score": "m_score",
}

FEATURE_SETS = {
    "finance": tuple(FINANCE_FEATURES),
    "text": tuple(TEXT_FEATURES),
    "fused": tuple(ALL_FEATURES),
}

MODEL_KINDS = ("logit", "hgb")

_BINARY_COLUMNS = (
    "mod_opinion",
    "mod_opinion_wide",
    "violation_any_t1",
    "violation_disclosure_t1",
    "violation_any_t1_strict",
    "violation_disclosure_t1_strict",
    "violation_any_t1_loose",
    "violation_disclosure_t1_loose",
    "has_report_date",
)


def _read_codes(path: str | Path) -> pd.DataFrame:
    """Read a table and normalise the six-digit stock code."""
    frame = pd.read_csv(Path(path), dtype={"symbol": str})
    frame["symbol"] = frame["symbol"].str.zfill(6)
    return frame


def build_labelled_frame(
    events_path: str | Path,
    scores_path: str | Path,
    window_days: int | None = 365,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Merge the published scores with the loose and strict t+1 labels."""
    events = _read_codes(events_path)
    scores = _read_codes(scores_path)
    frame = scores.merge(
        events.drop(columns=["mod_opinion_wide"], errors="ignore"),
        on=["symbol", "fiscal_year"],
        how="left",
    )
    wide = events[["symbol", "fiscal_year", "mod_opinion_wide"]]
    frame = frame.merge(wide, on=["symbol", "fiscal_year"], how="left")

    sample = frame[["symbol", "fiscal_year"]].copy()
    strict = strict_forward_labels(
        sample,
        parse_audit_opinions(),
        parse_violations(),
        window_days=window_days,
    )
    frame = frame.merge(strict, on=["symbol", "fiscal_year"], how="left")
    for column in _BINARY_COLUMNS:
        if column in frame.columns:
            frame[column] = frame[column].fillna(0).astype(int)
    return frame, strict


def strict_diagnostics(frame: pd.DataFrame) -> pd.DataFrame:
    """Count loose versus strict labels and the share the gate removes."""
    rows: list[dict[str, object]] = []
    for label, description, loose in LABELS:
        if loose is None:
            continue
        loose_n = int(frame[loose].sum())
        strict_n = int(frame[label].sum())
        rows.append(
            {
                "label": label,
                "description": description,
                "n_firm_years": int(len(frame)),
                "n_loose": loose_n,
                "n_strict": strict_n,
                "n_dropped": loose_n - strict_n,
                "share_dropped": (loose_n - strict_n) / loose_n if loose_n else float("nan"),
                "rate_loose": float(frame[loose].mean()),
                "rate_strict": float(frame[label].mean()),
                "n_firm_years_without_report_date": int((frame["has_report_date"] == 0).sum()),
            }
        )
    return pd.DataFrame(rows)


def ranking_block(frame: pd.DataFrame, boot: int = 400) -> pd.DataFrame:
    """Ranking metrics on every label, with the loose counterparts appended."""
    blocks = [ranking_metrics(frame, label, SCORE_COLUMNS, n_boot=boot) for label, _, _ in LABELS]
    ranking = pd.concat(blocks, ignore_index=True)
    for _label, _description, loose in LABELS:
        if loose is None:
            continue
        compare = ranking_metrics(frame, loose, SCORE_COLUMNS, n_boot=boot)
        ranking = pd.concat(
            [ranking, compare.assign(label=f"{loose}_loose")], ignore_index=True
        )
    return ranking


def supervised_block(frame: pd.DataFrame, features: pd.DataFrame, boot: int = 400) -> pd.DataFrame:
    """Firm-grouped supervised comparison on the strict labels with paired deltas."""
    merged = frame.merge(
        features[["symbol", "fiscal_year", *ALL_FEATURES]],
        on=["symbol", "fiscal_year"],
        how="left",
    )
    rows: list[dict[str, object]] = []
    for label, _description, _loose in LABELS:
        if merged[label].nunique() < 2 or merged[label].sum() < 20:
            continue
        predictions: dict[str, np.ndarray] = {}
        for kind in MODEL_KINDS:
            for set_name, columns in FEATURE_SETS.items():
                oof = oof_predictions(merged, label, columns, kind=kind)
                predictions[f"{kind}:{set_name}"] = oof
                auc, lo, hi = bootstrap_auc(merged[label].to_numpy(), oof, n_boot=boot)
                rows.append(
                    {
                        "label": label,
                        "model": kind,
                        "feature_set": set_name,
                        "n_features": len(columns),
                        "n": int(np.sum(~np.isnan(oof))),
                        "n_events": int(merged[label].sum()),
                        "oof_auc": auc,
                        "oof_auc_lo": lo,
                        "oof_auc_hi": hi,
                    }
                )
        for kind in MODEL_KINDS:
            base = predictions.get(f"{kind}:finance")
            if base is None:
                continue
            for name in ("fused", "text"):
                other = predictions.get(f"{kind}:{name}")
                if other is None:
                    continue
                delta, lo, hi = paired_delta_auc(
                    merged[label].to_numpy(), base, other, n_boot=boot
                )
                rows.append(
                    {
                        "label": label,
                        "model": kind,
                        "feature_set": f"delta_{name}_vs_finance",
                        "n_features": 0,
                        "n": int(np.sum(~np.isnan(other))),
                        "n_events": int(merged[label].sum()),
                        "oof_auc": delta,
                        "oof_auc_lo": lo,
                        "oof_auc_hi": hi,
                    }
                )
    return pd.DataFrame(rows)
