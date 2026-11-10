# -*- coding: utf-8 -*-
"""
test_feature_table.py
Author: Group12A2 DSW Team
Purpose: Unit tests for the fused feature-table merge and text-quality flags.
Module: tests

Revision History
-----------------
2026-11-05  initial version.
"""
import pandas as pd

from src.features.feature_table import build_feature_table, classify_text_quality


def _sample() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "symbol": ["000001", "000001", "000003"],
            "fiscal_year": [2021, 2022, 2021],
            "industry_code_d": ["C34", "C34", "C27"],
        }
    )


def _finance() -> pd.DataFrame:
    # FINANCE_COLS schema incl. base year 2020 for growth/Beneish lags
    return pd.DataFrame(
        [
            ["000001", 2020, 1000, 600, 2000, 1000, 800, 500, 100, 600, 200, 300, 50, 120, 100, 300],
            ["000001", 2021, 1100, 660, 2200, 1100, 880, 550, 110, 660, 220, 330, 55, 130, 110, 330],
            ["000001", 2022, 1210, 726, 2420, 1210, 968, 605, 121, 726, 242, 363, 60, 140, 120, 360],
            ["000003", 2020, 500, 300, 1000, 500, 400, 250, 50, 300, 100, 150, 25, 60, 50, 150],
            ["000003", 2021, 550, 330, 1100, 550, 440, 275, 55, 330, 110, 165, 28, 65, 55, 165],
        ],
        columns=[
            "symbol", "fiscal_year", "revenue", "cogs", "total_assets", "total_liabilities",
            "current_assets", "current_liabilities", "receivables", "fixed_assets",
            "long_term_debt", "cash", "depreciation", "sga", "net_income", "ocf",
        ],
    )


def _text() -> dict[int, pd.DataFrame]:
    return {
        2021: pd.DataFrame(
            {
                "symbol": ["000001", "000003"],
                "status": ["ok", "no_mda"],
                "readability": [0.01, 0.02],
                "sentiment_balance": [0.001, 0.0],
                "uncertainty_ratio": [0.002, 0.0],
                "n_tokens": [8000, 12],
                "n_sentences": [300, 2],
            }
        ),
        2022: pd.DataFrame(
            {
                "symbol": ["000001"],
                "status": ["ok"],
                "readability": [0.011],
                "sentiment_balance": [0.002],
                "uncertainty_ratio": [0.003],
                "n_tokens": [9000],
                "n_sentences": [320],
            }
        ),
    }


def test_build_feature_table_merges_and_excludes_base_year():
    table = build_feature_table(_sample(), _finance(), _text())
    assert list(table["fiscal_year"]) == [2021, 2022, 2021]
    assert set(table.columns) >= {
        "symbol", "fiscal_year", "industry_code_d", "m_score",
        "readability", "sentiment_balance", "uncertainty_ratio", "text_quality",
    }
    # finance + text joined for 000001-2021
    row = table[(table["symbol"] == "000001") & (table["fiscal_year"] == 2021)].iloc[0]
    assert row["m_score"] == row["m_score"]  # not NaN
    assert row["readability"] == 0.01


def test_text_quality_flags():
    assert classify_text_quality("ok", 8000) == "ok"
    assert classify_text_quality("no_mda", 12) == "suspicious"
    assert classify_text_quality("ok", 50) == "suspicious"
    assert classify_text_quality(None, float("nan")) == "missing"


def test_text_quality_column_values():
    table = build_feature_table(_sample(), _finance(), _text())
    qualities = dict(zip(table["symbol"], table["text_quality"]))
    assert qualities["000001"] == "ok"
    assert qualities["000003"] == "suspicious"
