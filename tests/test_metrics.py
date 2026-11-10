# -*- coding: utf-8 -*-
"""
test_metrics.py
Author: Group12A2 DSW Team
Purpose: Tests for the evaluation metrics.
Module: tests

Revision History
-----------------
2026-11-05  initial version.
"""
import numpy as np

from src.evaluation.metrics import (
    enrichment_ratio,
    spearman_corr,
    top_k_event_rate,
    top_k_overlap,
)


def test_spearman_perfect_positive_correlation():
    rho, p_value = spearman_corr(np.array([1.0, 2.0, 3.0]), np.array([10.0, 20.0, 30.0]))
    assert rho == 1.0
    assert p_value < 0.05


def test_spearman_ignores_nan_pairs():
    rho, _ = spearman_corr(np.array([1.0, np.nan, 3.0, 4.0]), np.array([2.0, 99.0, 6.0, 8.0]))
    assert rho == 1.0


def test_event_rate_and_enrichment_exact():
    scores = np.array([0.9, 0.1, 0.8])
    flags = np.array([1, 0, 1])
    assert top_k_event_rate(scores, flags, k=2 / 3) == 1.0
    assert enrichment_ratio(scores, flags, k=2 / 3) == 1.5


def test_top_k_overlap_exact():
    a = np.array([0.9, 0.8, 0.1, 0.0])
    b = np.array([0.0, 0.8, 0.9, 0.1])
    assert top_k_overlap(a, b, k=0.5) == 0.5
