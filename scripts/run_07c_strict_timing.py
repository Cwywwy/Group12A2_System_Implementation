# -*- coding: utf-8 -*-
"""
run_07c_strict_timing.py
Author: Group12A2 DSW Team
Purpose: Rebuild the t+1 violation labels with a disclosure-date gate and
         rerun the external-outcome evaluation on them.
Module: scripts

Usage: python scripts/run_07c_strict_timing.py [--events PATH] [--scores PATH]
                                                [--features PATH] [--boot N]
                                                [--window-days N] [--no-window]
                                                [--strict-report PATH]

The analysis lives in `src.evaluation.timing_eval` and the report rendering in
`src.reporting.revision_reports`; this file only parses arguments, writes the
three CSVs and prints the headline numbers.

Revision History
----------------
2026-11-24  initial version: disclosure-date gating and rerun for the v0.3
            revision.
2026-11-24  thinned to argument parsing after the analysis moved into src.
"""
import argparse
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import TABLES  # noqa: E402
from src.evaluation.timing_eval import (  # noqa: E402
    LABELS,
    build_labelled_frame,
    ranking_block,
    strict_diagnostics,
    supervised_block,
)
from src.reporting.revision_reports import write_timing_report  # noqa: E402

DEFAULT_EVENTS = PROJECT_ROOT / "data" / "processed" / "event_table.csv"
DEFAULT_SCORES = TABLES / "anomaly_scores.csv"
DEFAULT_FEATURES = PROJECT_ROOT / "data" / "processed" / "feature_table.csv"
DEFAULT_REPORT = PROJECT_ROOT / "outputs" / "branches" / "strict_timing_and_lexicon_control.md"


def _read_features(path: str) -> pd.DataFrame:
    features = pd.read_csv(Path(path), dtype={"symbol": str})
    features["symbol"] = features["symbol"].str.zfill(6)
    return features


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--events", type=str, default=str(DEFAULT_EVENTS))
    parser.add_argument("--scores", type=str, default=str(DEFAULT_SCORES))
    parser.add_argument("--features", type=str, default=str(DEFAULT_FEATURES))
    parser.add_argument("--boot", type=int, default=400)
    parser.add_argument("--window-days", type=int, default=365)
    parser.add_argument(
        "--no-window",
        action="store_true",
        help="drop the upper lag bound and keep every announcement after the report date",
    )
    parser.add_argument("--strict-report", type=str, default=str(DEFAULT_REPORT))
    args = parser.parse_args()
    window = None if args.no_window else args.window_days

    frame, _strict = build_labelled_frame(args.events, args.scores, window_days=window)
    print(f"[run_07c] merged rows={len(frame):,} firms={frame['symbol'].nunique():,}")
    for label, _description, _loose in LABELS:
        print(
            f"[run_07c] {label}: events={int(frame[label].sum()):,} "
            f"rate={frame[label].mean():.2%}"
        )

    diagnostics = strict_diagnostics(frame)
    diagnostics.to_csv(
        TABLES / "event_strict_diagnostics.csv", index=False, encoding="utf-8-sig"
    )
    print(f"[run_07c] wrote {TABLES / 'event_strict_diagnostics.csv'}")

    ranking = ranking_block(frame, boot=args.boot)
    ranking.to_csv(
        TABLES / "event_ranking_metrics_strict.csv", index=False, encoding="utf-8-sig"
    )
    print(f"[run_07c] wrote {TABLES / 'event_ranking_metrics_strict.csv'}")

    supervised = supervised_block(frame, _read_features(args.features), boot=args.boot)
    supervised.to_csv(
        TABLES / "event_supervised_metrics_strict.csv", index=False, encoding="utf-8-sig"
    )
    print(f"[run_07c] wrote {TABLES / 'event_supervised_metrics_strict.csv'}")

    report = write_timing_report(
        args.strict_report, ranking, supervised, diagnostics, window
    )
    print(f"[run_07c] wrote {report}")

    focus = ranking[ranking["model"].isin(["finance-only IF", "fused IF", "text-only IF"])]
    for _, row in focus.iterrows():
        print(
            f"[run_07c] AUC {row['label']:<34s} {row['model']:<16s} "
            f"{row['auc']:.3f} [{row['auc_lo']:.3f}, {row['auc_hi']:.3f}] "
            f"lift10={row['lift_10pct']:.2f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
