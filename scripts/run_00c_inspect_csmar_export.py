#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Print the structure of a CSMAR export so a download can be checked quickly.

Module role: data-ingestion readiness check for the event-variable branch.
Author: Jinyu Wang

CSMAR exports differ between platforms (Chinese labels, English labels, a code
row plus a unit row), so before wiring a new table into the pipeline we only
need to know: which sheet holds the data, which columns exist, how many rows,
and whether the security code column survived as text. This script answers
those four questions for any .xlsx/.csv file or directory of them.

Usage:
    python scripts/run_00c_inspect_csmar_export.py data/raw/csmar_events
    python scripts/run_00c_inspect_csmar_export.py path/to/AUD_OPINION.xlsx
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DIR = PROJECT_ROOT / "data" / "raw" / "csmar_events"
HEAD_ROWS = 3


def _describe_csv(path: Path) -> None:
    frame = pd.read_csv(path, dtype=str, nrows=None)
    _report(path, "csv", frame)


def _describe_excel(path: Path) -> None:
    book = pd.ExcelFile(path)
    for sheet in book.sheet_names:
        frame = pd.read_excel(book, sheet_name=sheet, dtype=str)
        _report(path, sheet, frame)


def _report(path: Path, sheet: str, frame: pd.DataFrame) -> None:
    print(f"\n=== {path.name} · sheet={sheet} ===")
    print(f"rows={len(frame):,} cols={len(frame.columns)}")
    print("columns:")
    for name in frame.columns:
        print(f"  - {name}")
    code_cols = [c for c in frame.columns if c.strip().lower() in {"stkcd", "symbol", "证券代码"}]
    for column in code_cols:
        sample = frame[column].dropna().astype(str).head(3).tolist()
        print(f"code column {column!r} sample={sample}")
        lengths = frame[column].dropna().astype(str).str.len().unique()[:5].tolist()
        print(f"  code lengths seen: {lengths}")
    if HEAD_ROWS:
        with pd.option_context("display.max_columns", 8, "display.width", 160):
            print(frame.head(HEAD_ROWS).to_string())


def main(argv: list[str]) -> int:
    target = Path(argv[1]) if len(argv) > 1 else DEFAULT_DIR
    if not target.exists():
        print(f"path not found: {target}")
        print("put the CSMAR export(s) there, or pass an explicit file path")
        return 2
    files = [target] if target.is_file() else sorted(target.glob("*"))
    exports = [p for p in files if p.suffix.lower() in {".xlsx", ".xls", ".csv"}]
    if not exports:
        print(f"no .xlsx/.csv files under {target}")
        return 2
    for path in exports:
        try:
            if path.suffix.lower() == ".csv":
                _describe_csv(path)
            else:
                _describe_excel(path)
        except Exception as exc:  # noqa: BLE001 - report and keep going
            print(f"\n!!! {path.name} could not be read: {type(exc).__name__}: {exc}")
    print("\nchecklist: code column looks like 6 digits or 6 chars with leading zeros,")
    print("one row per firm-year (or one row per announcement), and a readable")
    print("opinion / restatement / violation type column.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
