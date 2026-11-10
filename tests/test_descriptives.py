# -*- coding: utf-8 -*-
"""
test_descriptives.py
Author: Group12A2 DSW Team
Purpose: Unit tests for src/reporting/descriptives.py.
Module: tests

Revision History
-----------------
2026-11-06  initial version.
"""
import pandas as pd
import pytest

from src.reporting.descriptives import (
    describe_benchmark,
    describe_download_coverage,
    describe_feature_summary,
    describe_text_coverage,
)


def _make_feature_table() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "symbol": ["000001", "000001", "000002", "000002", "000003"],
            "fiscal_year": [2021, 2022, 2021, 2022, 2021],
            "roa": [0.05, 0.06, None, 0.04, 0.03],
            "readability": [0.008, 0.009, 0.007, None, 0.010],
            "sentiment_balance": [0.01, 0.02, 0.03, 0.04, 0.05],
            "uncertainty_ratio": [0.002, 0.003, 0.004, 0.005, 0.006],
            "text_quality": ["ok", "ok", "suspicious", "missing", "ok"],
            "m_score": [-3.0, -1.5, -2.0, None, -1.2],
        }
    )


def _make_audit() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "symbol": ["000001", "000001", "000002", "000002", "000003"],
            "fiscal_year": [2021, 2022, 2021, 2022, 2021],
            "status": ["ok", "ok", "missing", "ok", "ok"],
            "log_title": ["2021年年度报告"] * 5,
        }
    )


def test_download_coverage_counts_and_ratio():
    cov = describe_download_coverage(_make_audit())
    assert cov.loc[2021, "ok"] == 2
    assert cov.loc[2021, "missing"] == 1
    assert cov.loc[2021, "coverage"] == pytest.approx(0.6667)
    assert cov.loc[2022, "ok"] == 2
    assert cov.loc[2022, "missing"] == 0
    assert cov.loc[2022, "coverage"] == 1.0


def test_text_coverage_counts():
    cov = describe_text_coverage(_make_feature_table())
    assert cov.loc[2021, "ok"] == 2
    assert cov.loc[2021, "suspicious"] == 1
    assert cov.loc[2022, "missing"] == 1
    assert cov.loc[2021, "share_ok"] == pytest.approx(0.6667)


def test_feature_summary_ignores_nan():
    summary = describe_feature_summary(_make_feature_table())
    roa = summary.set_index("feature").loc["roa"]
    assert roa["n"] == 4
    assert roa["mean"] == pytest.approx(0.045)
    assert roa["min"] == 0.03
    assert roa["max"] == 0.06


def test_benchmark_flags_only_above_threshold():
    bench = describe_benchmark(_make_feature_table())
    assert bench["all_n"].iloc[0] == 4
    assert bench["all_flagged_n"].iloc[0] == 2
    row = bench.set_index("fiscal_year").loc[2021]
    assert row["flagged_n"] == 1
    assert row["flagged_share"] == pytest.approx(0.3333)
