# -*- coding: utf-8 -*-
"""
run_04_audit_downloads.py
Author: Group12A2 DSW Team
Purpose: Audit downloaded annual-report PDFs against the checklist and download
         logs; flag missing files and title-year mismatches for rework.
Module: scripts

Usage: python scripts/run_04_audit_downloads.py [--year 2021] [--min-kb 100]

Revision History
-----------------
2026-11-05  initial version.
2026-11-06  merge repair logs; accept 'YYYY年度报告' title style.
"""
import argparse
import re
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import CNINFO_RAW, DATA_PROCESSED  # noqa: E402

MIN_SIZE_BYTES = 100 * 1024
YEAR_RE = re.compile(r"(20\d{2})年?年度报告")


def _target_year_from_title(title: str) -> int | None:
    match = YEAR_RE.search(title or "")
    return int(match.group(1)) if match else None


def _latest_rows(year: int) -> pd.DataFrame:
    """Newest download/repair log row per code for the given year."""
    patterns = (f"download_log_{year}_*.csv", "repair_log_*.csv")
    paths = sorted(
        (p for pat in patterns for p in DATA_PROCESSED.glob(pat)),
        key=lambda p: p.stat().st_mtime,
    )
    frames = []
    for path in paths:
        df = pd.read_csv(path, dtype=str)
        if {"symbol", "fiscal_year"}.issubset(df.columns):
            df = df.rename(columns={"symbol": "code", "fiscal_year": "year"})
        if "year" in df.columns:
            df = df[df["year"].astype(str) == str(year)]
        frames.append(df)
    if not frames:
        return pd.DataFrame()
    merged = pd.concat(frames, ignore_index=True)
    return merged.drop_duplicates(subset=["code"], keep="last")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, default=None)
    args = parser.parse_args()

    checklist = pd.read_csv(DATA_PROCESSED / "download_checklist.csv", dtype={"symbol": str})
    years = [args.year] if args.year else (2021, 2022, 2023)
    rows = []
    for year in years:
        year_col = f"fiscal_{year}"
        if year_col not in checklist.columns:
            continue
        expected = checklist.loc[checklist[year_col] == "Y", "symbol"].tolist()
        log = _latest_rows(year)
        log_titles = dict(zip(log["code"], log.get("title", [""]))) if not log.empty else {}
        for symbol in expected:
            pdf = CNINFO_RAW / str(year) / f"{symbol}_{year}_annual_report.pdf"
            status = "ok"
            title = str(log_titles.get(symbol, ""))
            if not pdf.exists():
                status = "missing"
            elif pdf.stat().st_size < MIN_SIZE_BYTES:
                status = "too_small"
            else:
                title_year = _target_year_from_title(title)
                if title_year and title_year != year:
                    status = "mismatched_year"
            rows.append({"symbol": symbol, "fiscal_year": year, "status": status, "log_title": title})

    audit = pd.DataFrame(rows)
    out_path = DATA_PROCESSED / "download_audit.csv"
    audit.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(audit.groupby("status").size().to_string())
    print(f"audit written: {out_path}")


if __name__ == "__main__":
    main()
