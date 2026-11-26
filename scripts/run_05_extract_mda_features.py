# -*- coding: utf-8 -*-
"""
run_05_extract_mda_features.py
Author: Group12A2 DSW Team
Purpose: Batch-extract the three textual features from downloaded annual-report
         PDFs (incremental; resumes after interruption).
Module: scripts

Usage: python scripts/run_05_extract_mda_features.py [--year 2021] [--start ...] [--end ...]

Revision History
-----------------
2026-11-05  initial version.
2026-11-05  fix: flatten the nested "features" dict returned by extract_mda_features
            into the CSV row (earlier version stored it as one dict cell).
2026-11-06  robustness: checkpoint the partial CSV every CHECKPOINT_EVERY files so
            a crash or kill no longer loses all progress since the last full run.
2026-11-06  fix: carried-over rows re-attach their symbol from the index (to_dict
            drops the index, which wrote NaN symbols after restarts); heal bad
            rows by re-extracting them; dedupe by symbol before writing.
"""
import argparse
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import CNINFO_RAW, DATA_INTERIM, SAMPLE_YEARS  # noqa: E402
from src.features.textual import extract_mda_features  # noqa: E402

CHECKPOINT_EVERY = 25


def _extract_one(pdf_path: str) -> dict:
    """Worker: return one feature row for a single annual-report PDF."""
    pdf = Path(pdf_path)
    result = extract_mda_features(pdf)
    row = {"symbol": pdf.name.split("_")[0], "status": result.get("status", "error")}
    features = result.get("features")
    if isinstance(features, dict):
        row.update(features)
    return row


def _write_table(rows: list[dict], out_path: Path) -> None:
    table = pd.DataFrame(rows)
    if not table.empty and "symbol" in table.columns:
        table = table.drop_duplicates(subset=["symbol"], keep="last")
    table.to_csv(out_path, index=False, encoding="utf-8-sig")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, default=None)
    parser.add_argument("--start", type=str, default=None)
    parser.add_argument("--end", type=str, default=None)
    parser.add_argument("--workers", type=int, default=1,
                        help="parallel extraction processes; 1 keeps the serial path")
    args = parser.parse_args()

    years = [args.year] if args.year else SAMPLE_YEARS
    DATA_INTERIM.mkdir(parents=True, exist_ok=True)
    for year in years:
        out_path = DATA_INTERIM / f"text_features_{year}.csv"
        done: dict[str, dict] = {}
        if out_path.exists():
            existing = pd.read_csv(out_path, dtype={"symbol": str})
            existing = existing.dropna(subset=["symbol"])
            existing = existing[existing["symbol"].str.match(r"^\d{6}$", na=False)]
            done = {
                str(sym): {"symbol": str(sym), **vals}
                for sym, vals in existing.set_index("symbol").to_dict("index").items()
            }

        pdf_dir = CNINFO_RAW / str(year)
        pdfs = sorted(pdf_dir.glob("*_annual_report.pdf")) if pdf_dir.exists() else []
        if args.start:
            pdfs = [p for p in pdfs if p.name >= args.start]
        if args.end:
            pdfs = [p for p in pdfs if p.name <= args.end]

        rows = [done[pdf.name.split("_")[0]] for pdf in pdfs if pdf.name.split("_")[0] in done]
        pending = [pdf for pdf in pdfs if pdf.name.split("_")[0] not in done]
        started = time.time()
        print(f"[run_05] {year}: {len(pending)} to extract, {len(rows)} carried over, "
              f"{args.workers} workers", flush=True)

        if args.workers > 1 and pending:
            with ProcessPoolExecutor(max_workers=args.workers) as pool:
                for done_count, row in enumerate(pool.map(_extract_one, map(str, pending), chunksize=4), 1):
                    rows.append(row)
                    print(f"[run_05] {year} {done_count}/{len(pending)} {row['symbol']} -> "
                          f"{row['status']} ({row.get('n_tokens', 0)} tokens)", flush=True)
                    if done_count % CHECKPOINT_EVERY == 0:
                        _write_table(rows, out_path)
                        print(f"[run_05] checkpoint {done_count} written", flush=True)
        else:
            for i, pdf in enumerate(pending, 1):
                row = _extract_one(str(pdf))
                rows.append(row)
                print(f"[run_05] {year} {i}/{len(pending)} {row['symbol']} -> {row['status']} "
                      f"({row.get('n_tokens', 0)} tokens)", flush=True)
                if i % CHECKPOINT_EVERY == 0:
                    _write_table(rows, out_path)
                    print(f"[run_05] checkpoint {i} written", flush=True)

        _write_table(rows, out_path)
        table = pd.DataFrame(rows)
        ok = int((table["status"] == "ok").sum()) if "status" in table else 0
        elapsed = time.time() - started
        print(f"[run_05] {year} done: {ok}/{len(table)} ok in {elapsed:.0f}s -> {out_path}", flush=True)


if __name__ == "__main__":
    main()
