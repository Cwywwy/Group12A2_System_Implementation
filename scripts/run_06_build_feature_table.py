# -*- coding: utf-8 -*-
"""
run_06_build_feature_table.py
Author: Group12A2 DSW Team
Purpose: Driver that fuses the sample frame, CSMAR-derived finance features,
         Beneish M-Score and MD&A text features into the final feature table.
Module: scripts

Usage: python scripts/run_06_build_feature_table.py [--finance PATH]

The finance intermediate table is produced from the CSMAR three statements by
src/data_ingestion/csmar_parser.py; until the team provides the CSMAR files,
this script exits with a clear message instead of producing a partial table.

Revision History
-----------------
2026-11-05  initial version.
"""
import argparse
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import DATA_INTERIM, DATA_PROCESSED, SAMPLE_YEARS  # noqa: E402
from src.features.feature_table import build_feature_table  # noqa: E402

FINANCE_INTERIM = DATA_INTERIM / "finance_intermediate.csv"
SAMPLE_FRAME = DATA_PROCESSED / "manufacturing_sample_frame.csv"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--finance", type=str, default=str(FINANCE_INTERIM))
    parser.add_argument("--out", type=str, default=str(DATA_PROCESSED / "feature_table.csv"))
    args = parser.parse_args()

    finance_path = Path(args.finance)
    if not finance_path.exists():
        print(f"[run_06] missing finance intermediate: {finance_path}")
        print("[run_06] generate it from the CSMAR three statements with "
              "src/data_ingestion/csmar_parser.py once the team places the files "
              "in data/raw/csmar/. No feature table written.")
        sys.exit(2)

    sample = pd.read_csv(SAMPLE_FRAME, dtype={"symbol": str})
    finance = pd.read_csv(finance_path, dtype={"symbol": str})
    text_frames: dict[int, pd.DataFrame] = {}
    for year in SAMPLE_YEARS:
        path = DATA_INTERIM / f"text_features_{year}.csv"
        if path.exists():
            text_frames[year] = pd.read_csv(path, dtype={"symbol": str})

    if not text_frames:
        print("[run_06] warning: no text_features_*.csv found; text columns will be empty.")

    table = build_feature_table(sample, finance, text_frames)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(out_path, index=False, encoding="utf-8-sig")

    n = len(table)
    coverage = {
        "rows": n,
        "finance_ok": int(table["m_score"].notna().sum()),
        "text_ok": int((table["text_quality"] == "ok").sum()),
        "text_suspicious": int((table["text_quality"] == "suspicious").sum()),
        "text_missing": int((table["text_quality"] == "missing").sum()),
    }
    print(f"[run_06] feature table written: {out_path}")
    print(f"[run_06] coverage: {coverage['rows']} rows, finance {coverage['finance_ok']}, "
          f"text ok {coverage['text_ok']} / suspicious {coverage['text_suspicious']} / "
          f"missing {coverage['text_missing']}")


if __name__ == "__main__":
    main()
