# -*- coding: utf-8 -*-
"""
run_00_coverage_gate.py
Author: Group12A2 DSW Team
Purpose: Coverage gate that checks, per fiscal year, how many manufacturing
         firm-years survive each pipeline stage, and whether a newly extended
         year is complete enough to be reported alongside the existing sample.
Module: scripts

Usage
-----
    python scripts/run_00_coverage_gate.py
    python scripts/run_00_coverage_gate.py --interim data/interim/finance_intermediate_p2025.csv

The gate compares the newest year's complete-case count with the previous year's
and fails when the ratio falls below --threshold (default 0.90). Output is a
markdown report written to --out, plus a console summary.

Revision History
-----------------
2026-11-26  initial version; Phase 0 gate for the 2025 extension.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config import CNINFO_RAW, DATA_INTERIM, DATA_PROCESSED, REPORTS  # noqa: E402

SIX_INPUTS = (
    "net_income",
    "total_assets",
    "total_liabilities",
    "revenue",
    "receivables",
    "ocf",
)

# Depreciation is deliberately absent: the direct-method cash-flow export has no
# such line, so DEPI is neutralised at 1.0 in src/features/beneish.py. The
# M-Score additionally needs the same fields one year earlier for the index
# denominators; the gate therefore treats this column as an upper bound.
BENEISH_INPUTS = SIX_INPUTS + (
    "cogs",
    "current_assets",
    "fixed_assets",
    "sga",
)

DEFAULT_INTERIM = DATA_INTERIM / "finance_intermediate_p2025.csv"
DEFAULT_OUT = REPORTS / "phase0_2025_coverage.md"


def _pdf_symbols(fiscal_year: int) -> set[str]:
    folder = CNINFO_RAW / str(fiscal_year)
    if not folder.exists():
        return set()
    return {path.name.split("_")[0] for path in folder.glob("*.pdf")}


def build_coverage(interim: Path) -> pd.DataFrame:
    """Return one row per fiscal year with frame, download and completeness counts."""
    frame = pd.read_csv(DATA_PROCESSED / "manufacturing_sample_frame.csv", dtype={"symbol": str})
    frame["symbol"] = frame["symbol"].str.zfill(6)
    fin = pd.read_csv(interim, dtype={"symbol": str})
    fin["symbol"] = fin["symbol"].str.zfill(6)

    missing = [column for column in (*SIX_INPUTS, *BENEISH_INPUTS) if column not in fin.columns]
    if missing:
        raise KeyError(f"intermediate file lacks required columns: {missing}")

    fin["six_ok"] = fin[list(SIX_INPUTS)].notna().all(axis=1)
    fin["beneish_ok"] = fin[list(BENEISH_INPUTS)].notna().all(axis=1)

    rows = []
    for year, group in frame.groupby("fiscal_year"):
        year = int(year)
        symbols = set(group["symbol"])
        merged = fin.loc[(fin["fiscal_year"] == year) & (fin["symbol"].isin(symbols))]
        rows.append(
            {
                "fiscal_year": year,
                "frame": len(symbols),
                "pdf": len(symbols & _pdf_symbols(year)),
                "six": int(merged["six_ok"].sum()),
                "beneish": int(merged["beneish_ok"].sum()),
            }
        )
    table = pd.DataFrame(rows).sort_values("fiscal_year").reset_index(drop=True)
    table["rate_of_frame"] = table["beneish"] / table["frame"]
    table["rate_within_previous"] = table["beneish"] / table["beneish"].shift(1)
    return table


def render(table: pd.DataFrame, threshold: float, interim: Path) -> tuple[str, bool]:
    """Return the markdown report and whether the gate passed."""
    latest = int(table["fiscal_year"].max())
    latest_ratio = float(table.loc[table["fiscal_year"] == latest, "rate_within_previous"].iloc[-1])
    passed = latest_ratio >= threshold

    lines = [
        "# Phase 0 coverage gate: fiscal-year extension",
        "",
        f"Source intermediate file: `{interim.name}`",
        f"Gate: complete-case coverage of the newest year (FY{latest}) must reach "
        f"{threshold:.0%} of the previous year.",
        "",
        "| Fiscal year | Frame | PDF on disk | Six financial inputs | Beneish inputs | Share of frame | vs previous year |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in table.itertuples():
        ratio = "—" if pd.isna(row.rate_within_previous) else f"{row.rate_within_previous:.3f}"
        lines.append(
            f"| FY{row.fiscal_year} | {row.frame:,} | {row.pdf:,} | {row.six:,} | "
            f"{row.beneish:,} | {row.rate_of_frame:.1%} | {ratio} |"
        )
    lines += [
        "",
        f"**Verdict: {'PASS' if passed else 'FAIL'}** — FY{latest} reaches {latest_ratio:.3f} "
        f"of the previous year's complete cases (threshold {threshold:.2f}).",
        "",
        "Notes",
        "",
        "- FY2020 enters only as the base year for growth and Beneish components; it is not a modelling year.",
        "- `depreciation` is absent from the direct-method cash-flow export, so the depreciation index is "
        "neutralised at 1.0 rather than imputed.",
        "- Frame counts come from `data/processed/sample_frame.csv`; PDF counts count distinct symbols with "
        "at least one PDF on disk for that fiscal year.",
        "",
    ]
    return "\n".join(lines), passed


def main() -> None:
    parser = argparse.ArgumentParser(description="Per-year coverage gate for the extended panel.")
    parser.add_argument("--interim", type=Path, default=DEFAULT_INTERIM)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--threshold", type=float, default=0.90)
    args = parser.parse_args()

    if not args.interim.exists():
        raise FileNotFoundError(f"intermediate file not found: {args.interim}")

    table = build_coverage(args.interim)
    report, passed = render(table, args.threshold, args.interim)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(report, encoding="utf-8")

    print(table.to_string(index=False))
    print(f"\n[run_00] gate {'PASSED' if passed else 'FAILED'}; report -> {args.out}")


if __name__ == "__main__":
    main()
