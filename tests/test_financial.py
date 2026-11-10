# -*- coding: utf-8 -*-
"""
test_financial.py
Author: Group12A2 DSW Team
Purpose: Unit tests for the six financial features.
Module: tests

Revision History
-----------------
2026-11-05  initial version.
"""
import pandas as pd
import pytest

from src.features.financial import compute_finance_features


def make_df() -> pd.DataFrame:
    """One firm, two years, values chosen for easy exact arithmetic."""
    return pd.DataFrame(
        {
            "symbol": ["000001", "000001"],
            "fiscal_year": [2020, 2021],
            "revenue": [100.0, 120.0],
            "cogs": [60.0, 72.0],
            "total_assets": [200.0, 240.0],
            "total_liabilities": [100.0, 120.0],
            "current_assets": [80.0, 96.0],
            "current_liabilities": [50.0, 60.0],
            "receivables": [20.0, 24.0],
            "fixed_assets": [100.0, 120.0],
            "long_term_debt": [40.0, 48.0],
            "cash": [10.0, 12.0],
            "depreciation": [10.0, 12.0],
            "sga": [15.0, 18.0],
            "net_income": [10.0, 12.0],
            "ocf": [30.0, 36.0],
        }
    )


def test_six_finance_features_exact_values():
    out = compute_finance_features(make_df())
    year = out.loc[out["fiscal_year"] == 2021].iloc[0]
    assert year["roa"] == pytest.approx(12 / 240)
    assert year["leverage"] == pytest.approx(120 / 240)
    assert year["revenue_growth"] == pytest.approx(20 / 100)
    assert year["ocf_to_assets"] == pytest.approx(36 / 240)
    assert year["receivables_turnover"] == pytest.approx(120 / 24)
    assert year["accruals_to_assets"] == pytest.approx((12 - 36) / 240)


def test_base_year_has_no_growth():
    out = compute_finance_features(make_df())
    base = out.loc[out["fiscal_year"] == 2020].iloc[0]
    assert pd.isna(base["revenue_growth"])
