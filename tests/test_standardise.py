# -*- coding: utf-8 -*-
"""
test_standardise.py
Author: Group12A2 DSW Team
Purpose: Unit tests for winsorisation and group standardisation.
Module: tests

Revision History
-----------------
2026-11-05  initial version.
"""
import pandas as pd
import pytest

from src.features.standardise import standardise_within_groups, winsorize_columns


def test_winsorize_clips_at_quantiles():
    df = pd.DataFrame({"x": [0.0, 1.0, 2.0, 100.0]})
    out = winsorize_columns(df, ["x"], quantiles=(0.25, 0.75))
    # pandas linear interpolation: q(0.25) = 0.75, q(0.75) = 26.5.
    assert out["x"].tolist() == pytest.approx([0.75, 1.0, 2.0, 26.5])


def make_groups() -> pd.DataFrame:
    rows = pd.DataFrame(
        {
            "industry_code_d": ["C27"] * 20 + ["C24"] * 3,
            "fiscal_year": [2021] * 23,
            "x": [float(i) for i in range(1, 21)] + [100.0, 101.0, 102.0],
        }
    )
    return rows


def test_large_group_is_standardised_in_cell():
    df = make_groups()
    z = standardise_within_groups(df, ["x"], min_cell=5)
    large = z.loc[df["industry_code_d"] == "C27", "x"]
    assert large.mean() == pytest.approx(0.0, abs=1e-9)
    assert large.std(ddof=0) == pytest.approx(1.0)


def test_sparse_group_falls_back_to_full_sample():
    df = make_groups()
    z = standardise_within_groups(df, ["x"], min_cell=5)
    sparse_idx = df.index[df["industry_code_d"] == "C24"]
    full_mean = df["x"].mean()
    full_std = df["x"].std(ddof=0)
    expected = (df.loc[sparse_idx, "x"] - full_mean) / full_std
    assert z.loc[sparse_idx, "x"].tolist() == pytest.approx(expected.tolist())
