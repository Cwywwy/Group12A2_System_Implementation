# -*- coding: utf-8 -*-
"""
test_beneish.py
Author: Group12A2 DSW Team
Purpose: Unit tests for the Beneish M-Score benchmark.
Module: tests

Revision History
-----------------
2026-11-05  initial version.
2026-11-10  add division-by-zero guard test (inf -> NaN).
"""
import pandas as pd
import pytest

from src.features.beneish import compute_beneish


def constant_firm() -> pd.DataFrame:
    """Identical values in both years: every ratio is 1 and TATA is 0."""
    return pd.DataFrame(
        {
            "symbol": ["000001", "000001"],
            "fiscal_year": [2020, 2021],
            "revenue": [100.0, 100.0],
            "cogs": [60.0, 60.0],
            "total_assets": [200.0, 200.0],
            "total_liabilities": [100.0, 100.0],
            "current_assets": [80.0, 80.0],
            "current_liabilities": [50.0, 50.0],
            "receivables": [20.0, 20.0],
            "fixed_assets": [100.0, 100.0],
            "long_term_debt": [40.0, 40.0],
            "cash": [10.0, 10.0],
            "depreciation": [10.0, 10.0],
            "sga": [15.0, 15.0],
            "net_income": [10.0, 10.0],
            "ocf": [10.0, 10.0],
        }
    )


def test_constant_firm_scores_the_model_constant():
    out = compute_beneish(constant_firm())
    year = out.loc[out["fiscal_year"] == 2021].iloc[0]
    for ratio in ("DSRI", "GMI", "AQI", "SGI", "DEPI", "SGAI", "LVGI"):
        assert year[ratio] == pytest.approx(1.0)
    assert year["TATA"] == pytest.approx(0.0)
    # All ratios equal 1, so M = -4.84 + (0.92+0.528+0.404+0.892+0.115-0.172-0.327) = -2.48.
    assert year["m_score"] == pytest.approx(-2.48)


def test_revenue_doubling_shifts_dsri_and_sgi():
    df = constant_firm()
    df.loc[df["fiscal_year"] == 2021, "revenue"] = 200.0
    out = compute_beneish(df)
    year = out.loc[out["fiscal_year"] == 2021].iloc[0]
    # receivables/revenue halves: (20/200) / (20/100) = 0.5
    assert year["DSRI"] == pytest.approx(0.5)
    assert year["SGI"] == pytest.approx(2.0)
    assert year["m_score"] > -4.84


def test_zero_base_year_revenue_yields_nan_not_inf():
    """Division by zero must produce NaN, never +inf/-inf, in the M-Score."""
    df = constant_firm()
    df.loc[df["fiscal_year"] == 2020, "revenue"] = 0.0
    out = compute_beneish(df)
    year = out.loc[out["fiscal_year"] == 2021].iloc[0]
    assert pd.isna(year["SGI"])          # 100 / 0 -> inf -> NaN
    assert pd.isna(year["m_score"])      # inf must not leak into the M-Score
    assert not float("inf") == year["m_score"]
