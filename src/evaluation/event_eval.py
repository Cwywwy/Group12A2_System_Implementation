# -*- coding: utf-8 -*-
"""
event_eval.py
Author: Group12A2 DSW Team
Purpose: Evaluate anomaly rankings and supervised feature sets against real
         firm-year events (modified audit opinions, forward violations) with
         AUC, PR-AUC and top-queue enrichment, all with bootstrap intervals.
Module: src/evaluation

Two evaluation modes
--------------------
1. ``ranking_metrics``: treat an existing score column (Isolation Forest,
   autoencoder, Beneish M-Score) as a risk ranking and ask how well it ranks
   firms that later receive a regulatory event. This keeps the unsupervised
   headline of the paper and adds an external-outcome check.
2. ``oof_predictions`` + ``paired_delta_auc``: supervised comparison of the
   finance-only, text-only and fused feature sets under grouped cross
   validation, so a positive incremental value of text can be tested directly.

Revision History
----------------
2026-11-11  initial version.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from src.models.isolation_forest import top_k_indices

DEFAULT_BOOTSTRAP = 1000


def _safe_auc(labels: np.ndarray, scores: np.ndarray) -> float:
    if len(np.unique(labels)) < 2:
        return float("nan")
    return float(roc_auc_score(labels, scores))


def _safe_pr_auc(labels: np.ndarray, scores: np.ndarray) -> float:
    if len(np.unique(labels)) < 2:
        return float("nan")
    return float(average_precision_score(labels, scores))


def bootstrap_auc(
    labels: np.ndarray,
    scores: np.ndarray,
    n_boot: int = DEFAULT_BOOTSTRAP,
    seed: int = 42,
) -> tuple[float, float, float]:
    """AUC plus percentile bootstrap interval (resampling firm-year rows)."""
    labels = np.asarray(labels)
    scores = np.asarray(scores, dtype=float)
    mask = ~np.isnan(scores)
    labels, scores = labels[mask], scores[mask]
    point = _safe_auc(labels, scores)
    if np.isnan(point) or len(labels) < 10:
        return point, float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    n = len(labels)
    draws = np.empty(n_boot)
    for i in range(n_boot):
        idx = rng.integers(0, n, n)
        draws[i] = _safe_auc(labels[idx], scores[idx])
    lo, hi = np.nanpercentile(draws, [2.5, 97.5])
    return point, float(lo), float(hi)


def bootstrap_lift(
    labels: np.ndarray,
    scores: np.ndarray,
    k: float = 0.10,
    n_boot: int = DEFAULT_BOOTSTRAP,
    seed: int = 42,
) -> tuple[float, float, float]:
    """Enrichment in the top-k queue relative to the base rate, with interval."""
    labels = np.asarray(labels)
    scores = np.asarray(scores, dtype=float)
    mask = ~np.isnan(scores)
    labels, scores = labels[mask], scores[mask]
    base = float(np.mean(labels)) if len(labels) else float("nan")
    if not base or np.isnan(base):
        return float("nan"), float("nan"), float("nan")
    idx = top_k_indices(scores, k)
    point = float(np.mean(labels[idx])) / base
    rng = np.random.default_rng(seed + 1)
    n = len(labels)
    draws = np.empty(n_boot)
    for i in range(n_boot):
        pick = rng.integers(0, n, n)
        lab, sc = labels[pick], scores[pick]
        b = float(np.mean(lab))
        if b == 0:
            draws[i] = np.nan
            continue
        top = top_k_indices(sc, k)
        draws[i] = float(np.mean(lab[top])) / b
    lo, hi = np.nanpercentile(draws, [2.5, 97.5])
    return point, float(lo), float(hi)


def ranking_metrics(
    frame: pd.DataFrame,
    label: str,
    score_columns: dict[str, str],
    k_values: tuple[float, ...] = (0.05, 0.10, 0.15),
    n_boot: int = DEFAULT_BOOTSTRAP,
    seed: int = 42,
) -> pd.DataFrame:
    """Ranking quality of each score column for one binary event label."""
    rows: list[dict[str, object]] = []
    labels = frame[label].to_numpy()
    for model, column in score_columns.items():
        scores = frame[column].to_numpy(dtype=float)
        auc, auc_lo, auc_hi = bootstrap_auc(labels, scores, n_boot=n_boot, seed=seed)
        pr_auc = _safe_pr_auc(labels[~np.isnan(scores)], scores[~np.isnan(scores)])
        row: dict[str, object] = {
            "label": label,
            "model": model,
            "n": int(np.sum(~np.isnan(scores))),
            "n_events": int(np.nansum(labels[~np.isnan(scores)])),
            "base_rate": float(np.mean(labels[~np.isnan(scores)])),
            "auc": auc,
            "auc_lo": auc_lo,
            "auc_hi": auc_hi,
            "pr_auc": pr_auc,
        }
        valid = ~np.isnan(scores)
        for k in k_values:
            lift, lo, hi = bootstrap_lift(labels, scores, k=k, n_boot=n_boot, seed=seed)
            tag = f"{int(round(k * 100))}pct"
            row[f"lift_{tag}"] = lift
            row[f"lift_{tag}_lo"] = lo
            row[f"lift_{tag}_hi"] = hi
            top = top_k_indices(scores[valid], k)
            events_total = float(np.sum(labels[valid]))
            row[f"recall_{tag}"] = (
                float(np.sum(labels[valid][top])) / events_total
                if events_total
                else float("nan")
            )
        rows.append(row)
    return pd.DataFrame(rows)


def _make_model(kind: str, seed: int = 42) -> Pipeline:
    if kind == "logit":
        return Pipeline(
            [
                ("impute", SimpleImputer(strategy="median")),
                ("scale", StandardScaler()),
                (
                    "model",
                    LogisticRegression(
                        max_iter=2000, class_weight="balanced", random_state=seed
                    ),
                ),
            ]
        )
    if kind == "hgb":
        return Pipeline(
            [
                ("impute", SimpleImputer(strategy="median")),
                (
                    "model",
                    HistGradientBoostingClassifier(
                        max_iter=300,
                        learning_rate=0.05,
                        max_leaf_nodes=15,
                        min_samples_leaf=40,
                        l2_regularization=1.0,
                        random_state=seed,
                    ),
                ),
            ]
        )
    raise ValueError(f"unknown model kind: {kind}")


def oof_predictions(
    frame: pd.DataFrame,
    label: str,
    features: tuple[str, ...],
    kind: str = "logit",
    n_splits: int = 5,
    seed: int = 42,
) -> np.ndarray:
    """Out-of-fold predicted probabilities with firm-grouped folds.

    Folds are grouped on ``symbol`` so that the same firm never appears in both
    the training and the validation part; without this the panel structure
    leaks and AUCs become optimistic.
    """
    y = frame[label].to_numpy(dtype=int)
    X = frame[list(features)].to_numpy(dtype=float)
    groups = frame["symbol"].to_numpy()
    oof = np.full(len(frame), np.nan)
    splitter = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    for train_idx, test_idx in splitter.split(X, y, groups):
        model = _make_model(kind, seed=seed)
        model.fit(X[train_idx], y[train_idx])
        oof[test_idx] = model.predict_proba(X[test_idx])[:, 1]
    return oof


def paired_delta_auc(
    labels: np.ndarray,
    scores_a: np.ndarray,
    scores_b: np.ndarray,
    n_boot: int = DEFAULT_BOOTSTRAP,
    seed: int = 42,
) -> tuple[float, float, float]:
    """AUC(b) - AUC(a) with a paired bootstrap interval on the same rows."""
    labels = np.asarray(labels)
    a = np.asarray(scores_a, dtype=float)
    b = np.asarray(scores_b, dtype=float)
    mask = ~(np.isnan(a) | np.isnan(b))
    labels, a, b = labels[mask], a[mask], b[mask]
    point = _safe_auc(labels, b) - _safe_auc(labels, a)
    rng = np.random.default_rng(seed + 2)
    n = len(labels)
    draws = np.empty(n_boot)
    for i in range(n_boot):
        idx = rng.integers(0, n, n)
        draws[i] = _safe_auc(labels[idx], b[idx]) - _safe_auc(labels[idx], a[idx])
    lo, hi = np.nanpercentile(draws, [2.5, 97.5])
    return float(point), float(lo), float(hi)
