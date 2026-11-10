# -*- coding: utf-8 -*-
"""
pipeline.py
Author: Group12A2 DSW Team
Purpose: End-to-end modelling and evaluation pipeline (Phase 3).
Module: src

Steps: load the feature table -> winsorise -> standardise within
subindustry-year cells (sparse-cell fallback) -> three Isolation Forest
rankings (finance only / text only / fused) plus an autoencoder on the fused
matrix -> benchmark flags (legacy Beneish M > -1.78 plus a sample-calibrated
top-decile M-Score flag; never used in training) ->
metrics tables (Spearman rho, top-k event rate, enrichment ratio, top-k
overlap) -> SHAP global, group and local explanations.

Revision History
-----------------
2026-11-05  initial version.
2026-11-06  reuse the fused Isolation Forest for SHAP instead of refitting;
            align the top-1 local explanation with the SHAP subsample index
            (fixes row misalignment when the sample exceeds SHAP_SAMPLE_CAP).
2026-11-10  force-include the top-1 review-priority row in the SHAP subsample
            so its local explanation never raises KeyError when the sample is
            capped (n > 2000).
2026-11-11  add a second, sample-calibrated benchmark flag (top-decile M-Score)
            alongside the legacy -1.78 flag; top-k metrics are reported per
            benchmark ("legacy" vs "calibrated").
"""
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import (
    ALL_FEATURES,
    BENEISH_THRESHOLD,
    BENEISH_TOP_QUANTILE,
    FINANCE_FEATURES,
    OUTPUTS,
    SEED,
    TEXT_FEATURES,
)
from src.evaluation.metrics import (
    enrichment_ratio,
    spearman_corr,
    top_k_event_rate,
    top_k_overlap,
)
from src.features.standardise import standardise_within_groups, winsorize_columns
from src.models.autoencoder import (
    fit_autoencoder,
    reconstruction_errors,
    record_autoencoder_config,
)
from src.models.isolation_forest import (
    anomaly_scores,
    fit_isolation_forest,
    top_k_indices,
)
from src.models.shap_explain import (
    global_importance,
    group_contributions,
    local_explanation,
    shap_values,
)

SHAP_SAMPLE_CAP = 2000
K_VALUES = (0.05, 0.10, 0.15)


