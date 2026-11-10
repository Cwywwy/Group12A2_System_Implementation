# -*- coding: utf-8 -*-
"""
test_pipeline.py
Author: Group12A2 DSW Team
Purpose: End-to-end tests for src.pipeline.run_pipeline on synthetic data.
Module: tests
"""
import numpy as np
import pandas as pd
import pytest

from src.pipeline import run_pipeline

N_ROWS = 48
N_ANOMALOUS = 8


def _make_feature_csv(tmp_path):
    rng = np.random.default_rng(42)
    years = np.tile([2021, 2022, 2023], N_ROWS // 3)
    symbols = [f"600{i:03d}" for i in range(1, N_ROWS + 1)]
    df = pd.DataFrame({
        "symbol": symbols,
        "fiscal_year": years,
        "industry_code_d": np.where(np.arange(N_ROWS) % 2 == 0, "C26", "C27"),
        "roa": rng.normal(0, 0.1, N_ROWS),
        "leverage": rng.normal(0.4, 0.1, N_ROWS),
        "revenue_growth": rng.normal(0.1, 0.2, N_ROWS),
        "ocf_to_assets": rng.normal(0.08, 0.05, N_ROWS),
        "receivables_turnover": rng.normal(8, 3, N_ROWS),
        "accruals_to_assets": rng.normal(0, 0.1, N_ROWS),
        "readability": rng.normal(0.01, 0.003, N_ROWS),
        "sentiment_balance": rng.normal(0, 0.01, N_ROWS),
        "uncertainty_ratio": rng.normal(0.005, 0.002, N_ROWS),
        "m_score": rng.uniform(-6, -2, N_ROWS),
    })
    # plant a few anomalous rows: extreme features + high M-Score
    anom = rng.choice(N_ROWS, size=N_ANOMALOUS, replace=False)
    for col in ("roa", "accruals_to_assets", "uncertainty_ratio"):
        df.loc[anom, col] = df.loc[anom, col] * 8
    df.loc[anom, "m_score"] = rng.uniform(-1.5, 2.0, N_ANOMALOUS)
    path = tmp_path / "synthetic_features.csv"
    df.to_csv(path, index=False)
    return path


def test_run_pipeline_writes_all_tables(tmp_path):
    feature_csv = _make_feature_csv(tmp_path)
    out_dir = tmp_path / "outputs"
    summary = run_pipeline(feature_csv, output_dir=out_dir)

    tables = out_dir / "tables"
    for name in (
        "model_metrics.csv",
        "topk_metrics.csv",
        "ranking_overlap.csv",
        "anomaly_scores.csv",
        "shap_global.csv",
        "shap_group_contributions.csv",
        "shap_local_top1.csv",
    ):
        assert (tables / name).exists(), f"missing {name}"

    assert summary["n_rows"] == N_ROWS
    metrics = pd.read_csv(tables / "model_metrics.csv")
    assert list(metrics["model"]) == ["if_finance", "if_text", "if_fused", "ae_fused"]
    topk = pd.read_csv(tables / "topk_metrics.csv")
    assert len(topk) == 24  # 2 benchmarks x 4 models x 3 k values
    assert set(topk["benchmark"]) == {"legacy", "calibrated"}
    overlap = pd.read_csv(tables / "ranking_overlap.csv")
    assert len(overlap) == 16  # 4 x 4 model pairs


def test_run_pipeline_top1_consistent(tmp_path):
    feature_csv = _make_feature_csv(tmp_path)
    out_dir = tmp_path / "outputs"
    summary = run_pipeline(feature_csv, output_dir=out_dir)
    scores = pd.read_csv(out_dir / "tables" / "anomaly_scores.csv")
    top_row = scores.loc[scores["if_fused"].idxmax()]
    assert str(top_row["symbol"]) == summary["top1_symbol"]


def test_run_pipeline_raises_on_all_missing(tmp_path):
    df = pd.DataFrame({
        "symbol": ["600001"],
        "fiscal_year": [2021],
        "roa": [np.nan],
        "leverage": [np.nan],
        "revenue_growth": [np.nan],
        "ocf_to_assets": [np.nan],
        "receivables_turnover": [np.nan],
        "accruals_to_assets": [np.nan],
        "readability": [np.nan],
        "sentiment_balance": [np.nan],
        "uncertainty_ratio": [np.nan],
        "m_score": [-3.0],
    })
    path = tmp_path / "bad.csv"
    df.to_csv(path, index=False)
    with pytest.raises(ValueError):
        run_pipeline(path, output_dir=tmp_path / "outputs")
