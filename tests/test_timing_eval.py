# -*- coding: utf-8 -*-
"""
test_timing_eval.py
Author: Group12A2 DSW Team
Purpose: Tests for the disclosure-date gated label evaluation (diagnostics,
         ranking block and supervised block bookkeeping).
Module: tests
"""
import numpy as np
import pandas as pd
import pytest

from src.evaluation.timing_eval import (
    LABELS,
    SCORE_COLUMNS,
    ranking_block,
    strict_diagnostics,
    supervised_block,
)


def _frame(n=300, seed=3):
    rng = np.random.default_rng(seed)
    frame = pd.DataFrame(
        {
            "symbol": [f"{i:06d}" for i in range(n)],
            "fiscal_year": np.tile([2021, 2022, 2023], n // 3 + 1)[:n],
            "if_finance": rng.normal(size=n),
            "if_text": rng.normal(size=n),
            "if_fused": rng.normal(size=n),
            "ae_fused": rng.normal(size=n),
            "m_score": rng.normal(size=n),
            "has_report_date": np.ones(n, dtype=int),
        }
    )
    signal = frame["if_finance"].to_numpy()
    frame["mod_opinion"] = 0
    frame["mod_opinion_wide"] = 0
    frame["violation_any_t1"] = (signal + rng.normal(scale=0.5, size=n) > 0.8).astype(int)
    frame["violation_disclosure_t1"] = (
        signal + rng.normal(scale=0.5, size=n) > 1.2
    ).astype(int)
    frame["violation_any_t1_strict"] = (
        frame["violation_any_t1"] * (rng.random(n) > 0.2)
    ).astype(int)
    frame["violation_disclosure_t1_strict"] = (
        frame["violation_disclosure_t1"] * (rng.random(n) > 0.2)
    ).astype(int)
    return frame


def _features(frame):
    features = frame[["symbol", "fiscal_year"]].copy()
    rng = np.random.default_rng(5)
    for column in ("roa", "leverage", "revenue_growth", "ocf_to_assets", "receivables_turnover", "accruals_to_assets"):
        features[column] = frame["if_finance"].to_numpy() + rng.normal(scale=0.3, size=len(frame))
    for column in ("readability", "sentiment_balance", "uncertainty_ratio"):
        features[column] = rng.normal(size=len(frame))
    return features


def test_strict_diagnostics_counts_only_the_pairs_with_a_loose_counterpart():
    frame = _frame()

    diagnostics = strict_diagnostics(frame)

    assert list(diagnostics["label"]) == [
        "violation_any_t1_strict",
        "violation_disclosure_t1_strict",
    ]
    for _, row in diagnostics.iterrows():
        assert row["n_dropped"] == row["n_loose"] - row["n_strict"]
        assert 0 <= row["share_dropped"] <= 1
        assert row["n_firm_years_without_report_date"] == 0


def test_ranking_block_appends_the_loose_counterparts():
    frame = _frame()

    ranking = ranking_block(frame, boot=40)

    labels = set(ranking["label"])
    assert "violation_any_t1_loose" in labels
    assert "violation_disclosure_t1_loose" in labels
    assert set(SCORE_COLUMNS) <= set(ranking["model"])
    for column in ("auc", "auc_lo", "auc_hi", "lift_10pct"):
        assert column in ranking.columns


def test_supervised_block_emits_feature_sets_and_paired_deltas():
    frame = _frame()
    features = _features(frame)

    supervised = supervised_block(frame, features, boot=40)

    assert set(supervised["model"]) == {"logit", "hgb"}
    feature_sets = set(supervised["feature_set"])
    assert {"finance", "text", "fused"} <= feature_sets
    assert {"delta_fused_vs_finance", "delta_text_vs_finance"} <= feature_sets
    deltas = supervised[supervised["feature_set"] == "delta_fused_vs_finance"]
    assert deltas["oof_auc_lo"].notna().all()
    assert (deltas["oof_auc_lo"] <= deltas["oof_auc_hi"]).all()


def test_label_table_is_consistent():
    labels = [label for label, _description, _loose in LABELS]
    assert labels[0] == "mod_opinion"
    assert len(labels) == len(set(labels))
    loose = [loose for _label, _description, loose in LABELS if loose]
    assert loose == ["violation_any_t1", "violation_disclosure_t1"]
