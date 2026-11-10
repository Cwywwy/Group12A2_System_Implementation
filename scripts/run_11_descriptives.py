# -*- coding: utf-8 -*-
"""
run_11_descriptives.py
Author: Group12A2 DSW Team
Purpose: Generate the descriptives summary markdown for the experiment chapter.
Module: scripts

Usage: python scripts/run_11_descriptives.py [--feature-csv PATH] [--audit-csv PATH]

Revision History
-----------------
2026-11-06  initial version.
"""
import argparse
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import DATA_PROCESSED, REPORTS  # noqa: E402
from src.reporting.descriptives import build_descriptives_report  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--feature-csv", type=Path, default=DATA_PROCESSED / "feature_table.csv")
    parser.add_argument("--audit-csv", type=Path, default=DATA_PROCESSED / "download_audit.csv")
    args = parser.parse_args()

    if not args.feature_csv.exists():
        print(f"missing feature table: {args.feature_csv} (run scripts/run_06 first)")
        sys.exit(2)
    ft = pd.read_csv(args.feature_csv, dtype={"symbol": str})
    audit = pd.DataFrame()
    if args.audit_csv.exists():
        audit = pd.read_csv(args.audit_csv, dtype={"symbol": str})

    out_md = REPORTS / "descriptives_summary.md"
    summary = build_descriptives_report(ft, audit, out_md)
    print(f"wrote {out_md}")
    print(f"summary: {summary}")


if __name__ == "__main__":
    main()
