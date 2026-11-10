# -*- coding: utf-8 -*-
"""
standardise.py
Author: Group12A2 DSW Team
Purpose: Winsorisation and subindustry-year group standardisation with sparse fallback.
Module: src/features

Revision History
-----------------
2026-11-05  initial version.
"""
import pandas as pd

from src.config import MIN_SUBINDUSTRY_YEAR_CELL, WINSOR_QUANTILES


def winsorize_columns(
    df: pd.DataFrame,
    columns: list[str],
    quantiles: tuple[float, float] = WINSOR_QUANTILES,
) -> pd.DataFrame:
    """Clip each column at its own quantiles (per-column, not per-group)."""
    out = df.copy()
    for col in columns:
        lower, upper = out[col].quantile(quantiles)
        out[col] = out[col].clip(lower, upper)
    return out


def standardise_within_groups(
    df: pd.DataFrame,
    value_cols: list[str],
    group_cols: tuple[str, ...] = ("industry_code_d", "fiscal_year"),
    min_cell: int = MIN_SUBINDUSTRY_YEAR_CELL,
) -> pd.DataFrame:
    """z-scores within each subindustry-year cell; sparse cells use full-sample stats."""
    value_cols = list(value_cols)
    original_index = df.index
    work = df.copy()
    work.index = pd.RangeIndex(len(work))
    full_mean = work[value_cols].mean()
    full_std = work[value_cols].std(ddof=0).replace(0, 1.0)
    z = pd.DataFrame(index=work.index, columns=value_cols, dtype=float)

    grouped = work.groupby(list(group_cols), sort=False)
    for _, idx in grouped.indices.items():
        cell = work.loc[idx, value_cols]
        if len(cell) >= min_cell:
            cell_mean = cell.mean()
            cell_std = cell.std(ddof=0).replace(0, 1.0)
            z.loc[idx] = (cell - cell_mean) / cell_std
        else:
            z.loc[idx] = (cell - full_mean) / full_std
    z.index = original_index
    return z
