#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Probe whether MD&A text carries signal for any Beneish component.

Module role: exploratory branch analysis for the second specification.
Author: Jinyu Wang

The headline benchmark is the aggregate M-Score, which mixes eight ratios with
opposite signs. A text measure can be informative about one ratio and still show
nothing against the aggregate, so this script correlates every anomaly ranking
with each component separately and writes a table for the manuscript notes.

Outputs: outputs/branches/branch_component_correlations.csv
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.features.beneish import BENEISH_COEFFICIENTS, compute_beneish  # noqa: E402

FINANCE = PROJECT_ROOT / "data" / "interim" / "finance_intermediate.csv"
SCORES = PROJECT_ROOT / "outputs" / "tables" / "anomaly_scores.csv"
OUT = PROJECT_ROOT / "outputs" / "branches" / "branch_component_correlations.csv"
COMPONENTS = list(BENEISH_COEFFICIENTS) + ["m_score"]
MODELS = ["if_finance", "if_text", "if_fused", "ae_fused"]


def main() -> int:
    finance = pd.read_csv(FINANCE, dtype={"symbol": str})
    scores = pd.read_csv(SCORES, dtype={"symbol": str})
    scores = scores.drop(columns=["m_score"], errors="ignore")
    for frame in (finance, scores):
        frame["symbol"] = frame["symbol"].str.zfill(6)

    comp = compute_beneish(finance)[["symbol", "fiscal_year", *COMPONENTS]]
    merged = scores.merge(
        comp, on=["symbol", "fiscal_year"], how="left", validate="one_to_one"
    )

    rows: list[dict[str, object]] = []
    for model in MODELS:
        for name in COMPONENTS:
            pair = merged[[model, name]].dropna()
            rho = pair[model].corr(pair[name], method="spearman")
            rows.append(
                {
                    "model": model,
                    "target": name,
                    "n": int(len(pair)),
                    "spearman_rho": round(float(rho), 4),
                }
            )
    table = pd.DataFrame(rows)
    table.to_csv(OUT, index=False)

    wide = table.pivot(index="target", columns="model", values="spearman_rho")
    wide = wide.loc[COMPONENTS, MODELS]
    print(f"rows={len(table)} -> {OUT}")
    print(wide.to_string())
    best = table.loc[table["model"].isin(["if_text", "if_fused"])]
    best = best.reindex(best["spearman_rho"].abs().sort_values(ascending=False).index)
    print("\ntop text-bearing associations (absolute):")
    print(best.head(8).to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
