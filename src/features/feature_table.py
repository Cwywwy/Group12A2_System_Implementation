# -*- coding: utf-8 -*-
"""
feature_table.py
Author: Group12A2 DSW Team
Purpose: Merge the sample frame, financial features, Beneish M-Score and the
         three textual features into the single fused feature table consumed
         by the modelling pipeline.
Module: src/features

Revision History
-----------------
2026-11-05  initial version: merge + text-quality classification.
2026-11-06  defensive: build the combined sga column from sga_sales + sga_admin when
            the intermediate table does not carry it (parser normally provides it).
"""
import pandas as pd

from src.config import FINANCE_FEATURES
from src.features.beneish import compute_beneish
from src.features.financial import compute_finance_features

MIN_MDA_TOKENS = 300
TEXT_COLS = ["readability", "sentiment_balance", "uncertainty_ratio"]


def classify_text_quality(text_status: str | None, n_tokens: float | None) -> str:
    """Label each firm-year's text evidence for QC downstream.

    missing   - no extraction row at all (PDF not downloaded/processed yet)
    suspicious - heading not found, or an implausibly short slice (scan / TOC only)
    ok        - usable MD&A evidence
    """
    if pd.isna(n_tokens):
        return "missing"
    if text_status == "no_mda" or n_tokens < MIN_MDA_TOKENS:
        return "suspicious"
    return "ok"


def build_feature_table(
    sample: pd.DataFrame,
    finance_intermediate: pd.DataFrame,
    text_frames: dict[int, pd.DataFrame],
) -> pd.DataFrame:
    """Fuse sample frame + finance features + M-Score + text features.

    sample: columns symbol, fiscal_year, industry_code_d, ...
    finance_intermediate: FINANCE_COLS schema incl. base year 2020
    text_frames: {fiscal_year: text features df from run_05}
    """
    finance_intermediate = finance_intermediate.copy()
    if "sga" not in finance_intermediate.columns:
        parts = [c for c in ("sga_sales", "sga_admin") if c in finance_intermediate.columns]
        finance_intermediate["sga"] = (
            finance_intermediate[parts].sum(axis=1, min_count=1) if parts else pd.NA
        )
    fin = compute_beneish(compute_finance_features(finance_intermediate))
    fin = fin[["symbol", "fiscal_year", *FINANCE_FEATURES, "m_score"]].copy()
    fin["symbol"] = fin["symbol"].astype(str).str.zfill(6)

    text_dfs = []
    for year, frame in text_frames.items():
        if frame is None or frame.empty:
            continue
        part = frame.copy()
        part["symbol"] = part["symbol"].astype(str).str.zfill(6)
        part["fiscal_year"] = int(year)
        text_dfs.append(part)
    text = pd.concat(text_dfs, ignore_index=True) if text_dfs else pd.DataFrame()
    if not text.empty:
        text = text.rename(columns={"status": "text_status"})
        text = text[["symbol", "fiscal_year", "text_status", *TEXT_COLS, "n_tokens", "n_sentences"]]

    merged = sample.merge(fin, on=["symbol", "fiscal_year"], how="left")
    if not text.empty:
        merged = merged.merge(text, on=["symbol", "fiscal_year"], how="left")
    else:
        merged = merged.assign(text_status=None, **{c: None for c in TEXT_COLS},
                               n_tokens=None, n_sentences=None)

    merged["text_quality"] = [
        classify_text_quality(status, tokens)
        for status, tokens in zip(merged["text_status"], merged["n_tokens"])
    ]
    return merged
