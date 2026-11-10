# -*- coding: utf-8 -*-
"""
run_08_qc_report.py
Author: Group12A2 DSW Team
Purpose: QC report over yearly text-feature CSVs and the download audit.
Module: scripts

Usage: .venv/Scripts/python scripts/run_08_qc_report.py
Outputs: data/processed/qc_summary.csv, data/processed/qc_issues.csv

Revision History
-----------------
2026-11-06  initial version.
"""
import sys
import re
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config import DATA_INTERIM, DATA_PROCESSED
from src.features.qc import build_qc_report


def main() -> int:
    text_frames: dict[int, pd.DataFrame] = {}
    for path in sorted(DATA_INTERIM.glob("text_features_*.csv")):
        match = re.fullmatch(r"text_features_(\d{4})\.csv", path.name)
        if not match:
            continue
        year = int(match.group(1))
        frame = pd.read_csv(path, dtype={"symbol": str})
        text_frames[year] = frame

    if not text_frames:
        print("[run_08] 未找到任何 text_features_*.csv，请先运行 run_05。")
        return 2

    audit_path = DATA_PROCESSED / "download_audit.csv"
    audit = pd.read_csv(audit_path, dtype={"symbol": str}) if audit_path.exists() else None

    summary, issues = build_qc_report(text_frames, audit)
    summary.to_csv(DATA_PROCESSED / "qc_summary.csv", index=False, encoding="utf-8-sig")
    issues.to_csv(DATA_PROCESSED / "qc_issues.csv", index=False, encoding="utf-8-sig")

    print("[run_08] QC 汇总：")
    print(summary.to_string(index=False))
    print(f"[run_08] 问题清单 {len(issues)} 行 -> data/processed/qc_issues.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
