# -*- coding: utf-8 -*-
"""
run_09_repair_downloads.py
Author: Group12A2 DSW Team
Purpose: Re-download every firm-year flagged by run_04 (missing / too_small /
         mismatched_year).  Dry-run by default; pass --apply to download.
Module: scripts

Usage:
    .venv/Scripts/python scripts/run_09_repair_downloads.py           # plan only
    .venv/Scripts/python scripts/run_09_repair_downloads.py --apply   # download

Revision History
-----------------
2026-11-06  initial version.
"""
import argparse
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import CNINFO_RAW, DATA_PROCESSED  # noqa: E402
from src.data_ingestion.cninfo_client import download_annual_report  # noqa: E402


def _repair_items(audit: pd.DataFrame) -> list[tuple[str, int]]:
    """Return (symbol, fiscal_year) pairs whose audit status is not ok."""
    bad = audit.loc[audit["status"] != "ok"] if "status" in audit else pd.DataFrame()
    return [
        (str(row["symbol"]).zfill(6), int(row["fiscal_year"]))
        for _, row in bad.iterrows()
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="Re-download audit-flagged annual reports.")
    parser.add_argument("--apply", action="store_true", help="actually download; default is a dry run")
    parser.add_argument("--delay", type=float, default=1.0)
    args = parser.parse_args()

    audit_path = DATA_PROCESSED / "download_audit.csv"
    if not audit_path.exists():
        print("[run_09] no download_audit.csv - run scripts/run_04_audit_downloads.py first")
        return 2
    audit = pd.read_csv(audit_path, dtype={"symbol": str})
    items = _repair_items(audit)
    print(f"[run_09] {len(items)} item(s) to repair")
    if not items:
        return 0

    log_path = DATA_PROCESSED / f"repair_log_{datetime.now():%Y%m%d_%H%M%S}.csv"
    results = []
    for i, (symbol, year) in enumerate(items, 1):
        target = CNINFO_RAW / str(year) / f"{symbol}_{year}_annual_report.pdf"
        record = {"symbol": symbol, "fiscal_year": year, "status": "skipped(dry)"}
        if args.apply:
            if target.exists():
                target.unlink()
            result = download_annual_report(symbol, year)
            record["status"] = result.get("status")
            record["title"] = result.get("title", "")
        results.append(record)
        print(f"[run_09] {i}/{len(items)} {symbol}-{year} -> {record['status']}", flush=True)

    pd.DataFrame(results).to_csv(log_path, index=False, encoding="utf-8-sig")
    print(f"[run_09] repair log: {log_path}")


if __name__ == "__main__":
    sys.exit(main())
