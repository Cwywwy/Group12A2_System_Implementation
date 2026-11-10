# -*- coding: utf-8 -*-
"""
run_02_download_annual_reports.py
Author: Group12A2 DSW Team
Purpose: Batch-download annual report PDFs for the manufacturing checklist.
Module: scripts

Usage:
    python scripts/run_02_download_annual_reports.py --year 2021 --start 0 --end 100
Rows refer to data/processed/download_checklist.csv; only firms flagged for the
requested fiscal year are downloaded. The run log is written next to the checklist.

Revision History
-----------------
2026-11-05  initial version.
2026-11-06  add --codes (targeted repair list) and --force (ignore cached PDF).
"""
import argparse
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd  # noqa: E402

from src.config import CNINFO_RAW  # noqa: E402
from src.data_ingestion.cninfo_client import REQUEST_PAUSE_SECONDS, download_annual_report  # noqa: E402
from src.sample_frame import CHECKLIST_CSV


def _parse_codes(raw: str | None) -> list[str]:
    """Parse --codes: comma-separated list or path to a file (one symbol per line)."""
    if not raw:
        return []
    candidate = Path(raw)
    if candidate.exists():
        lines = candidate.read_text(encoding="utf-8-sig").splitlines()
    else:
        lines = raw.split(",")
    return [item.strip() for item in lines if item.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description="Batch-download annual report PDFs from CNINFO.")
    parser.add_argument("--year", type=int, required=True, choices=(2021, 2022, 2023))
    parser.add_argument("--start", type=int, default=0, help="checklist row offset to start from")
    parser.add_argument("--end", type=int, default=None, help="checklist row offset to stop before")
    parser.add_argument("--delay", type=float, default=REQUEST_PAUSE_SECONDS)
    parser.add_argument("--codes", type=str, default=None,
                        help="comma-separated symbols or path to a file listing symbols (targeted repair)")
    parser.add_argument("--force", action="store_true",
                        help="remove a cached PDF before downloading it again")
    args = parser.parse_args()

    checklist = pd.read_csv(CHECKLIST_CSV, dtype={"symbol": str})
    col = f"fiscal_{args.year}"
    todo = checklist.loc[checklist[col] == "Y", "symbol"].astype(str).tolist()
    codes = _parse_codes(args.codes)
    if codes:
        wanted = set(codes)
        todo = [c for c in todo if c in wanted]
    todo = todo[args.start : args.end]
    print(f"[run_02] fiscal {args.year}: {len(todo)} firms in slice [{args.start}:{args.end}]")

    records = 0
    ok = 0
    log_path = CHECKLIST_CSV.parent / f"download_log_{args.year}_{datetime.now():%Y%m%d_%H%M%S}.csv"
    with log_path.open("w", encoding="utf-8-sig", newline="") as log_handle:
        for i, code in enumerate(todo, 1):
            if args.force:
                target = CNINFO_RAW / str(args.year) / f"{code}_{args.year}_annual_report.pdf"
                if target.exists():
                    target.unlink()
            record = download_annual_report(code, args.year)
            pd.DataFrame([record]).to_csv(log_handle, index=False, header=(records == 0))
            log_handle.flush()
            records += 1
            if record["status"] in ("downloaded", "cached"):
                ok += 1
            print(f"[run_02] {i}/{len(todo)} {code} -> {record['status']} | {record['title']}", flush=True)
            if args.delay > 0:
                time.sleep(args.delay)

    print(f"[run_02] done: {ok} ok, {records - ok} failed/missing; log -> {log_path}")


if __name__ == "__main__":
    main()
