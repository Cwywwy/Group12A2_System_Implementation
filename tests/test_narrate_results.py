"""test_narrate_results.py

File:     tests/test_narrate_results.py
Author:   Group12A2 DSW Team
Purpose:  unit tests for the manuscript results narrators.
Module:   tests

Revision History:
  2026-11-06  initial version.
"""
import pandas as pd
import pytest

from src.reporting.narrate_results import (
    build_results_narrative,
    narrate_rq1,
    narrate_rq2,
    narrate_rq3,
)


def _metrics() -> pd.DataFrame:
    return pd.DataFrame([
        {"model": "if_finance", "spearman_rho": 0.250, "spearman_p": 0.010},
        {"model": "if_text", "spearman_rho": 0.180, "spearman_p": 0.040},
        {"model": "if_fused", "spearman_rho": 0.420, "spearman_p": 0.001},
        {"model": "ae_fused", "spearman_rho": 0.390, "spearman_p": 0.001},
    ])


def test_narrate_rq1_reports_rho_and_incremental_claim():
    text = narrate_rq1(_metrics())
    assert "0.420" in text
    assert "0.180" in text
    assert "incremental information" in text


def test_narrate_rq1_no_incremental_claim_when_fused_not_better():
    m = _metrics()
    m.loc[m["model"] == "if_fused", "spearman_rho"] = 0.100
    text = narrate_rq1(m)
    assert "does not improve rank agreement" in text


def test_narrate_rq2_lists_groups_and_top_feature():
    g = pd.DataFrame([
        {"group": "finance", "abs_shap_share": 0.61, "n_features": 6},
        {"group": "text", "abs_shap_share": 0.39, "n_features": 3},
    ])
    gl = pd.DataFrame([
        {"feature": "leverage", "mean_abs_shap": 0.050},
        {"feature": "uncertainty_ratio", "mean_abs_shap": 0.030},
        {"feature": "revenue_growth", "mean_abs_shap": 0.021},
    ])
    loc = pd.DataFrame([
        {"feature": "leverage", "shap_value": -0.040},
        {"feature": "uncertainty_ratio", "shap_value": 0.110},
        {"feature": "roa", "shap_value": 0.002},
    ])
    text = narrate_rq2(gl, g, loc)
    assert "finance" in text and "0.610" in text
    assert "leverage (0.050)" in text
    assert "uncertainty_ratio" in text


def test_narrate_rq3_lists_overlap_and_screening_sentence():
    ov = pd.DataFrame([
        {"model_a": "if_finance", "model_b": "if_finance", "top10_overlap": 1.0},
        {"model_a": "if_finance", "model_b": "if_fused", "top10_overlap": 0.71},
    ])
    tk = pd.DataFrame([
        {"model": "if_fused", "k": 0.05, "event_rate": 0.30, "enrichment": 4.2},
        {"model": "if_fused", "k": 0.10, "event_rate": 0.26, "enrichment": 3.7},
        {"model": "if_fused", "k": 0.15, "event_rate": 0.20, "enrichment": 2.9},
    ])
    text = narrate_rq3(ov, tk)
    assert "0.710" in text
    assert "0.260" in text
    assert "screening signal" in text
    assert "if_finance vs if_finance" not in text  # diagonal dropped


def test_build_results_narrative_requires_tables(tmp_path):
    with pytest.raises(FileNotFoundError):
        build_results_narrative(tmp_path)
