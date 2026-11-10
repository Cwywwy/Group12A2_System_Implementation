# -*- coding: utf-8 -*-
"""
sample_frame.py
Author: Group12A2 DSW Team
Purpose: Build the manufacturing firm-year sample frame from CSMAR ListedCoInfoAnnual.
Module: src (core)

Revision History
-----------------
2026-11-05  initial version: CAPCO IndustryCodeD filter for 2021-2023 plus checklist.
"""
import re
from pathlib import Path

import pandas as pd

from src.config import (
    DATA_PROCESSED,
    LISTEDCO_INFO_XLSX,
    MANUFACTURING_PREFIX,
    SAMPLE_YEARS,
)

INFO_USE_COLS = ["Symbol", "ShortName_en", "EndDate", "IndustryCodeD", "IndustryNameD_EN"]
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")

SAMPLE_FRAME_CSV = DATA_PROCESSED / "manufacturing_sample_frame.csv"
CHECKLIST_CSV = DATA_PROCESSED / "download_checklist.csv"


def read_listedco_info(path: Path = LISTEDCO_INFO_XLSX) -> pd.DataFrame:
    """Read the raw CSMAR table and drop the Chinese label / unit rows."""
    df = pd.read_excel(path, usecols=INFO_USE_COLS, dtype=str)
    df = df.loc[df["EndDate"].str.match(DATE_PATTERN, na=False)].copy()
    df["fiscal_year"] = pd.to_datetime(df["EndDate"], errors="coerce").dt.year
    df = df.dropna(subset=["fiscal_year"])
    df["fiscal_year"] = df["fiscal_year"].astype(int)
    return df


def build_sample_frame(
    info: pd.DataFrame,
    years: tuple[int, ...] = SAMPLE_YEARS,
    prefix: str = MANUFACTURING_PREFIX,
) -> pd.DataFrame:
    """Return manufacturing firm-year rows for the sample years (CAPCO code D)."""
    mask = info["IndustryCodeD"].str.startswith(prefix, na=False) & info["fiscal_year"].isin(years)
    frame = info.loc[mask].copy()
    frame["symbol"] = frame["Symbol"].str.zfill(6)
    return frame[
        ["symbol", "ShortName_en", "fiscal_year", "IndustryCodeD", "IndustryNameD_EN", "EndDate"]
    ].rename(columns={"ShortName_en": "short_name", "IndustryCodeD": "industry_code_d", "IndustryNameD_EN": "industry_name_d", "EndDate": "end_date"})


def make_checklist(frame: pd.DataFrame, years: tuple[int, ...] = SAMPLE_YEARS) -> pd.DataFrame:
    """One row per unique manufacturing firm, with one flag column per fiscal year."""
    base = (
        frame[["symbol", "short_name", "industry_code_d"]]
        .drop_duplicates(subset=["symbol"])
        .sort_values("symbol")
        .reset_index(drop=True)
    )
    for year in years:
        have = set(frame.loc[frame["fiscal_year"] == year, "symbol"])
        base[f"fiscal_{year}"] = base["symbol"].isin(have).map({True: "Y", False: ""})
    return base


def main() -> None:
    info = read_listedco_info()
    frame = build_sample_frame(info)
    checklist = make_checklist(frame)
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    frame.to_csv(SAMPLE_FRAME_CSV, index=False, encoding="utf-8-sig")
    checklist.to_csv(CHECKLIST_CSV, index=False, encoding="utf-8-sig")
    print(f"all rows after cleaning : {len(info)}")
    print(f"manufacturing firm-years: {len(frame)}")
    print(f"unique manufacturing firms: {checklist['symbol'].nunique()}")
    for year in SAMPLE_YEARS:
        print(f"  fiscal {year}: {int((frame['fiscal_year'] == year).sum())} firm-years")


if __name__ == "__main__":
    main()
