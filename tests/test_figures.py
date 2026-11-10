# -*- coding: utf-8 -*-
"""
test_figures.py
Author: Group12A2 DSW Team
Purpose: Unit tests for src/reporting/figures.py (synthetic tables, Agg backend).
Module: tests

Revision History
-----------------
2026-11-06  initial version.
"""
import pandas as pd
import pytest

from src.reporting.figures import (
    make_all_figures,
    plot_group_contributions,
    plot_ranking_overlap,
    plot_score_distribution,
    plot_shap_importance,
    plot_topk_enrichment,
)


def _scores() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "symbol": ["600001"] * 4,
            "fiscal_year": [2021] * 4,
            "if_finance": [-0.1, 0.2, 0.3, 0.4],
            "if_text": [-0.2, 0.1, 0.2, 0.5],
            "if_fused": [-0.1, 0.3, 0.4, 0.6],
            "ae_fused": [0.05, 0.2, 0.3, 0.7],
            "m_score": [-3.0, -2.0, -1.0, 0.0],
            "benchmark_flag": [0, 1, 1, 1],
        }
    )


def _topk() -> pd.DataFrame:
    rows = [
        {"model": m, "k": k, "event_rate": 0.2 + i * 0.1, "enrichment": 1.5 + i}
        for i, m in enumerate(("if_finance", "if_text", "if_fused", "ae_fused"))
        for k in (0.05, 0.10, 0.15)
    ]
    return pd.DataFrame(rows)


def _overlap() -> pd.DataFrame:
    rows = [
        {"model_a": a, "model_b": b, "top10_overlap": 1.0 if a == b else 0.3}
        for a in ("if_finance", "if_text", "if_fused", "ae_fused")
        for b in ("if_finance", "if_text", "if_fused", "ae_fused")
    ]
    return pd.DataFrame(rows)


def test_score_distribution_writes_png(tmp_path):
    out = plot_score_distribution(_scores(), "if_fused", tmp_path / "dist.png")
    assert out.exists() and out.stat().st_size > 1000


def test_topk_enrichment_writes_png(tmp_path):
    out = plot_topk_enrichment(_topk(), tmp_path / "topk.png")
    assert out.exists() and out.stat().st_size > 1000


def test_group_contributions_writes_png(tmp_path):
    frame = pd.DataFrame(
        {"group": ["financial", "textual"], "abs_shap_share": [0.62, 0.38], "n_features": [6, 3]}
    )
    out = plot_group_contributions(frame, tmp_path / "groups.png")
    assert out.exists() and out.stat().st_size > 1000


def test_shap_importance_writes_png(tmp_path):
    frame = pd.DataFrame({"feature": [f"f{i}" for i in range(9)], "mean_abs_shap": range(9, 0, -1)})
    out = plot_shap_importance(frame, tmp_path / "shap.png")
    assert out.exists() and out.stat().st_size > 1000


def test_ranking_overlap_writes_png(tmp_path):
    out = plot_ranking_overlap(_overlap(), tmp_path / "overlap.png")
    assert out.exists() and out.stat().st_size > 1000


def test_make_all_figures_from_tables_dir(tmp_path):
    tables = tmp_path / "tables"
    tables.mkdir()
    _scores().to_csv(tables / "anomaly_scores.csv", index=False)
    _topk().to_csv(tables / "topk_metrics.csv", index=False)
    _overlap().to_csv(tables / "ranking_overlap.csv", index=False)
    pd.DataFrame({"feature": [f"f{i}" for i in range(9)], "mean_abs_shap": range(9, 0, -1)}).to_csv(
        tables / "shap_global.csv", index=False
    )
    pd.DataFrame(
        {"group": ["financial", "textual"], "abs_shap_share": [0.62, 0.38], "n_features": [6, 3]}
    ).to_csv(tables / "shap_group_contributions.csv", index=False)
    produced = make_all_figures(tables, tmp_path / "figures")
    assert len(produced) == 8  # 4 distributions + 4 summary figures
    assert all(p.exists() and p.stat().st_size > 1000 for p in produced)
