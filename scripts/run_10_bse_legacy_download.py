# -*- coding: utf-8 -*-
"""
run_10_bse_legacy_download.py
Author: Group12A2 DSW Team
Purpose: Re-download annual-report PDFs for BSE (920xxx) firms whose CNINFO
         records are only indexed under their pre-2025 legacy codes.
Module: scripts

Beijing Stock Exchange switched 242 listed firms from 83xxxx/87xxxx/43xxxx
codes to 920xxx on 2025-10-09.  CNINFO resolves org ids only for the legacy
codes for these firms, so the main run_02 downloader records them as missing.
This script maps each missing 920xxx code back to its legacy code (via the
official mapping table in data/external/bse_920_code_mapping.csv), queries the
unfiltered BSE announcement list, and saves the PDF under the NEW code so that
every downstream step keeps the same file naming convention.

Revision History
----------------
2026-11-06  initial version: mapping lookup + BSE legacy search + download loop.
"""
from __future__ import annotations

import argparse
import csv
import sys
import time
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd  # noqa: E402

from src.config import CNINFO_RAW, DATA_PROCESSED  # noqa: E402
from src.data_ingestion.cninfo_client import (  # noqa: E402
    REQUEST_PAUSE_SECONDS,
    download_pdf,
    resolve_org_id,
    search_annual_reports_bse,
    select_annual_report,
)

MAPPING_CSV = PROJECT_ROOT / "data" / "external" / "bse_920_code_mapping.csv"


def load_legacy_mapping(mapping_csv: Path = MAPPING_CSV) -> dict[str, str]:
    """Map new 920xxx code -> legacy code from the BSE mapping table."""
    table = pd.read_csv(mapping_csv, dtype=str)
    table = table[table["new_code"].str.fullmatch(r"\d{6}", na=False)]
    mapping = dict(zip(table["new_code"], table["old_code"]))
    assert mapping, f"empty mapping table: {mapping_csv}"
    return mapping


def build_missing_codes(years: tuple[int, ...]) -> list[tuple[int, str]]:
    """Union of 920xxx missing codes across the latest download logs."""
    missing: set[tuple[int, str]] = set()
    for year in years:
        logs = sorted(DATA_PROCESSED.glob(f"download_log_{year}_*.csv"))
        if not logs:
            print(f"[run_10] no download log for {year}, skipped", flush=True)
            continue
        log = pd.read_csv(logs[-1], dtype=str)
        codes = log.loc[log["status"] == "missing", "code"]
        missing.update((year, code) for code in codes if code.startswith("920"))
    return sorted(missing)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--years", default="2021,2022,2023", help="comma list of fiscal years")
    parser.add_argument("--delay", type=float, default=REQUEST_PAUSE_SECONDS, help="pause between firms")
    parser.add_argument("--codes", default=None, help="optional file with 920xxx codes (one per line)")
    args = parser.parse_args()

    years = tuple(int(y) for y in args.years.split(","))
    mapping = load_legacy_mapping()
    if args.codes:
        codes = [c.strip() for c in Path(args.codes).read_text(encoding="utf-8").splitlines() if c.strip()]
        work = [(year, code) for year in years for code in codes if code.startswith("920")]
    else:
        work = build_missing_codes(years)
    print(f"[run_10] {len(work)} firm-year(s) to attempt across {years}", flush=True)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = DATA_PROCESSED / f"download_log_bse_{stamp}.csv"
    with log_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["code", "old_code", "year", "status", "title", "path"])
        writer.writeheader()
        ok = cached = missing = failed = 0
        for index, (year, code) in enumerate(work, start=1):
            old_code = mapping.get(code)
            record = {"code": code, "old_code": old_code or "", "year": year,
                      "status": "mapping_error", "title": "legacy code not in mapping", "path": ""}
            if old_code:
                dest = CNINFO_RAW / str(year) / f"{code}_{year}_annual_report.pdf"
                record["path"] = str(dest)
                try:
                    items = search_annual_reports_bse(old_code, year)
                    ann = select_annual_report(items, year)
                    if ann is None:
                        record.update(status="missing", title="no annual report found")
                    else:
                        record.update(status=download_pdf(ann.adjunct_url, dest), title=ann.title)
                except LookupError:
                    record.update(status="missing", title="no org id for legacy code")
                except Exception as exc:  # noqa: BLE001 - record and continue
                    record.update(status="error", title=str(exc))
            ok += record["status"] == "downloaded"
            cached += record["status"] == "cached"
            missing += record["status"] in ("missing", "mapping_error")
            failed += record["status"] == "error"
            writer.writerow(record)
            handle.flush()
            print(f"[run_10] {index}/{len(work)} {year} {code} (legacy {old_code}) -> {record['status']}",
                  flush=True)
            time.sleep(args.delay)

    print(f"[run_10] done: {ok} downloaded, {cached} cached, {missing} missing, {failed} failed", flush=True)
    print(f"[run_10] log: {log_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
