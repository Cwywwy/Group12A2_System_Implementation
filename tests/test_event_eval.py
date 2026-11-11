# -*- coding: utf-8 -*-
"""
test_event_eval.py
Author: Group12A2 DSW Team
Purpose: Tests for the external-outcome evaluation helpers (AUC with bootstrap,
         top-queue enrichment and recall, grouped out-of-fold predictions and
         paired AUC differences).
Module: tests
"""
import numpy as np
import pandas as pd
import pytest

from src.evaluation.event_eval import (
    bootstrap_auc,
    bootstrap_lift,
    oof_predictions,
    paired_delta_auc,
    ranking_metrics,
)


def _synthetic(n=400, seed=42):
    rng = np.random.default_rng(seed)
    signal = rng.normal(size=n)
    labels = (signal + rng.normal(scale=0.5, size=n) > 1.0).astype(int)
    frame = pd.DataFrame(
        {
            "symbol": [f"{i:06d}" for i in range(n)],
            "fiscal_year": np.tile([2021, 2022, 2023, 2021], n // 4),
            "event": labels,
            "good_score": signal,
            "noise_score": rng.normal(size=n),
        }
    )
    for name in ("roa", "leverage", "revenue_growth"):
        frame[name] = signal * 0.4 + rng.normal(size=n)
    return frame


def test_bootstrap_auc_detects_signal_and_interval():
    frame = _synthetic()
    auc, lo, hi = bootstrap_auc(
        frame["event"].to_numpy(), frame["good_score"].to_numpy(), n_boot=100
    )
    assert auc > 0.7
    assert lo < auc < hi


def test_bootstrap_auc_noise_is_near_half():
    frame = _synthetic()
    auc, _, _ = bootstrap_auc(
        frame["event"].to_numpy(), frame["noise_score"].to_numpy(), n_boot=100
    )
    assert 0.4 < auc < 0.6


def test_bootstrap_lift_matches_manual_calculation():
    frame = _synthetic()
    labels = frame["event"].to_numpy()
    scores = frame["good_score"].to_numpy()
    lift, lo, hi = bootstrap_lift(labels, scores, k=0.10, n_boot=50)
    base = labels.mean()
    top = np.argsort(-scores, kind="stable")[: max(1, int(round(len(labels) * 0.10)))]
    manual = labels[top].mean() / base
    assert lift == pytest.approx(manual, rel=1e-9)
    assert lo <= lift <= hi


def test_ranking_metrics_reports_lift_and_recall():
    frame = _synthetic()
    table = ranking_metrics(
        frame,
        "event",
        {"good": "good_score", "noise": "noise_score"},
        n_boot=50,
    )
    assert len(table) == 2
    good = table[table["model"] == "good"].iloc[0]
    assert good["auc"] > 0.7
    assert good["lift_10pct"] > 1.5
    assert 0.0 < good["recall_10pct"] <= 1.0
    assert "pr_auc" in table.columns


def test_oof_predictions_are_probabilities_and_learn():
    frame = _synthetic()
    oof = oof_predictions(frame, "event", ("roa", "leverage", "revenue_growth"))
    assert len(oof) == len(frame)
    assert np.all((oof >= 0) & (oof <= 1))
    auc, _, _ = bootstrap_auc(frame["event"].to_numpy(), oof, n_boot=50)
    assert auc > 0.65


def test_paired_delta_auc_is_zero_for_identical_scores():
    frame = _synthetic()
    labels = frame["event"].to_numpy()
    scores = frame["good_score"].to_numpy()
    delta, lo, hi = paired_delta_auc(labels, scores, scores, n_boot=50)
    assert delta == pytest.approx(0.0)
    assert lo <= 0.0 <= hi
