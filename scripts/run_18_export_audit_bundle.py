#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
run_18_export_audit_bundle.py
Author: Group12A2 DSW Team
Purpose: Export the compact, licence-safe analysis bundle (identifiers, four
         outcome labels, four anomaly scores and the Beneish benchmark) so an
         external reviewer can recompute every headline statistic without the
         licensed raw data.
Module: scripts
Revision history:
    2026-11-26 initial version: export audit_bundle.csv for the review brief
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd  # noqa: E402

from src.config import DATA_PROCESSED, TABLES  # noqa: E402

BUNDLE = TABLES / "audit_bundle.csv"

SCORE_COLUMNS = ("if_finance", "if_text", "if_fused", "ae_fused", "m_score")
LABEL_COLUMNS = (
    "mod_opinion",
    "mod_opinion_wide",
    "violation_any_t1",
    "violation_disclosure_t1",
)
COLUMNS = ("symbol", "fiscal_year", *SCORE_COLUMNS, *LABEL_COLUMNS)


def build_bundle() -> pd.DataFrame:
    """Merge the saved scores with the four outcome labels on firm-year keys."""
    scores = pd.read_csv(TABLES / "anomaly_scores.csv", dtype={"symbol": str})
    events = pd.read_csv(DATA_PROCESSED / "event_table.csv", dtype={"symbol": str})
    scores["symbol"] = scores["symbol"].str.zfill(6)
    events["symbol"] = events["symbol"].str.zfill(6)
    events = events[["symbol", "fiscal_year", *LABEL_COLUMNS]]
    bundle = scores[["symbol", "fiscal_year", *SCORE_COLUMNS]].merge(
        events, on=["symbol", "fiscal_year"], how="left", validate="one_to_one"
    )
    bundle = bundle[list(COLUMNS)].sort_values(["symbol", "fiscal_year"])
    # Ten decimals reproduce the published ranking exactly. Rounding to six is
    # not enough: it introduces ties that move the autoencoder AUC off the
    # reported 0.696 down to 0.696.
    bundle[list(SCORE_COLUMNS)] = bundle[list(SCORE_COLUMNS)].round(10)
    return bundle


def main() -> int:
    bundle = build_bundle()
    bundle.to_csv(BUNDLE, index=False, encoding="utf-8")
    size_mb = BUNDLE.stat().st_size / 1024 / 1024
    print(f"wrote {BUNDLE.relative_to(PROJECT_ROOT)}: {len(bundle):,} rows, {size_mb:.2f} MB")
    print(f"firms {bundle['symbol'].nunique():,}; years {bundle['fiscal_year'].nunique()}")
    print("missing labels:", int(bundle[list(LABEL_COLUMNS)].isna().sum().sum()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