def _full_sample_z(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Fallback standardisation across the whole sample (ddof=0, std=0 -> 1)."""
    z = df.copy()
    for col in columns:
        mean = df[col].mean()
        std = df[col].std(ddof=0)
        z[col] = (df[col] - mean) / (1.0 if std == 0 else std)
    return z


def run_pipeline(feature_csv: Path, output_dir: Path | None = None) -> dict:
    """Run the full Phase 3 pipeline and write all output tables."""
    output_dir = Path(output_dir) if output_dir else OUTPUTS
    tables_dir = output_dir / "tables"
    reports_dir = output_dir / "reports"
    tables_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(feature_csv)
    id_columns = [c for c in ("symbol", "fiscal_year", "industry_code_d") if c in df.columns]
    work = df.dropna(subset=list(ALL_FEATURES) + ["m_score"]).copy()
    if work.empty:
        raise ValueError("No complete rows after dropping missing features or M-Score.")

    work = winsorize_columns(work, ALL_FEATURES)
    if "industry_code_d" in work.columns and "fiscal_year" in work.columns:
        z = standardise_within_groups(work, ALL_FEATURES)
    else:
        z = _full_sample_z(work, ALL_FEATURES)

    finance_z = z[list(FINANCE_FEATURES)]
    text_z = z[list(TEXT_FEATURES)]
    fused_z = z[list(ALL_FEATURES)]
    rankings: dict[str, np.ndarray] = {}
    fused_model = None
    for name, matrix in (("if_finance", finance_z), ("if_text", text_z), ("if_fused", fused_z)):
        model = fit_isolation_forest(matrix)
        if name == "if_fused":
            fused_model = model
        rankings[name] = anomaly_scores(model, matrix)

    autoencoder = fit_autoencoder(fused_z)
    rankings["ae_fused"] = reconstruction_errors(autoencoder, fused_z)
    record_autoencoder_config(out_path=reports_dir / "autoencoder_config.json")

    flags = (work["m_score"] > BENEISH_THRESHOLD).astype(int).to_numpy()
    calibrated_flags = np.zeros(len(work), dtype=int)
    calibrated_flags[top_k_indices(work["m_score"].to_numpy(), BENEISH_TOP_QUANTILE)] = 1
    benchmark_flags = {"legacy": flags, "calibrated": calibrated_flags}

    spearman_rows = []
    for name, scores in rankings.items():
        rho, p_value = spearman_corr(scores, work["m_score"].to_numpy())
        spearman_rows.append({"model": name, "spearman_rho": rho, "spearman_p": p_value})
    pd.DataFrame(spearman_rows).to_csv(tables_dir / "model_metrics.csv", index=False)

    topk_rows = []
    for benchmark_name, flag_arr in benchmark_flags.items():
        for name, scores in rankings.items():
            for k in K_VALUES:
                topk_rows.append({
                    "benchmark": benchmark_name,
                    "model": name,
                    "k": k,
                    "event_rate": top_k_event_rate(scores, flag_arr, k),
                    "enrichment": enrichment_ratio(scores, flag_arr, k),
                })
    pd.DataFrame(topk_rows).to_csv(tables_dir / "topk_metrics.csv", index=False)

    overlap_rows = []
    for name_a, scores_a in rankings.items():
        for name_b, scores_b in rankings.items():
            overlap_rows.append({
                "model_a": name_a,
                "model_b": name_b,
                "top10_overlap": top_k_overlap(scores_a, scores_b, k=0.10),
            })
    pd.DataFrame(overlap_rows).to_csv(tables_dir / "ranking_overlap.csv", index=False)

    scores_out = work[id_columns].reset_index(drop=True)
    for name, scores in rankings.items():
        scores_out[name] = scores
    scores_out["m_score"] = work["m_score"].to_numpy()
    scores_out["benchmark_flag"] = flags
    scores_out["benchmark_flag_calibrated"] = calibrated_flags
    scores_out.to_csv(tables_dir / "anomaly_scores.csv", index=False)

    # SHAP on the fused model (reused from the ranking loop), capped for runtime
    # with a seeded subsample. The top-1 review-priority row is force-included so
    # its local explanation is always available even when the sample is capped.
    top1_pos = int(np.argmax(rankings["if_fused"]))
    top1_index = work.index[top1_pos]
    if len(work) <= SHAP_SAMPLE_CAP:
        shap_frame = work
    else:
        subsample = work.sample(SHAP_SAMPLE_CAP - 1, random_state=SEED)
        if top1_index not in subsample.index:
            subsample = pd.concat([subsample, work.loc[[top1_index]]])
        shap_frame = subsample
    shap_matrix = shap_values(fused_model, fused_z.loc[shap_frame.index])
    global_importance(shap_matrix, ALL_FEATURES).to_csv(tables_dir / "shap_global.csv", index=False)
    group_contributions(shap_matrix, ALL_FEATURES).to_csv(tables_dir / "shap_group_contributions.csv", index=False)
    local_position = shap_frame.index.get_loc(top1_index)
    local_explanation(shap_matrix, ALL_FEATURES, local_position).to_csv(
        tables_dir / "shap_local_top1.csv", index=False
    )

    summary = {
        "n_rows": int(len(work)),
        "spearman": {r["model"]: round(r["spearman_rho"], 4) for r in spearman_rows},
        "event_rate_top10": {
            r["model"]: round(r["event_rate"], 4)
            for r in topk_rows if r["k"] == 0.10 and r["benchmark"] == "calibrated"
        },
        "enrichment_top10": {
            r["model"]: round(r["enrichment"], 4)
            for r in topk_rows if r["k"] == 0.10 and r["benchmark"] == "calibrated"
        },
        "event_rate_top10_legacy": {
            r["model"]: round(r["event_rate"], 4)
            for r in topk_rows if r["k"] == 0.10 and r["benchmark"] == "legacy"
        },
        "enrichment_top10_legacy": {
            r["model"]: round(r["enrichment"], 4)
            for r in topk_rows if r["k"] == 0.10 and r["benchmark"] == "legacy"
        },
        "top1_symbol": str(work.iloc[int(np.argmax(rankings["if_fused"]))]["symbol"]),
    }
    return summary
