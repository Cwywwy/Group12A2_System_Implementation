# -*- coding: utf-8 -*-
"""
compare_runs.py
Author: Group12A2 DSW Team
Purpose: Compare two experiment runs (outputs/tables directories) side by side so
         a change in the text dictionary or in the benchmark definition can be
         read off directly instead of being inferred from two sets of logs.
Module: scripts

Usage
-----
python scripts/compare_runs.py --old outputs/.tmp/v01_prev_run/tables \
                               --new outputs/tables [--label-old v0.1 --label-new v0.2]

The script only reads the CSV tables written by scripts/run_07_experiment.py and
prints a diff report to stdout; it never modifies the run outputs.

Revision History
----------------
2026-11-11  initial version.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

MODELS = ("if_finance", "if_text", "if_fused", "ae_fused")
MODEL_LABELS = {
    "if_finance": "Finance-only IF",
    "if_text": "Text-only IF",
    "if_fused": "Fused IF",
    "ae_fused": "Fused autoencoder",
}


def _read(directory: Path, name: str) -> pd.DataFrame | None:
    path = directory / name
    if not path.exists():
        return None
    return pd.read_csv(path)


def _fmt(value: float, digits: int = 3) -> str:
    return "n/a" if pd.isna(value) else f"{value:.{digits}f}"


def _fmt_p(value: float) -> str:
    if pd.isna(value):
        return "n/a"
    return "< 0.001" if value < 0.001 else f"{value:.3f}"


def _topk_row(table: pd.DataFrame, benchmark: str, model: str, k: float):
    """Return the matching row, tolerating legacy tables without a benchmark column."""
    if "benchmark" not in table.columns:
        if benchmark != "legacy":
            return None
        subset = table
    else:
        subset = table[table["benchmark"] == benchmark]
    match = subset[(subset["model"] == model) & (subset["k"] == k)]
    return None if match.empty else match.iloc[0]


def _with_change(old: float, new: float, digits: int = 3) -> str:
    if pd.isna(old) or pd.isna(new):
        return f"{_fmt(new, digits)} (n/a)"
    return f"{_fmt(old, digits)} -> {_fmt(new, digits)} ({new - old:+.{digits}f})"


def section(title: str) -> None:
    print()
    print(title)
    print("-" * len(title))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--old", type=str, default="outputs/.tmp/v01_prev_run/tables")
    parser.add_argument("--new", type=str, default="outputs/tables")
    parser.add_argument("--label-old", type=str, default="v0.1")
    parser.add_argument("--label-new", type=str, default="v0.2")
    args = parser.parse_args()

    old_dir = Path(args.old)
    new_dir = Path(args.new)
    for directory in (old_dir, new_dir):
        if not directory.exists():
            raise SystemExit(f"missing results directory: {directory}")

    print(f"old = {old_dir} ({args.label_old})")
    print(f"new = {new_dir} ({args.label_new})")

    section(f"Sample ({args.label_old} -> {args.label_new})")
    old_scores = _read(old_dir, "anomaly_scores.csv")
    new_scores = _read(new_dir, "anomaly_scores.csv")
    if old_scores is not None and new_scores is not None:
        print(f"firm-years        {len(old_scores):,} -> {len(new_scores):,}")
        print(f"firms             {old_scores['symbol'].nunique():,} -> "
              f"{new_scores['symbol'].nunique():,}")
        print(f"legacy flag rate  {_with_change(old_scores['benchmark_flag'].mean(), new_scores['benchmark_flag'].mean())}")
        print(f"decile cut-off    {_with_change(old_scores['m_score'].quantile(0.90), new_scores['m_score'].quantile(0.90), 2)}")

    section("Spearman rho against the Beneish M-Score")
    old_metrics = _read(old_dir, "model_metrics.csv")
    new_metrics = _read(new_dir, "model_metrics.csv")
    if old_metrics is not None and new_metrics is not None:
        old_metrics = old_metrics.set_index("model")
        new_metrics = new_metrics.set_index("model")
        for model in MODELS:
            if model in old_metrics.index and model in new_metrics.index:
                old_rho = old_metrics.loc[model, "spearman_rho"]
                new_rho = new_metrics.loc[model, "spearman_rho"]
                old_p = old_metrics.loc[model, "spearman_p"]
                new_p = new_metrics.loc[model, "spearman_p"]
                print(f"{MODEL_LABELS[model]:<20} rho {_with_change(old_rho, new_rho)}   "
                      f"p {_fmt_p(old_p)} -> {_fmt_p(new_p)}")

    section("Top-k enrichment (calibrated benchmark, M top-10%)")
    old_topk = _read(old_dir, "topk_metrics.csv")
    new_topk = _read(new_dir, "topk_metrics.csv")
    if old_topk is not None and new_topk is not None:
        for benchmark in ("calibrated", "legacy"):
            print(f"[{benchmark}]")
            for model in MODELS:
                for k in (0.05, 0.10, 0.15):
                    old_row = _topk_row(old_topk, benchmark, model, k)
                    new_row = _topk_row(new_topk, benchmark, model, k)
                    if old_row is None or new_row is None:
                        continue
                    old_enrich = float(old_row["enrichment"])
                    new_enrich = float(new_row["enrichment"])
                    print(f"  {MODEL_LABELS[model]:<20} k={k:.0%}  "
                          f"enrichment {_with_change(old_enrich, new_enrich)}")

    section("SHAP group shares")
    old_group = _read(old_dir, "shap_group_contributions.csv")
    new_group = _read(new_dir, "shap_group_contributions.csv")
    if old_group is not None and new_group is not None:
        old_group = old_group.set_index("group")
        new_group = new_group.set_index("group")
        for group in ("finance", "text"):
            if group in old_group.index and group in new_group.index:
                print(f"{group:<8} {_with_change(old_group.loc[group, 'abs_shap_share'],
                                                new_group.loc[group, 'abs_shap_share'])}")

    section("Ranking overlap (top-10% Jaccard)")
    old_overlap = _read(old_dir, "ranking_overlap.csv")
    new_overlap = _read(new_dir, "ranking_overlap.csv")
    if old_overlap is not None and new_overlap is not None:
        for _, row in new_overlap.iterrows():
            pair = (row["model_a"], row["model_b"])
            if pair[0] == pair[1]:
                continue
            match = old_overlap[(old_overlap["model_a"] == pair[0])
                                & (old_overlap["model_b"] == pair[1])]
            old_value = float(match["top10_overlap"].iloc[0]) if not match.empty else float("nan")
            print(f"{pair[0]:<12} vs {pair[1]:<12} "
                  f"{_with_change(old_value, float(row['top10_overlap']))}")

    section("Top-ranked firm-year")
    for label, scores in ((args.label_old, old_scores), (args.label_new, new_scores)):
        if scores is None:
            continue
        column = "if_fused" if "if_fused" in scores.columns else None
        if column is None:
            continue
        top = scores.sort_values(column, ascending=False).iloc[0]
        print(f"{label}: {str(top['symbol']).zfill(6)} ({int(top['fiscal_year'])}) "
              f"score {_fmt(top[column])} M-Score {_fmt(top['m_score'], 1)}")


if __name__ == "__main__":
    main()
