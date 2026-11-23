# -*- coding: utf-8 -*-
"""
run_08_lexicon_control.py
Author: Group12A2 DSW Team
Purpose: Isolate the lexicon change from the financial-data repair: rerun the
         ranking pipeline with the archived v0.1 text features on the repaired
         financial data.
Module: scripts

Usage: python scripts/run_08_lexicon_control.py [--features PATH]
                                                 [--archive-dir PATH]
                                                 [--report PATH]

The control itself lives in `src.evaluation.lexicon_control` and the report
rendering in `src.reporting.revision_reports`; this file only parses arguments,
writes the three CSVs and appends Part 2 of the evidence file (Part 1 has to be
produced first by run_07c).

Revision History
----------------
2026-11-24  initial version: same-row lexicon-only control for the v0.3
            revision.
2026-11-24  thinned to argument parsing after the control moved into src.
"""
import argparse
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import TABLES, TEXT_FEATURES  # noqa: E402
from src.evaluation.lexicon_control import (  # noqa: E402
    control_table,
    corpus_diagnostics,
    load_archive_text_features,
    prepare_control_frame,
    score_variant,
    variant_overlap,
)
from src.reporting.revision_reports import append_lexicon_report  # noqa: E402

DEFAULT_FEATURES = PROJECT_ROOT / "data" / "processed" / "feature_table.csv"
DEFAULT_ARCHIVE = PROJECT_ROOT / "data" / "archive_v0.1" / "text_features"
DEFAULT_REPORT = PROJECT_ROOT / "outputs" / "branches" / "strict_timing_and_lexicon_control.md"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--features", type=str, default=str(DEFAULT_FEATURES))
    parser.add_argument("--archive-dir", type=str, default=str(DEFAULT_ARCHIVE))
    parser.add_argument("--report", type=str, default=str(DEFAULT_REPORT))
    args = parser.parse_args()

    features = pd.read_csv(Path(args.features), dtype={"symbol": str})
    features["symbol"] = features["symbol"].str.zfill(6)
    archive = load_archive_text_features(args.archive_dir)
    work = prepare_control_frame(features, archive)
    print(f"[run_08] rows with both text versions={len(work):,} firms={work['symbol'].nunique():,}")

    diagnostics = corpus_diagnostics(work)
    diagnostics.to_csv(
        TABLES / "lexicon_control_diagnostics.csv", index=False, encoding="utf-8-sig"
    )
    print(f"[run_08] wrote {TABLES / 'lexicon_control_diagnostics.csv'}")

    current = score_variant(work, tuple(TEXT_FEATURES))
    legacy = score_variant(work, tuple(f"v01_{column}" for column in TEXT_FEATURES))

    control = control_table(current, legacy, work)
    control.to_csv(TABLES / "lexicon_control_v01.csv", index=False, encoding="utf-8-sig")
    print(f"[run_08] wrote {TABLES / 'lexicon_control_v01.csv'}")

    overlap = variant_overlap(current, legacy)
    overlap.to_csv(TABLES / "lexicon_control_overlap.csv", index=False, encoding="utf-8-sig")

    report = append_lexicon_report(args.report, control, overlap, diagnostics)
    print(f"[run_08] appended to {report}")

    for _, row in control.iterrows():
        print(
            f"[run_08] {row['spec']:<16s} {row['model']:<12s} "
            f"rho={row['spearman_rho']:+.3f} lift10_cal={row['enrichment_calibrated_k10']:.2f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
