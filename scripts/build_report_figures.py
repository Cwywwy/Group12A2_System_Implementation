# -*- coding: utf-8 -*-
"""
build_report_figures.py
Author: Group12A2 DSW Team
Purpose: Render the six English manuscript figures from the current result tables.
Module: scripts

The Chinese figures in src/reporting/figures.py serve the Chinese manuscript;
this script produces the English plates used in Group12A2_Final_EN.docx, so
that the figures and the tables are regenerated from one set of outputs.

Revision History
----------------
2026-11-23  initial version: six English plates for the corrected rerun.
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

TABLES = Path("outputs/tables")
OUT = Path("outputs/figures/manuscript")

BLUE = "#4C72B0"
GREEN = "#55A868"
RED = "#C44E52"
PURPLE = "#8172B3"
GREY = "#7F7F7F"

MODELS = [
    ("if_finance", "Finance-only IF"),
    ("if_text", "Text-only IF"),
    ("if_fused", "Fused IF"),
    ("ae_fused", "Fused AE"),
]


def _style() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 9,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "axes.grid.axis": "y",
            "grid.alpha": 0.25,
            "figure.dpi": 200,
            "savefig.dpi": 200,
        }
    )


def _save(fig, name: str) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / name
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path


def figure_51(figures: pd.DataFrame) -> Path:
    """Annual frame and complete-case counts."""
    _style()
    years = sorted(figures["fiscal_year"].unique())
    frame = [int(figures.loc[figures["fiscal_year"] == y, "frame"].iloc[0]) for y in years]
    complete = [
        int(figures.loc[figures["fiscal_year"] == y, "complete"].iloc[0]) for y in years
    ]
    fig, ax = plt.subplots(figsize=(5.7, 2.95))
    x = range(len(years))
    width = 0.38
    ax.bar([i - width / 2 for i in x], frame, width, color=BLUE, label="Sample frame")
    ax.bar([i + width / 2 for i in x], complete, width, color=GREEN, label="Complete case")
    for i, (a, b) in enumerate(zip(frame, complete)):
        ax.text(i - width / 2, a + 40, f"{a:,}", ha="center", fontsize=7.5)
        ax.text(i + width / 2, b + 40, f"{b:,}", ha="center", fontsize=7.5)
    ax.set_xticks(list(x))
    ax.set_xticklabels([str(y) for y in years])
    ax.set_ylabel("Firm-years")
    ax.set_title("Sample construction by fiscal year")
    ax.legend(frameon=False, loc="lower right")
    ax.set_ylim(0, max(frame) * 1.18)
    return _save(fig, "figure_5_1_sample.png")


def figure_52(metrics: pd.DataFrame) -> Path:
    """Spearman correlation with the Beneish M-Score."""
    _style()
    labels, values, pvals = [], [], []
    for model_id, label in MODELS:
        row = metrics[metrics["model"] == model_id]
        labels.append(label)
        values.append(float(row["spearman_rho"].iloc[0]))
        pvals.append(float(row["spearman_p"].iloc[0]))
    colours = [BLUE, GREEN, RED, PURPLE]
    fig, ax = plt.subplots(figsize=(5.7, 2.95))
    bars = ax.barh(labels[::-1], values[::-1], color=colours[::-1], height=0.55)
    ax.axvline(0, color=GREY, linewidth=0.9)
    for bar, value, p in zip(bars, values[::-1], pvals[::-1]):
        offset = 0.004 if value >= 0 else -0.004
        ax.text(value + offset, bar.get_y() + bar.get_height() / 2, f"{value:.3f}",
                va="center", ha="left" if value >= 0 else "right", fontsize=8)
    ax.set_xlim(min(values) - 0.02, 0.02)
    ax.set_xlabel("Spearman rank correlation with the Beneish M-Score")
    ax.set_title("Rank association with the Beneish benchmark")
    return _save(fig, "figure_5_2_spearman.png")


def figure_53(topk: pd.DataFrame) -> Path:
    """Top-10% enrichment under the calibrated benchmark."""
    _style()
    order = [("if_finance", "Finance-only IF"), ("if_text", "Text-only IF"),
             ("if_fused", "Fused IF"), ("ae_fused", "Fused AE")]
    labels, values = [], []
    for model, label in order:
        row = topk[
            (topk["model"] == model)
            & (topk["k"].astype(float) == 0.10)
            & (topk["benchmark"] == "calibrated")
        ]
        labels.append(label)
        values.append(float(row["enrichment"].iloc[0]))
    colours = [BLUE, GREEN, RED, PURPLE]
    fig, ax = plt.subplots(figsize=(5.7, 2.95))
    bars = ax.bar(labels, values, color=colours, width=0.6)
    ax.axhline(1.0, color=GREY, linestyle="--", linewidth=0.9)
    for bar, value in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, value + 0.03, f"{value:.2f}x",
                ha="center", fontsize=8)
    ax.set_ylabel("Enrichment (top 10% vs base rate)")
    ax.set_title("Top-10% review-queue enrichment, calibrated benchmark")
    ax.set_ylim(0, max(values) * 1.18)
    return _save(fig, "figure_5_3_enrichment.png")


def figure_54(contrib: pd.DataFrame) -> Path:
    """SHAP group shares."""
    _style()
    data = contrib.set_index("group")["abs_shap_share"]
    labels = ["Financial features", "Textual features"]
    values = [float(data.get("finance", 0.0)) * 100, float(data.get("text", 0.0)) * 100]
    fig, ax = plt.subplots(figsize=(5.7, 2.65))
    bars = ax.barh(labels[::-1], values[::-1], color=[GREEN, BLUE], height=0.5)
    for bar, value in zip(bars, values[::-1]):
        ax.text(value - 2, bar.get_y() + bar.get_height() / 2, f"{value:.1f}%",
                va="center", ha="right", color="white", fontsize=9)
    ax.set_xlim(0, 100)
    ax.set_xlabel("Share of absolute SHAP contribution (%)")
    ax.set_title("Feature-group contribution to the fused model")
    return _save(fig, "figure_5_4_shap_share.png")


def figure_55(ranking: pd.DataFrame) -> Path:
    """AUC against the two external outcomes."""
    _style()
    rows = [("finance-only IF", "Finance-only IF"), ("text-only IF", "Text-only IF"),
            ("fused IF", "Fused IF"), ("fused AE", "Fused AE"),
            ("Beneish M-Score", "Beneish M-Score")]
    labels = [label for _, label in rows]
    opinion = [
        float(ranking.loc[(ranking["model"] == key) & (ranking["label"] == "mod_opinion"), "auc"].iloc[0])
        for key, _ in rows
    ]
    disclosure = [
        float(
            ranking.loc[
                (ranking["model"] == key)
                & (ranking["label"] == "violation_disclosure_t1"),
                "auc",
            ].iloc[0]
        )
        for key, _ in rows
    ]
    import numpy as np

    x = np.arange(len(labels))
    width = 0.38
    fig, ax = plt.subplots(figsize=(5.9, 3.0))
    ax.bar(x - width / 2, opinion, width, color=BLUE, label="Modified audit opinion")
    ax.bar(x + width / 2, disclosure, width, color=GREEN, label="Disclosure violation t+1")
    ax.axhline(0.5, color=GREY, linestyle="--", linewidth=0.9)
    for i, (a, b) in enumerate(zip(opinion, disclosure)):
        ax.text(i - width / 2, a + 0.012, f"{a:.2f}", ha="center", fontsize=7)
        ax.text(i + width / 2, b + 0.012, f"{b:.2f}", ha="center", fontsize=7)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=18, ha="right", fontsize=7.5)
    ax.set_ylabel("AUC")
    ax.set_ylim(0, 1.0)
    ax.set_title("Ranking quality against external regulatory outcomes")
    ax.legend(frameon=False, fontsize=7.5, loc="upper right")
    return _save(fig, "figure_5_5_external_auc.png")


def figure_56(supervised: pd.DataFrame) -> Path:
    """Out-of-fold AUC for finance-only and fused models."""
    _style()
    import numpy as np

    outcomes = [
        ("mod_opinion", "Modified opinion"),
        ("violation_disclosure_t1", "Disclosure violation t+1"),
    ]
    models = [("logit", "Logit"), ("hgb", "Gradient boosting")]
    fig, axes = plt.subplots(1, 2, figsize=(5.9, 2.7), sharey=True)
    for ax, (outcome, title) in zip(axes, outcomes):
        sub = supervised[supervised["label"] == outcome]
        x = np.arange(len(models))
        width = 0.36
        finance = [
            float(sub[(sub["model"] == m) & (sub["feature_set"] == "finance")]["oof_auc"].iloc[0])
            for m, _ in models
        ]
        fused = [
            float(sub[(sub["model"] == m) & (sub["feature_set"] == "fused")]["oof_auc"].iloc[0])
            for m, _ in models
        ]
        ax.bar(x - width / 2, finance, width, color=BLUE, label="Finance only")
        ax.bar(x + width / 2, fused, width, color=RED, label="Fused")
        for i, (a, b) in enumerate(zip(finance, fused)):
            ax.text(i - width / 2, a + 0.01, f"{a:.3f}", ha="center", fontsize=6.5)
            ax.text(i + width / 2, b + 0.01, f"{b:.3f}", ha="center", fontsize=6.5)
        ax.set_xticks(x)
        ax.set_xticklabels([label for _, label in models], fontsize=7.5)
        ax.set_title(title, fontsize=8.5)
        ax.set_ylim(0, 1.0)
    axes[0].set_ylabel("Out-of-fold AUC")
    axes[0].legend(frameon=False, fontsize=7, loc="upper left")
    return _save(fig, "figure_5_6_supervised.png")


def figure_41_pipeline() -> Path:
    """Three-stage schematic of the study pipeline (Section 4.1)."""
    from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8, "savefig.dpi": 200})
    fig, ax = plt.subplots(figsize=(9.2, 4.4))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 60)
    ax.axis("off")

    def box(x: float, y: float, w: float, h: float, title: str, detail: str, shade: str) -> tuple[float, float]:
        ax.add_patch(
            FancyBboxPatch(
                (x, y), w, h,
                boxstyle="round,pad=0.35,rounding_size=1.2",
                linewidth=0.8, edgecolor="#4C72B0", facecolor=shade,
            )
        )
        ax.text(x + w / 2, y + h * 0.63, title, ha="center", va="center", fontsize=8.4, weight="bold")
        ax.text(x + w / 2, y + h * 0.3, detail, ha="center", va="center", fontsize=7.1, color="#333333")
        return x + w / 2, y + h / 2

    def right_arrow(x0: float, x1: float, y: float) -> None:
        ax.add_patch(FancyArrowPatch((x0, y), (x1, y), arrowstyle="-|>", mutation_scale=9, linewidth=0.9, color="#555555"))

    def down_arrow(x: float, y0: float, y1: float) -> None:
        ax.add_patch(FancyArrowPatch((x, y0), (x, y1), arrowstyle="-|>", mutation_scale=9, linewidth=0.9, color="#555555"))

    def stage_label(y: float, text: str) -> None:
        ax.text(0.4, y, text, ha="left", va="center", fontsize=7.6, weight="bold", color="#4C72B0", rotation=90)

    # Stage 1: data acquisition, sequential.
    stage_label(51.0, "ACQUISITION")
    row1 = [
        (6.5, 19.5, "Sample frame", "CSMAR, manufacturing\n2021-2025"),
        (30.0, 19.5, "Statement parsing", "income, balance sheet,\ncash flow"),
        (53.5, 19.5, "Annual-report PDFs", "CNINFO,\none file per firm-year"),
        (77.0, 19.5, "MD&A extraction", "section detection,\nstatus per firm-year"),
    ]
    for x, w, title, detail in row1:
        box(x, 46, w, 9, title, detail, "#EEF2F8")
    for i in range(3):
        right_arrow(row1[i][0] + row1[i][1] + 0.2, row1[i + 1][0] - 0.2, 50.5)

    # Stage 2: two feature families feeding one preprocessing step.
    stage_label(31.0, "FEATURES")
    box(6.5, 32.4, 28.5, 5.2, "Financial features", "6 indicators per firm-year", "#F1F7F1")
    box(6.5, 25.6, 28.5, 5.2, "Textual features", "3 MD&A indicators", "#F1F7F1")
    box(40.5, 24.4, 56.0, 13.2, "Preprocessing and matrices",
        "winsorise 1/99, subindustry-year z-scores;\nfinance-only, text-only and fused matrices, one seed", "#F1F7F1")
    ax.add_patch(FancyArrowPatch((35.2, 35.0), (40.1, 33.4), arrowstyle="-|>", mutation_scale=9, linewidth=0.9, color="#555555"))
    ax.add_patch(FancyArrowPatch((35.2, 28.2), (40.1, 29.8), arrowstyle="-|>", mutation_scale=9, linewidth=0.9, color="#555555"))

    # Stage 3: ranking models, attribution, evaluation, output.
    stage_label(14.5, "MODELLING")
    row3 = [
        (6.5, 18.0, "Isolation Forest", "finance, text, fused\n500 trees, seed 42"),
        (27.5, 16.0, "Autoencoder", "16-8-16,\nreconstruction error"),
        (46.0, 15.0, "SHAP attribution", "global, group,\nlocal"),
        (63.5, 17.0, "Evaluation", "Beneish, audit opinion,\nviolation t+1"),
        (83.0, 13.5, "Outputs", "tables, figures,\nworkbooks"),
    ]
    for x, w, title, detail in row3:
        box(x, 10, w, 9, title, detail, "#FAF3EA")
    for i in range(4):
        right_arrow(row3[i][0] + row3[i][1] + 0.2, row3[i + 1][0] - 0.2, 14.5)

    # Stage-to-stage connectors.
    down_arrow(86.75, 45.4, 38.4)
    down_arrow(68.5, 23.9, 19.6)

    ax.text(50, 4.0, "Every stage writes inspectable CSV artefacts; one seed, one configuration, scripted rebuild",
            ha="center", va="center", fontsize=7.2, style="italic", color="#555555")
    ax.text(50, 1.2, "172 automated tests cover parsing, features, scoring, evaluation and reporting",
            ha="center", va="center", fontsize=7.2, style="italic", color="#555555")
    return _save(fig, "figure_4_1_pipeline.png")


def main() -> None:
    scores = pd.read_csv(TABLES / "anomaly_scores.csv")
    counts = scores.groupby("fiscal_year").size().rename("complete")
    features = pd.read_csv("data/processed/feature_table.csv")
    frame = features.groupby("fiscal_year").size().rename("frame")
    figures = pd.concat([frame, counts], axis=1).reset_index()
    figures.columns = ["fiscal_year", "frame", "complete"]

    print(figure_51(figures))
    print(figure_52(pd.read_csv(TABLES / "model_metrics.csv")))
    print(figure_53(pd.read_csv(TABLES / "topk_metrics.csv")))
    print(figure_54(pd.read_csv(TABLES / "shap_group_contributions.csv")))
    print(figure_55(pd.read_csv(TABLES / "event_ranking_metrics.csv")))
    print(figure_56(pd.read_csv(TABLES / "event_supervised_metrics.csv")))


if __name__ == "__main__":
    main()
