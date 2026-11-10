# -*- coding: utf-8 -*-
"""
financial.py
Author: Group12A2 DSW Team
Purpose: The six financial features from the intermediate CSMAR schema.
Module: src/features

The functions consume the intermediate schema defined in docs/feature_dictionary.md;
src/data_ingestion/csmar_parser.py maps raw CSMAR columns onto this schema.

Revision History
-----------------
2026-11-05  initial version: six features with prior-year merge for growth.
"""
import pandas as pd

FINANCE_COLS = [
    "symbol",
    "fiscal_year",
    "revenue",
    "cogs",
    "total_assets",
    "total_liabilities",
    "current_assets",
    "current_liabilities",
    "receivables",
    "fixed_assets",
    "long_term_debt",
    "cash",
    "depreciation",
    "sga",
    "net_income",
    "ocf",
]


def compute_finance_features(df: pd.DataFrame) -> pd.DataFrame:
    """Compute the six financial features; requires prior-year rows for growth."""
    out = df.sort_values(["symbol", "fiscal_year"]).copy()
    prev = out.groupby("symbol", sort=False).shift(1)

    out["roa"] = out["net_income"] / out["total_assets"]
    out["leverage"] = out["total_liabilities"] / out["total_assets"]
    out["revenue_growth"] = (out["revenue"] - prev["revenue"]) / prev["revenue"]
    out["ocf_to_assets"] = out["ocf"] / out["total_assets"]
    out["receivables_turnover"] = out["revenue"] / out["receivables"]
    out["accruals_to_assets"] = (out["net_income"] - out["ocf"]) / out["total_assets"]
    return out
