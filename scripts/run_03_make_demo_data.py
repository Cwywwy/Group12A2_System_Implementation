# -*- coding: utf-8 -*-
"""
run_03_make_demo_data.py
Author: Group12A2 DSW Team
Purpose: Generate a synthetic demo feature table and smoke-test the Phase 3 pipeline.
Module: scripts

Demo scope: 80 firms x 4 years (2020-2023) across 7 manufacturing subindustries;
20% of firms are planted as anomalous (aggressive growth, high accruals,
low operating cash flow, high uncertainty wording). The full pipeline is then
run on the demo table so every downstream module is exercised before real data
arrives. Results are saved under outputs/tables/.

Revision History
-----------------
2026-11-05  initial version.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import SEED  # noqa: E402
from src.features.beneish import compute_beneish  # noqa: E402
from src.features.financial import FINANCE_COLS, compute_finance_features  # noqa: E402
from src.pipeline import run_pipeline  # noqa: E402

N_FIRMS = 80
SUBINDUSTRIES = ["C26", "C27", "C34", "C35", "C36", "C38", "C39"]
YEARS = (2020, 2021, 2022, 2023)
ANOMALOUS_SHARE = 0.20


def make_demo_finance_table(rng: np.random.Generator) -> pd.DataFrame:
    rows = []
    for i in range(N_FIRMS):
        symbol = f"{600001 + i}"
        subindustry = SUBINDUSTRIES[i % len(SUBINDUSTRIES)]
        anomalous = i < int(N_FIRMS * ANOMALOUS_SHARE)
        assets = rng.lognormal(mean=21.5, sigma=0.6)
        for year in YEARS:
            growth = rng.normal(0.10, 0.12)
            if anomalous and year >= 2021:
                growth += 0.30
            revenue = 0.62 * assets * (1 + growth)
            cogs = 0.72 * revenue
            sga = 0.12 * revenue
            depreciation = 0.045 * assets
            ni_margin = 0.05 + rng.normal(0, 0.02)
            if anomalous and year >= 2021:
                ni_margin -= 0.03
            net_income = revenue * ni_margin
            ocf = net_income + depreciation
            if anomalous and year >= 2021:
                ocf -= 0.10 * assets
            rows.append({
                "symbol": symbol,
                "fiscal_year": year,
                "revenue": revenue,
                "cogs": cogs,
                "total_assets": assets,
                "total_liabilities": 0.55 * assets,
                "current_assets": 0.50 * assets,
                "current_liabilities": 0.42 * assets,
                "receivables": 0.16 * assets + (0.06 * assets if anomalous and year >= 2021 else 0),
                "fixed_assets": 0.38 * assets,
                "long_term_debt": 0.09 * assets,
                "cash": 0.11 * assets,
                "depreciation": depreciation,
                "sga": sga,
                "net_income": net_income,
                "ocf": ocf,
            })
            assets = assets * (1 + growth) * (1 + rng.normal(0, 0.03))
    frame = pd.DataFrame(rows)
    assert list(frame.columns) == FINANCE_COLS
    return frame


def make_demo_text_features(frame: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    text = pd.DataFrame({
        "symbol": frame["symbol"],
        "fiscal_year": frame["fiscal_year"],
        "readability": np.clip(rng.normal(0.0080, 0.0016, len(frame)), 0.001, None),
        "sentiment_balance": rng.normal(0.0020, 0.0040, len(frame)),
        "uncertainty_ratio": np.clip(rng.normal(0.0040, 0.0020, len(frame)), 0.0, None),
    })
    anomalous_mask = frame["symbol"].isin(
        frame["symbol"].unique()[: int(N_FIRMS * ANOMALOUS_SHARE)]
    ) & (frame["fiscal_year"] >= 2021)
    text.loc[anomalous_mask, "uncertainty_ratio"] += 0.020
    text.loc[anomalous_mask, "sentiment_balance"] -= 0.020
    return text


def main() -> None:
    rng = np.random.default_rng(SEED)
    finance_intermediate = make_demo_finance_table(rng)
    finance_features = compute_finance_features(finance_intermediate)
    beneish = compute_beneish(finance_intermediate)
    text_features = make_demo_text_features(finance_intermediate, rng)

    subindustry = pd.DataFrame({
        "symbol": finance_intermediate["symbol"],
        "fiscal_year": finance_intermediate["fiscal_year"],
        "industry_code_d": finance_intermediate["symbol"].map(
            lambda s: SUBINDUSTRIES[(int(s) - 600001) % len(SUBINDUSTRIES)]
        ),
    })

    table = (
        finance_features.merge(beneish[["symbol", "fiscal_year", "m_score"]], on=["symbol", "fiscal_year"])
        .merge(text_features, on=["symbol", "fiscal_year"])
        .merge(subindustry, on=["symbol", "fiscal_year"])
    )
    interim_dir = PROJECT_ROOT / "data" / "interim"
    interim_dir.mkdir(parents=True, exist_ok=True)
    demo_csv = interim_dir / "demo_feature_table.csv"
    table.to_csv(demo_csv, index=False)
    print(f"demo feature table written: {demo_csv} ({len(table)} rows)")

    summary = run_pipeline(demo_csv)
    print("pipeline summary:")
    for key, value in summary.items():
        print(f"  {key}: {value}")
    print("done.")


if __name__ == "__main__":
    main()
