# -*- coding: utf-8 -*-
"""
figures.py
Author: Group12A2 DSW Team
Purpose: Experiment-phase report figures (headless-safe, Chinese labels).
Module: src/reporting

Each plot reads one of the CSV tables written by src/pipeline.run_pipeline
and saves a PNG under outputs/figures/.  matplotlib is pinned in
requirements.txt and must be installed in the project venv.

Revision History
-----------------
2026-11-06  initial version: score distribution, top-k enrichment, group
            contributions, SHAP importance, ranking overlap, batch helper.
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless rendering; must precede pyplot import

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

CHINESE_FONTS = ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "SimSun"]
SCORE_COLUMNS = ("if_finance", "if_text", "if_fused", "ae_fused")
SCORE_LABELS = {
    "if_finance": "IF-金融特征",
    "if_text": "IF-文本特征",
    "if_fused": "IF-融合特征",
    "ae_fused": "AE-融合特征",
}
GROUP_LABELS = {"financial": "金融特征组", "textual": "文本特征组"}
BASE_COLOURS = ("#4C72B0", "#55A868", "#C44E52", "#8172B3")


def _apply_style() -> None:
    plt.rcParams["font.sans-serif"] = CHINESE_FONTS
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["figure.dpi"] = 120


def _save(fig, out: Path) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    return out


def plot_score_distribution(scores: pd.DataFrame, score_col: str, out: Path) -> Path:
    """Histogram of one anomaly-score column; benchmark-flagged mass shaded."""
    _apply_style()
    values = scores[score_col].dropna().to_numpy()
    flagged = scores.loc[scores["benchmark_flag"].astype(int) == 1, score_col].dropna().to_numpy()
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.hist(values, bins=50, color=BASE_COLOURS[0], alpha=0.85, label="全部样本")
    ax.hist(flagged, bins=50, color=BASE_COLOURS[2], alpha=0.85, label="Beneish 标记 (M > -1.78)")
    ax.set_xlabel("异常得分")
    ax.set_ylabel("样本数")
    ax.set_title(f"异常得分分布 · {SCORE_LABELS.get(score_col, score_col)}")
    ax.legend()
    return _save(fig, out)


def plot_topk_enrichment(metrics: pd.DataFrame, out: Path) -> Path:
    """Grouped bars: enrichment ratio per model across k = 5% / 10% / 15%."""
    _apply_style()
    k_values = sorted(metrics["k"].unique())
    models = [m for m in SCORE_COLUMNS if m in set(metrics["model"])]
    width = 0.8 / len(models)
    x = np.arange(len(k_values))
    fig, ax = plt.subplots(figsize=(8, 4.5))
    for i, model in enumerate(models):
        heights = []
        for k in k_values:
            row = metrics[(metrics["model"] == model) & (metrics["k"] == k)]
            heights.append(float(row["enrichment"].iloc[0]) if not row.empty else np.nan)
        ax.bar(x + (i - (len(models) - 1) / 2) * width, heights, width, label=SCORE_LABELS[model])
    ax.axhline(1.0, color="grey", linestyle="--", linewidth=1, label="基准线 (=1)")
    ax.set_xticks(x)
    ax.set_xticklabels([f"{int(k * 100)}%" for k in k_values])
    ax.set_xlabel("审查比例 k")
    ax.set_ylabel("富集率（相对基准率）")
    ax.set_title("top-k 富集率：Beneish 标记在审查名单中的浓缩程度")
    ax.legend()
    return _save(fig, out)


def plot_group_contributions(contrib: pd.DataFrame, out: Path) -> Path:
    """Horizontal bars: absolute SHAP share per feature group (RQ2)."""
    _apply_style()
    data = contrib.copy()
    data["label"] = data["group"].map(lambda g: GROUP_LABELS.get(g, g))
    data = data.sort_values("abs_shap_share")
    fig, ax = plt.subplots(figsize=(8, 3.6))
    ax.barh(data["label"], data["abs_shap_share"] * 100, color=BASE_COLOURS[0])
    ax.set_xlabel("绝对 SHAP 贡献占比（%）")
    ax.set_title("特征组贡献（RQ2：金融 vs 文本）")
    for i, (share, n_features) in enumerate(zip(data["abs_shap_share"], data["n_features"])):
        ax.text(share * 100 + 0.5, i, f"{share * 100:.1f}%（{n_features} 个特征）", va="center")
    ax.set_xlim(0, 100)
    return _save(fig, out)


def plot_shap_importance(global_df: pd.DataFrame, out: Path, top_n: int = 15) -> Path:
    """Horizontal bars: mean |SHAP| per feature, top-n."""
    _apply_style()
    data = global_df.head(top_n).iloc[::-1]
    fig, ax = plt.subplots(figsize=(8, 0.45 * len(data) + 1.6))
    ax.barh(data["feature"], data["mean_abs_shap"], color=BASE_COLOURS[1])
    ax.set_xlabel("平均 |SHAP|")
    ax.set_title(f"全局特征重要性（前 {len(data)} 位，融合模型）")
    return _save(fig, out)


def plot_ranking_overlap(overlap: pd.DataFrame, out: Path) -> Path:
    """Heatmap: pairwise top-10% overlap between the four rankings (RQ3)."""
    _apply_style()
    models = [m for m in SCORE_COLUMNS if m in set(overlap["model_a"])]
    matrix = pd.pivot_table(
        overlap, index="model_a", columns="model_b", values="top10_overlap"
    ).reindex(index=models, columns=models)
    fig, ax = plt.subplots(figsize=(6.5, 5))
    image = ax.imshow(matrix.to_numpy(), cmap="Blues", vmin=0, vmax=1)
    fig.colorbar(image, ax=ax, label="top-10% 重叠率")
    ax.set_xticks(range(len(models)))
    ax.set_yticks(range(len(models)))
    ax.set_xticklabels([SCORE_LABELS[m] for m in models], rotation=45, ha="right")
    ax.set_yticklabels([SCORE_LABELS[m] for m in models])
    for i in range(len(models)):
        for j in range(len(models)):
            ax.text(j, i, f"{matrix.iloc[i, j]:.2f}", ha="center", va="center", color="black")
    ax.set_title("排序稳定性：四路排名两两 top-10% 重叠（RQ3）")
    return _save(fig, out)


def make_all_figures(tables_dir: Path, figures_dir: Path) -> list[Path]:
    """Render every figure from a pipeline tables directory; returns PNG paths."""
    tables_dir = Path(tables_dir)
    figures_dir = Path(figures_dir)
    produced: list[Path] = []

    scores = pd.read_csv(tables_dir / "anomaly_scores.csv")
    for col in SCORE_COLUMNS:
        produced.append(
            plot_score_distribution(scores, col, figures_dir / f"score_distribution_{col}.png")
        )

    produced.append(
        plot_topk_enrichment(pd.read_csv(tables_dir / "topk_metrics.csv"), figures_dir / "topk_enrichment.png")
    )
    produced.append(
        plot_group_contributions(
            pd.read_csv(tables_dir / "shap_group_contributions.csv"), figures_dir / "group_contributions.png"
        )
    )
    produced.append(
        plot_shap_importance(pd.read_csv(tables_dir / "shap_global.csv"), figures_dir / "shap_importance.png")
    )
    produced.append(
        plot_ranking_overlap(pd.read_csv(tables_dir / "ranking_overlap.csv"), figures_dir / "ranking_overlap.png")
    )
    return produced
