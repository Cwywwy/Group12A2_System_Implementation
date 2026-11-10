# -*- coding: utf-8 -*-
"""
beneish.py
Author: Group12A2 DSW Team
Purpose: Beneish M-Score (8-variable model) as the external benchmark only.
Module: src/features

The M-Score is NEVER a training input; it only flags benchmark events.

Revision History
-----------------
2026-11-05  initial version: eight ratios and the -4.84 constant model.
2026-11-10  guard division-by-zero: inf/-inf ratios become NaN so infinite
            M-Scores cannot poison benchmark flags or rank correlation.
"""
import numpy as np
import pandas as pd

BENEISH_COEFFICIENTS = {
    "DSRI": 0.92,
    "GMI": 0.528,
    "AQI": 0.404,
    "SGI": 0.892,
    "DEPI": 0.115,
    "SGAI": -0.172,
    "TATA": 4.679,
    "LVGI": -0.327,
}
M_SCORE_CONSTANT = -4.84


def compute_beneish(df: pd.DataFrame) -> pd.DataFrame:
    """Compute the eight ratios and the M-Score for each firm-year with a base year."""
    out = df.sort_values(["symbol", "fiscal_year"]).copy()
    p = out.groupby("symbol", sort=False).shift(1)

    out["DSRI"] = (out["receivables"] / out["revenue"]) / (p["receivables"] / p["revenue"])
    out["GMI"] = ((p["revenue"] - p["cogs"]) / p["revenue"]) / ((out["revenue"] - out["cogs"]) / out["revenue"])
    out["AQI"] = (1 - (out["current_assets"] + out["fixed_assets"]) / out["total_assets"]) / (
        1 - (p["current_assets"] + p["fixed_assets"]) / p["total_assets"]
    )
    out["SGI"] = out["revenue"] / p["revenue"]
    out["DEPI"] = (p["depreciation"] / (p["depreciation"] + p["fixed_assets"])) / (
        out["depreciation"] / (out["depreciation"] + out["fixed_assets"])
    )
    out["SGAI"] = (out["sga"] / out["revenue"]) / (p["sga"] / p["revenue"])
    out["LVGI"] = (out["total_liabilities"] / out["total_assets"]) / (
        p["total_liabilities"] / p["total_assets"]
    )
    out["TATA"] = (out["net_income"] - out["ocf"]) / out["total_assets"]
    out["m_score"] = M_SCORE_CONSTANT + sum(
        coef * out[name] for name, coef in BENEISH_COEFFICIENTS.items()
    )
    # Division by zero (e.g. zero revenue or total assets in the base year)
    # yields inf/-inf ratios; treat those firms as "M-Score undefined" instead
    # of letting infinities poison the benchmark flags and rank correlation.
    out = out.replace([np.inf, -np.inf], np.nan)
    return out
