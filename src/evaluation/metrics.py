# -*- coding: utf-8 -*-
"""
metrics.py
Author: Group12A2 DSW Team
Purpose: The three evaluation metrics plus top-k overlap for ranking stability.
Module: src/evaluation

Revision History
-----------------
2026-11-05  initial version.
"""
import numpy as np
from scipy.stats import spearmanr

from src.models.isolation_forest import top_k_indices


def spearman_corr(scores: np.ndarray, benchmark: np.ndarray) -> tuple[float, float]:
    """Spearman rho and p-value between anomaly scores and the M-Score benchmark."""
    mask = ~(np.isnan(scores) | np.isnan(benchmark))
    if mask.sum() < 3:
        return float("nan"), float("nan")
    rho, p_value = spearmanr(scores[mask], benchmark[mask])
    return float(rho), float(p_value)


def top_k_event_rate(scores: np.ndarray, flags: np.ndarray, k: float = 0.10) -> float:
    """Share of the top-k review list that is flagged by the benchmark."""
    idx = top_k_indices(scores, k)
    return float(np.mean(flags[idx]))


def enrichment_ratio(scores: np.ndarray, flags: np.ndarray, k: float = 0.10) -> float:
    """Event rate in the top-k list relative to the full-sample event rate."""
    baseline = float(np.mean(flags))
    if baseline == 0.0:
        return float("nan")
    return top_k_event_rate(scores, flags, k) / baseline


def top_k_overlap(scores_a: np.ndarray, scores_b: np.ndarray, k: float = 0.10) -> float:
    """Share of the top-k set shared by two rankings (RQ3: ranking stability)."""
    set_a = set(top_k_indices(scores_a, k))
    set_b = set(top_k_indices(scores_b, k))
    return float(len(set_a & set_b) / len(set_a))
