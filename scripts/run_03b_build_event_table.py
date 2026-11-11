# -*- coding: utf-8 -*-
"""
run_03b_build_event_table.py
Author: Group12A2 DSW Team
Purpose: Build the firm-year event label table (modified audit opinions and
         forward violation announcements) for the analysis sample, using the
         CSMAR FIN_Audit and STK_Violation_Main exports.
Module: scripts

Usage: python scripts/run_03b_build_event_table.py [--scores PATH] [--out PATH]

The base frame is the analysis sample produced by run_07_experiment.py
(outputs/tables/anomaly_scores.csv, one row per scored firm-year), so the
event labels line up exactly with the model scores. A diagnostic block with
coverage and per-year event rates is printed and written next to the table.

Revision History
----------------
2026-11-11  initial version: audit opinions (narrow/wide) plus t+1 violation
            labels for the 8,140 firm-year analysis sample.
"""
import argparse
import json
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import DATA_PROCESSED  # noqa: E402
from src.data_ingestion.event_parser import (  # noqa: E402
    build_event_table,
    event_summary,
    parse_audit_opinions,
    parse_violations,
)

DEFAULT_SCORES = PROJECT_ROOT / "outputs" / "tables" / "anomaly_scores.csv"
DEFAULT_OUT = DATA_PROCESSED / "event_table.csv"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scores", type=str, default=str(DEFAULT_SCORES))
    parser.add_argument("--out", type=str, default=str(DEFAULT_OUT))
    args = parser.parse_args()

    scores_path = Path(args.scores)
    if not scores_path.exists():
        print(f"[run_03b] missing scores file: {scores_path}")
        print("[run_03b] run scripts/run_07_experiment.py first. Nothing written.")
        sys.exit(2)

    scores = pd.read_csv(scores_path, dtype={"symbol": str})
    scores["symbol"] = scores["symbol"].str.zfill(6)
    base = scores[["symbol", "fiscal_year"]].copy()

    print("[run_03b] parsing CSMAR audit opinions ...")
    audit = parse_audit_opinions()
    print(f"[run_03b] audit rows={len(audit):,} years={int(audit['fiscal_year'].min())}"
          f"-{int(audit['fiscal_year'].max())}")

    print("[run_03b] parsing CSMAR violations ...")
    violations = parse_violations()
    print(f"[run_03b] violation rows={len(violations):,} "
          f"years={int(violations['declare_year'].min())}"
          f"-{int(violations['declare_year'].max())}")

    table = build_event_table(base, audit=audit, violations=violations)
    summary = event_summary(table)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(out_path, index=False, encoding="utf-8-sig")

    summary_path = out_path.with_suffix(".json")
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"[run_03b] wrote {out_path} ({len(table):,} rows)")
    print(f"[run_03b] audit coverage={summary['audit_coverage']:.1%}")
    for label in (
        "mod_opinion",
        "mod_opinion_wide",
        "violation_any_t1",
        "violation_disclosure_t1",
    ):
        print(
            f"[run_03b] {label}: count={summary[f'{label}_count']:,} "
            f"rate={summary[f'{label}_rate']:.2%}"
        )
    for year, block in summary["by_year"].items():
        print(
            f"[run_03b]   {year}: n={block['n']:,} "
            f"mod={block['mod_opinion']:.2%} mod_wide={block['mod_opinion_wide']:.2%} "
            f"viol_t1={block['violation_any_t1']:.2%} "
            f"disc_t1={block['violation_disclosure_t1']:.2%}"
        )
    print(f"[run_03b] wrote {summary_path}")


if __name__ == "__main__":
    main()
