# -*- coding: utf-8 -*-
"""
run_05b_recompute_text_features.py
Author: Group12A2 DSW Team
Purpose: Recompute the three textual features for every annual-report PDF using
         the v0.2 full dictionaries (Yao 2021 formal sentiment + expanded
         uncertainty) and token-based counting. Unlike run_05, this does NOT
         reuse the previous CSV (the dictionary changed), and it also caches the
         raw MD&A slice to JSONL so later re-counts never re-extract PDFs.
Module: scripts

Usage:
  python scripts/run_05b_recompute_text_features.py [--year 2021] [--workers 8] [--limit 50]

Revision History
-----------------
2026-11-11  initial version: multiprocessing recompute + MD&A JSONL cache.
"""
import argparse
import json
import shutil
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import CNINFO_RAW, DATA_INTERIM  # noqa: E402
from src.features.textual import extract_mda_features  # noqa: E402

CHECKPOINT_EVERY = 500
DEFAULT_WORKERS = 8
BACKUP_DIR = DATA_INTERIM / "v0.1_text_features_backup"

# The numeric feature columns, in the same order as run_05's output CSV.
CSV_COLUMNS = (
    "symbol",
    "status",
    "readability",
    "sentiment_balance",
    "uncertainty_ratio",
    "n_tokens",
    "n_sentences",
)


def _process(pdf: Path) -> dict:
    """Extract features (plus cached MD&A text) for one PDF. Runs in a worker."""
    symbol = pdf.name.split("_")[0]
    result = extract_mda_features(pdf, include_text=True)
    row = {"symbol": symbol, "status": result.get("status", "error")}
    features = result.get("features")
    if isinstance(features, dict):
        row.update(features)
    if "mda_text" in result:
        row["mda_text"] = result["mda_text"]
    return row


def _write_table(rows: list[dict], out_path: Path) -> None:
    """Write the numeric feature CSV (same schema as run_05), sorted by symbol."""
    table = pd.DataFrame(rows)
    for col in CSV_COLUMNS:
        if col not in table.columns:
            table[col] = None
    table = table.drop_duplicates(subset=["symbol"], keep="last")
    table = table.sort_values("symbol")
    table[list(CSV_COLUMNS)].to_csv(out_path, index=False, encoding="utf-8-sig")


def _write_jsonl(rows: list[dict], out_path: Path) -> None:
    """Write the MD&A text cache: one {"symbol","mda_text"} per line, ok rows only."""
    with open(out_path, "w", encoding="utf-8") as handle:
        for row in rows:
            if row.get("status") == "ok" and row.get("mda_text"):
                handle.write(
                    json.dumps(
                        {"symbol": row["symbol"], "mda_text": row["mda_text"]},
                        ensure_ascii=False,
                    )
                    + "\n"
                )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, default=None)
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS)
    parser.add_argument("--limit", type=int, default=None, help="process only first N PDFs per year")
    args = parser.parse_args()

    years = [args.year] if args.year else (2021, 2022, 2023)
    DATA_INTERIM.mkdir(parents=True, exist_ok=True)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    for year in years:
        out_csv = DATA_INTERIM / f"text_features_{year}.csv"
        out_jsonl = DATA_INTERIM / f"mda_text_{year}.jsonl"

        # Back up the v0.1 feature table once so the old results stay recoverable.
        backup_csv = BACKUP_DIR / f"text_features_{year}.csv"
        if out_csv.exists() and not backup_csv.exists():
            shutil.copy2(out_csv, backup_csv)
            print(f"[run_05b] backed up {out_csv.name} -> {backup_csv}", flush=True)

        pdf_dir = CNINFO_RAW / str(year)
        pdfs = sorted(pdf_dir.glob("*_annual_report.pdf")) if pdf_dir.exists() else []
        if args.limit:
            pdfs = pdfs[: args.limit]
        if not pdfs:
            print(f"[run_05b] {year}: no PDFs found, skipping", flush=True)
            continue

        rows: list[dict] = []
        started = time.time()
        with Pool(processes=args.workers) as pool:
            for i, row in enumerate(
                pool.imap_unordered(_process, pdfs, chunksize=8), 1
            ):
                rows.append(row)
                if i % CHECKPOINT_EVERY == 0:
                    _write_table(rows, out_csv)
                    ok = sum(1 for r in rows if r.get("status") == "ok")
                    print(
                        f"[run_05b] {year} checkpoint {i}/{len(pdfs)} "
                        f"({ok} ok, {time.time() - started:.0f}s)",
                        flush=True,
                    )

        _write_table(rows, out_csv)
        _write_jsonl(rows, out_jsonl)

        table = pd.DataFrame(rows)
        ok = int((table["status"] == "ok").sum()) if "status" in table else 0
        elapsed = time.time() - started
        print(
            f"[run_05b] {year} done: {ok}/{len(table)} ok in {elapsed:.0f}s "
            f"-> {out_csv.name} / {out_jsonl.name}",
            flush=True,
        )


if __name__ == "__main__":
    main()
