# -*- coding: utf-8 -*-
"""
test_sample_frame.py
Author: Group12A2 DSW Team
Purpose: Unit tests for the manufacturing sample frame builder.
Module: tests

Revision History
-----------------
2026-11-05  initial version: filter logic and checklist flags.
"""
import pandas as pd

from src.sample_frame import build_sample_frame, make_checklist


def make_info() -> pd.DataFrame:
    """Synthetic cleaned ListedCoInfoAnnual rows (label rows already dropped)."""
    return pd.DataFrame(
        {
            "Symbol": ["1", "2", "3", "4"],
            "ShortName_en": ["Alpha", "Beta", "Gamma", "Delta"],
            "EndDate": ["2021-12-31", "2022-12-31", "2023-12-31", "2024-12-31"],
            "IndustryCodeD": ["C27", "J66", "C24", "C26"],
            "IndustryNameD_EN": ["machinery", "banking", "electronics", "pharma"],
            "fiscal_year": [2021, 2022, 2023, 2024],
        }
    )


def test_build_sample_frame_filters_industry_and_years():
    frame = build_sample_frame(make_info())
    # 000002 is non-manufacturing (J66); 000004 is outside the 2021-2023 sample.
    assert set(frame["symbol"]) == {"000001", "000003"}


def test_symbol_is_zero_padded_to_six_digits():
    frame = build_sample_frame(make_info())
    assert frame["symbol"].str.len().eq(6).all()


def test_make_checklist_flags_only_present_years():
    frame = build_sample_frame(make_info())
    checklist = make_checklist(frame)
    row = checklist.loc[checklist["symbol"] == "000001"].iloc[0]
    assert row["fiscal_2021"] == "Y"
    assert row["fiscal_2022"] == ""
    assert checklist["symbol"].is_unique
