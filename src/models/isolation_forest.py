# -*- coding: utf-8 -*-
"""
isolation_forest.py
Author: Group12A2 DSW Team
Purpose: Isolation Forest main model with direction-corrected anomaly scores.
Module: src/models

All hyperparameters are fixed in src/config.py in advance and are never tuned
on outcomes (per the proposal). sklearn's score_samples returns higher values
for normal points, so the score is negated: higher = more anomalous.

Revision History
-----------------
2026-11-05  initial version.
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from src.config import IF_MAX_SAMPLES, IF_N_ESTIMATORS, SEED


def fit_isolation_forest(X: pd.DataFrame, n_estimators: int = IF_N_ESTIMATORS, max_samples: int = IF_MAX_SAMPLES, seed: int = SEED) -> IsolationForest:
    """Fit the model; max_samples falls back to the whole sample when smaller."""
    model = IsolationForest(
        n_estimators=n_estimators,
        max_samples=min(max_samples, len(X)),
        random_state=seed,
        n_jobs=-1,
    )
    model.fit(X)
    return model


def anomaly_scores(model: IsolationForest, X: pd.DataFrame) -> np.ndarray:
    """Direction-corrected scores: higher = more anomalous."""
    return -model.score_samples(X)


def top_k_indices(scores: np.ndarray, k: float = 0.10) -> np.ndarray:
    """Indices of the top-k most anomalous rows (k as a fraction of the sample)."""
    n_top = max(1, int(round(len(scores) * k)))
    return np.argsort(-scores)[:n_top]
