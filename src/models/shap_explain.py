# -*- coding: utf-8 -*-
"""
shap_explain.py
Author: Group12A2 DSW Team
Purpose: SHAP global and local explanations of the Isolation Forest ranking.
Module: src/models

Group-level contributions (finance vs text) answer RQ2; per-sample values
support local explanations of individual review-priority firms.

Revision History
-----------------
2026-11-05  initial version.
"""
import numpy as np
import pandas as pd
import shap
from sklearn.ensemble import IsolationForest

from src.config import FEATURE_GROUPS


def shap_values(model: IsolationForest, X: pd.DataFrame) -> np.ndarray:
    """TreeExplainer SHAP values for the fitted Isolation Forest."""
    explainer = shap.TreeExplainer(model)
    return np.asarray(explainer.shap_values(X))


def global_importance(shap_matrix: np.ndarray, columns: list[str]) -> pd.DataFrame:
    """Mean absolute SHAP value per feature, sorted descending."""
    importance = np.mean(np.abs(shap_matrix), axis=0)
    return pd.DataFrame({"feature": columns, "mean_abs_shap": importance}).sort_values(
        "mean_abs_shap", ascending=False
    ).reset_index(drop=True)


def group_contributions(shap_matrix: np.ndarray, columns: list[str]) -> pd.DataFrame:
    """Absolute SHAP contribution per feature group (RQ2: finance vs text)."""
    rows = []
    for group, features in FEATURE_GROUPS.items():
        idx = [columns.index(f) for f in features if f in columns]
        share = float(np.abs(shap_matrix[:, idx]).sum() / np.abs(shap_matrix).sum())
        rows.append({"group": group, "abs_shap_share": share, "n_features": len(idx)})
    return pd.DataFrame(rows)


def local_explanation(shap_matrix: np.ndarray, columns: list[str], row_index: int) -> pd.DataFrame:
    """Per-feature SHAP values for one firm-year row."""
    return pd.DataFrame({"feature": columns, "shap_value": shap_matrix[row_index]}).sort_values(
        "shap_value", key=lambda s: s.abs(), ascending=False
    ).reset_index(drop=True)
