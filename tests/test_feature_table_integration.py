# -*- coding: utf-8 -*-
"""
test_feature_table_integration.py
Author: Group12A2 DSW Team
Purpose: Integration test - sample frame + FINANCE_COLS intermediate + text frames
         fuse into the modelling-ready feature table (run_06 critical path).
Module: tests

Revision History
-----------------
2026-11-06  initial version.
"""
import pandas as pd

from src.features.feature_table import build_feature_table


def _finance_intermediate() -> pd.DataFrame:
    rows = []
    for symbol in ("000001", "000002", "600001"):
        for year in (2020, 2021, 2022):
            rows.append(
                {
                    "symbol": symbol,
                    "fiscal_year": year,
                    "revenue": 1000 + year * 10,
                    "cogs": 700 + year * 5,
                    "total_assets": 5000 + year * 100,
                    "total_liabilities": 2500 + year * 50,
                    "current_assets": 2000 + year * 40,
                    "current_liabilities": 1200 + year * 30,
                    "receivables": 300 + year * 5,
                    "fixed_assets": 1500 + year * 20,
                    "long_term_debt": 400 + year * 10,
                    "cash": 800 + year * 15,
                    "depreciation": 60 + year,
                    "sga_sales": 40 + year,
                    "sga_admin": 80 + year,
                    "net_income": 120 + year * 2,
                    "ocf": 200 + year * 3,
                }
            )
    return pd.DataFrame(rows)


def _sample() -> pd.DataFrame:
    rows = []
    for symbol in ("000001", "000002", "600001"):
        for year in (2021, 2022):
            rows.append(
                {
                    "symbol": symbol,
                    "fiscal_year": year,
                    "industry_code_d": "C27" if symbol != "600001" else "C34",
                }
            )
    return pd.DataFrame(rows)


def _text_frames() -> dict[int, pd.DataFrame]:
    frames = {}
    for year in (2021, 2022):
        frames[year] = pd.DataFrame(
            [
                {"symbol": "000001", "status": "ok", "readability": 0.01,
                 "sentiment_balance": 0.02, "uncertainty_ratio": 0.03,
                 "n_tokens": 5000, "n_sentences": 120},
                {"symbol": "000002", "status": "no_mda", "readability": 0.0,
                 "sentiment_balance": 0.0, "uncertainty_ratio": 0.0,
                 "n_tokens": 10, "n_sentences": 1},
            ]
        )
    return frames


def test_build_feature_table_fuses_all_sides():
    table = build_feature_table(_sample(), _finance_intermediate(), _text_frames())
    # base year rows never enter the sample frame output
    assert sorted(table["fiscal_year"].tolist()) == [2021, 2021, 2021, 2022, 2022, 2022]
    expected_cols = {
        "symbol", "fiscal_year", "industry_code_d", "roa", "leverage",
        "revenue_growth", "ocf_to_assets", "receivables_turnover",
        "accruals_to_assets", "m_score", "text_status", "readability",
        "sentiment_balance", "uncertainty_ratio", "n_tokens", "n_sentences",
        "text_quality",
    }
    assert expected_cols.issubset(set(table.columns))
    assert not table["m_score"].isna().any()  # 2020 base year feeds M-Score


def test_build_feature_table_text_quality_labels():
    table = build_feature_table(_sample(), _finance_intermediate(), _text_frames())
    row1 = table[(table.symbol == "000001") & (table.fiscal_year == 2021)].iloc[0]
    row2 = table[(table.symbol == "000002") & (table.fiscal_year == 2021)].iloc[0]
    row3 = table[(table.symbol == "600001") & (table.fiscal_year == 2021)].iloc[0]
    assert row1["text_quality"] == "ok"
    assert row2["text_quality"] == "suspicious"  # no_mda
    assert row3["text_quality"] == "missing"  # absent from text frames


def test_build_feature_table_without_text_frames_still_computes_finance():
    table = build_feature_table(_sample(), _finance_intermediate(), {})
    assert not table["m_score"].isna().any()
    assert (table["text_quality"] == "missing").all()
