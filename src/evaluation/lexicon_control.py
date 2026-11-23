# -*- coding: utf-8 -*-
"""
lexicon_control.py
Author: Group12A2 DSW Team
Purpose: Hold the financial data, sample, preprocessing and model fixed and
         swap only the dictionary-era text features, so the v0.1 versus v0.2
         movement can be attributed to the lexicon or to the repair.
Module: src.evaluation

Revision History
----------------
2026-11-24  initial version: archive loader, variant scoring and control table
            extracted from run_08.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.config import (
    ALL_FEATURES,
    BENEISH_THRESHOLD,
    BENEISH_TOP_QUANTILE,
    FINANCE_FEATURES,
    TEXT_FEATURES,
)
from src.evaluation.metrics import enrichment_ratio, spearman_corr, top_k_overlap
from src.features.standardise import standardise_within_groups, winsorize_columns
from src.models.isolation_forest import (
    anomaly_scores,
    fit_isolation_forest,
    top_k_indices,
)

__all__ = [
    "K_VALUES",
    "control_table",
    "corpus_diagnostics",
    "load_archive_text_features",
    "prepare_control_frame",
    "score_variant",
    "variant_overlap",
]

K_VALUES = (0.05, 0.10, 0.15)


def load_archive_text_features(directory: str | Path) -> pd.DataFrame:
    """Read the archived v0.1 text features, one CSV per year.

    The archived files carry no ``fiscal_year`` column, so the year is taken
    from the file name and the three text columns are prefixed ``v01_``.
    """
    frames = []
    for path in sorted(Path(directory).glob("text_features_*.csv")):
        year = int(path.stem.split("_")[-1])
        frame = pd.read_csv(path, dtype={"symbol": str})
        frame["symbol"] = frame["symbol"].str.zfill(6)
        frame["fiscal_year"] = year
        frames.append(frame)
    if not frames:
        raise FileNotFoundError(f"no archive text features under {directory}")
    archive = pd.concat(frames, ignore_index=True)
    keep = ["symbol", "fiscal_year", *TEXT_FEATURES, "n_tokens"]
    archive = archive[[column for column in keep if column in archive.columns]]
    return archive.rename(
        columns={column: f"v01_{column}" for column in TEXT_FEATURES + ("n_tokens",)}
    )


def prepare_control_frame(features: pd.DataFrame, archive: pd.DataFrame) -> pd.DataFrame:
    """Inner-join the current and the archived text features on the same rows."""
    merged = features.merge(archive, on=["symbol", "fiscal_year"], how="inner")
    needed = (
        list(ALL_FEATURES)
        + ["m_score", "industry_code_d"]
        + [f"v01_{column}" for column in TEXT_FEATURES]
    )
    return merged.dropna(subset=needed).copy()


def score_variant(work: pd.DataFrame, text_columns: tuple[str, ...]) -> dict[str, object]:
    """Fit the three matrices with one text measurement and return their scores."""
    columns = list(FINANCE_FEATURES) + list(text_columns)
    winsorised = winsorize_columns(work, columns)
    standardised = standardise_within_groups(winsorised, columns)
    matrices = {
        "if_finance": standardised[list(FINANCE_FEATURES)],
        "if_text": standardised[list(text_columns)],
        "if_fused": standardised[columns],
    }

    results: dict[str, object] = {}
    for name, matrix in matrices.items():
        scores = anomaly_scores(fit_isolation_forest(matrix), matrix)
        rho, p_value = spearman_corr(scores, work["m_score"].to_numpy())
        results[name] = {"scores": scores, "rho": rho, "p": p_value}
    results["fused_scores"] = results["if_fused"]["scores"]
    return results


def corpus_diagnostics(work: pd.DataFrame) -> pd.DataFrame:
    """Compare the archived and the current text features row by row."""
    same_tokens = np.isclose(work["n_tokens"], work["v01_n_tokens"], rtol=1e-9)
    return pd.DataFrame(
        [
            {
                "n_rows": len(work),
                "n_firms": int(work["symbol"].nunique()),
                "share_identical_token_count": float(same_tokens.mean()),
                "mean_abs_readability_diff": float(
                    (work["readability"] - work["v01_readability"]).abs().mean()
                ),
                "mean_abs_sentiment_diff": float(
                    (work["sentiment_balance"] - work["v01_sentiment_balance"]).abs().mean()
                ),
                "mean_abs_uncertainty_diff": float(
                    (work["uncertainty_ratio"] - work["v01_uncertainty_ratio"]).abs().mean()
                ),
                "corr_readability": float(work["readability"].corr(work["v01_readability"])),
                "corr_sentiment": float(
                    work["sentiment_balance"].corr(work["v01_sentiment_balance"])
                ),
                "corr_uncertainty": float(
                    work["uncertainty_ratio"].corr(work["v01_uncertainty_ratio"])
                ),
            }
        ]
    )


def control_table(
    current: dict[str, object], legacy: dict[str, object], work: pd.DataFrame
) -> pd.DataFrame:
    """Rank correlation and benchmark enrichment for both text measurements."""
    legacy_flags = (work["m_score"].to_numpy() > BENEISH_THRESHOLD).astype(int)
    calibrated_flags = np.zeros(len(work), dtype=int)
    calibrated_flags[top_k_indices(work["m_score"].to_numpy(), BENEISH_TOP_QUANTILE)] = 1

    rows: list[dict[str, object]] = []
    for spec_name, spec in (("current_lexicon", current), ("v0.1_lexicon", legacy)):
        for model in ("if_finance", "if_text", "if_fused"):
            scores = spec[model]["scores"]
            row: dict[str, object] = {
                "spec": spec_name,
                "model": model,
                "n": len(work),
                "spearman_rho": spec[model]["rho"],
                "spearman_p": spec[model]["p"],
                "enrichment_legacy_k10": enrichment_ratio(scores, legacy_flags, 0.10),
                "enrichment_calibrated_k10": enrichment_ratio(scores, calibrated_flags, 0.10),
            }
            for k in K_VALUES:
                row[f"enrichment_calibrated_k{int(round(k * 100))}"] = enrichment_ratio(
                    scores, calibrated_flags, k
                )
            rows.append(row)
    return pd.DataFrame(rows)


def variant_overlap(current: dict[str, object], legacy: dict[str, object]) -> pd.DataFrame:
    """Top-decile overlap between the two text measurements."""
    return pd.DataFrame(
        [
            {
                "pair": "fused_current_vs_v01",
                "top10_overlap": top_k_overlap(current["fused_scores"], legacy["fused_scores"], k=0.10),
            },
            {
                "pair": "text_current_vs_v01",
                "top10_overlap": top_k_overlap(
                    current["if_text"]["scores"], legacy["if_text"]["scores"], k=0.10
                ),
            },
        ]
    )
