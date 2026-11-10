"""narrate_results.py

File:     src/reporting/narrate_results.py
Author:   Group12A2 DSW Team
Purpose:  turn the pipeline output tables into manuscript-ready English Results
          paragraphs (RQ1-RQ3) for the 24 Nov experiment chapter.
Module:   src/reporting (results narration)

Revision History:
  2026-11-06  initial version: RQ1/RQ2/RQ3 narrators over pipeline CSVs.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

SCORE_MODELS = ("if_finance", "if_text", "if_fused", "ae_fused")
BENCHMARK_LABELS = {"legacy": "M > -1.78", "calibrated": "M top-10%"}


def _f(x, digits: int = 3) -> str:
    if pd.isna(x):
        return "n.a."
    return f"{float(x):.{digits}f}"


def _metrics_row(metrics: pd.DataFrame, model: str) -> dict:
    row = metrics.loc[metrics["model"] == model]
    if row.empty:
        return {"model": model, "spearman_rho": float("nan"), "spearman_p": float("nan")}
    return row.iloc[0].to_dict()


def narrate_rq1(metrics: pd.DataFrame) -> str:
    """Spearman correlation of each anomaly score against the Beneish M-Score."""
    fin = _metrics_row(metrics, "if_finance")
    text = _metrics_row(metrics, "if_text")
    fused = _metrics_row(metrics, "if_fused")
    ae = _metrics_row(metrics, "ae_fused")
    lines = [
        "## RQ1: Incremental value of textual features",
        "",
        "| Model | Spearman rho (vs M-Score) | p-value |",
        "| --- | --- | --- |",
        f"| Finance-only IF | {_f(fin['spearman_rho'])} | {_f(fin['spearman_p'])} |",
        f"| Text-only IF | {_f(text['spearman_rho'])} | {_f(text['spearman_p'])} |",
        f"| Fused IF | {_f(fused['spearman_rho'])} | {_f(fused['spearman_p'])} |",
        f"| Fused autoencoder | {_f(ae['spearman_rho'])} | {_f(ae['spearman_p'])} |",
        "",
        f"The finance-only score correlates with the M-Score at rho = {_f(fin['spearman_rho'])}, "
        f"the text-only score at rho = {_f(text['spearman_rho'])}, and the fused score at "
        f"rho = {_f(fused['spearman_rho'])}. "
        + (
            "Adding the three textual features raises rank agreement with the accounting "
            "benchmark, consistent with the expectation that disclosure tone carries "
            "incremental information."
            if fused["spearman_rho"] > fin["spearman_rho"]
            else "The fused score does not improve rank agreement with the accounting "
                 "benchmark over the finance-only score in this sample."
        ),
        "",
    ]
    return "\n".join(lines)


def narrate_rq2(global_df: pd.DataFrame, group_df: pd.DataFrame,
                local_df: pd.DataFrame) -> str:
    """SHAP global importance and finance-vs-text group shares."""
    lines = [
        "## RQ2: Feature group contributions",
        "",
        "| Group | Share of absolute SHAP | Features |",
        "| --- | --- | --- |",
    ]
    for _, row in group_df.iterrows():
        lines.append(f"| {row['group']} | {_f(row['abs_shap_share'])} | "
                     f"{int(row['n_features'])} |")
    lines.append("")
    top = global_df.sort_values("mean_abs_shap", ascending=False).head(3)
    if not top.empty:
        lines.append("The largest global SHAP contributions come from "
                     + ", ".join(f"{r.feature} ({_f(r.mean_abs_shap)})"
                                 for r in top.itertuples(index=False)) + ".")
    if not local_df.empty:
        first = local_df.iloc[0]
        lines.append(
            f"For the top-ranked firm-year, the largest local drivers are "
            f"{_f(local_df['shap_value'].abs().max())} in absolute SHAP; "
            f"the feature with the largest absolute value is "
            f"{local_df.loc[local_df['shap_value'].abs().idxmax(), 'feature']}."
        )
    lines.append("")
    return "\n".join(lines)


def narrate_rq3(overlap: pd.DataFrame, topk: pd.DataFrame) -> str:
    """Ranking overlap between model pairs and sensitivity across k."""
    lines = [
        "## RQ3: Ranking stability",
        "",
        "| Pair | Top-10% overlap |",
        "| --- | --- |",
    ]
    for _, row in overlap.iterrows():
        if row["model_a"] == row["model_b"]:
            continue  # drop the diagonal self-pairs, they carry no information
        lines.append(f"| {row['model_a']} vs {row['model_b']} | "
                     f"{_f(row['top10_overlap'])} |")
    lines.append("")
    lines.append("| Benchmark | Model | k | Event rate | Enrichment |")
    lines.append("| --- | --- | --- | --- | --- |")
    for _, row in topk.iterrows():
        label = BENCHMARK_LABELS.get(row["benchmark"], row["benchmark"])
        lines.append(f"| {label} | {row['model']} | {row['k']} | {_f(row['event_rate'])} | "
                     f"{_f(row['enrichment'])} |")
    lines.append("")
    fused = topk.loc[(topk["model"] == "if_fused") & (topk["k"] == 0.10)
                     & (topk["benchmark"] == "calibrated")]
    if not fused.empty:
        r = fused.iloc[0]
        lines.append(
            f"At the top-10% review threshold the fused model flags {_f(r['event_rate'])} "
            f"of the sample-calibrated benchmark (top-decile M-Score), i.e. "
            f"{_f(r['enrichment'])}x the 10% benchmark rate, which supports its use as "
            f"a screening signal rather than a definitive risk label."
        )
    lines.append("")
    return "\n".join(lines)


def load_pipeline_tables(tables_dir: str | Path) -> dict[str, pd.DataFrame]:
    d = Path(tables_dir)
    names = ["model_metrics", "topk_metrics", "ranking_overlap", "shap_global",
             "shap_group_contributions", "shap_local_top1", "anomaly_scores"]
    tables: dict[str, pd.DataFrame] = {}
    for name in names:
        path = d / f"{name}.csv"
        if path.exists():
            tables[name] = pd.read_csv(path)
    return tables


def build_results_narrative(tables_dir: str | Path,
                            descriptives_path: str | Path | None = None) -> str:
    tables = load_pipeline_tables(tables_dir)
    required = {"model_metrics", "topk_metrics", "ranking_overlap", "shap_global",
                "shap_group_contributions", "shap_local_top1"}
    missing = sorted(required - set(tables))
    if missing:
        raise FileNotFoundError(
            f"missing pipeline tables in {tables_dir}: {', '.join(missing)}")
    header = ["# Results (auto-narrated)", "",
              "_Generated from outputs/tables; review, discuss, and delete this "
              "header for the final chapter._", ""]
    parts = [
        "\n".join(header),
        narrate_rq1(tables["model_metrics"]),
        narrate_rq2(tables["shap_global"], tables["shap_group_contributions"],
                    tables["shap_local_top1"]),
        narrate_rq3(tables["ranking_overlap"], tables["topk_metrics"]),
    ]
    if descriptives_path and Path(descriptives_path).exists():
        parts.append(f"Sample descriptives: see {Path(descriptives_path).name}.")
    return "\n".join(parts) + "\n"
