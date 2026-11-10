# -*- coding: utf-8 -*-
"""
test_models.py
Author: Group12A2 DSW Team
Purpose: Tests for the isolation forest and autoencoder models.
Module: tests

Revision History
-----------------
2026-11-05  initial version.
"""
import numpy as np
import pandas as pd

from src.models.autoencoder import AE_CONFIG, fit_autoencoder, reconstruction_errors
from src.models.isolation_forest import (
    anomaly_scores,
    fit_isolation_forest,
    top_k_indices,
)


def test_if_planted_outlier_ranks_most_anomalous():
    rng = np.random.default_rng(7)
    X = rng.normal(size=(200, 4))
    X = np.vstack([X, np.full((1, 4), 12.0)])
    frame = pd.DataFrame(X)
    model = fit_isolation_forest(frame, n_estimators=100, max_samples=64, seed=42)
    scores = anomaly_scores(model, frame)
    assert int(np.argmax(scores)) == 200


def test_if_max_samples_falls_back_when_sample_small():
    rng = np.random.default_rng(0)
    frame = pd.DataFrame(rng.normal(size=(40, 3)))
    model = fit_isolation_forest(frame, max_samples=256, seed=42)
    assert model.max_samples == 40


def test_top_k_indices_picks_largest_scores():
    scores = np.array([0.1, 0.9, 0.5, 0.3, 0.7])
    idx = top_k_indices(scores, k=0.4)
    assert len(idx) == 2
    assert set(idx.tolist()) == {1, 4}


def test_autoencoder_outlier_error_above_inliers():
    rng = np.random.default_rng(3)
    X = rng.normal(size=(300, 3))
    X = np.vstack([X, np.full((1, 3), 10.0)])
    frame = pd.DataFrame(X)
    config = dict(AE_CONFIG)
    config.update(hidden_layer_sizes=(4, 2, 4), max_iter=300, batch_size=64)
    model = fit_autoencoder(frame, config=config)
    errors = reconstruction_errors(model, frame)
    assert errors[-1] > np.quantile(errors[:-1], 0.9)
