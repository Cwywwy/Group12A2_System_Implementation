# -*- coding: utf-8 -*-
"""
autoencoder.py
Author: Group12A2 DSW Team
Purpose: Autoencoder robustness ranking via reconstruction error (sklearn MLPRegressor).
Module: src/models

The full hyperparameter set is recorded to outputs/reports/autoencoder_config.json,
as the outline requires (architecture, bottleneck width, activation, regularisation,
optimiser, epochs, early stopping, batch size, seed).

Revision History
-----------------
2026-11-05  initial version.
"""
import inspect
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.neural_network import MLPRegressor

from src.config import OUTPUTS, SEED

AE_CONFIG = {
    "hidden_layer_sizes": (16, 8, 16),
    "bottleneck_width": 8,
    "activation": "relu",
    "solver": "adam",
    "alpha": 1e-4,
    "batch_size": 256,
    "learning_rate_init": 1e-3,
    "max_iter": 500,
    "early_stopping": True,
    "n_iter_no_change": 20,
    "validation_fraction": 0.1,
    "tol": 1e-6,
    "random_state": SEED,
    "loss": "squared_error",
}


def _mlp_params(config: dict) -> dict:
    """Keep only keys accepted by MLPRegressor (bottleneck_width is documentation-only)."""
    valid = inspect.signature(MLPRegressor.__init__).parameters
    return {k: v for k, v in config.items() if k in valid}


def fit_autoencoder(X: pd.DataFrame, config: dict | None = None) -> MLPRegressor:
    """Fit the autoencoder with X as both input and target."""
    config = config or AE_CONFIG
    model = MLPRegressor(**_mlp_params(config))
    model.fit(X, X)
    return model


def reconstruction_errors(model: MLPRegressor, X: pd.DataFrame) -> np.ndarray:
    """Per-sample mean squared reconstruction error; higher = more anomalous."""
    reconstructed = model.predict(X)
    return np.mean((X.to_numpy() - reconstructed) ** 2, axis=1)


def record_autoencoder_config(config: dict | None = None, out_path: Path | None = None) -> Path:
    """Persist the exact configuration used, as required for reproducibility."""
    config = config or AE_CONFIG
    out_path = out_path or (OUTPUTS / "reports" / "autoencoder_config.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(config, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    return out_path
