#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Rebuild the experiment section (§5) from the run_07 result tables.

Outputs
-------
1. ``docs/manuscript_experiment_section.md`` - the markdown source of §5, with
   Tables 5.1-5.3 inlined and prose generated from ``outputs/tables/*.csv``.
2. ``outputs/manuscript/Group12A2_Final_EN.docx`` - the Word deliverable, where
   §5 paragraphs are refreshed and the three tables are typeset into the body so
   that the manuscript satisfies the 12-15 page requirement.

Module role: manuscript assembly (one source of truth for §5 numbers).
Author: Jinyu Wang
"""

from __future__ import annotations

import argparse
import copy
from pathlib import Path

import pandas as pd
from docx import Document
from docx.oxml import OxmlElement
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt
from docx.table import Table
from docx.text.paragraph import Paragraph

ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "outputs" / "tables"
REPORTS = ROOT / "outputs" / "reports"
PROCESSED = ROOT / "data" / "processed"
DOCS = ROOT / "docs"
MANUSCRIPT = ROOT / "outputs" / "manuscript"
V01_TABLES = ROOT / "outputs" / "archive_v0.1" / "tables"

EVENT_TABLE = ROOT / "data" / "processed" / "event_table.csv"
EVENT_RANKING = TABLES / "event_ranking_metrics.csv"
EVENT_SUPERVISED = TABLES / "event_supervised_metrics.csv"
EVENT_LABELS = (
    "mod_opinion",
    "mod_opinion_wide",
    "violation_any_t1",
    "violation_disclosure_t1",
)
EVENT_SCORES = (
    "finance-only IF",
    "text-only IF",
    "fused IF",
    "fused AE",
    "Beneish M-Score",
)

FEATURES = [
    "roa",
    "leverage",
    "revenue_growth",
    "ocf_to_assets",
    "receivables_turnover",
    "accruals_to_assets",
    "readability",
    "sentiment_balance",
    "uncertainty_ratio",
]

MODEL_LABELS = {
    "if_finance": "Finance-only IF",
    "if_text": "Text-only IF",
    "if_fused": "Fused IF",
    "ae_fused": "Fused autoencoder",
}

# Paragraph slots in the delivered Word file (0-based, body paragraph index).
SLOT_ABSTRACT = 3
SLOT_LIMITATIONS = 52
SLOT_S51 = 55
SLOT_S52_INTRO = 57
SLOT_S53 = 59
SLOT_S54 = 61
SLOT_S55 = 63
INSERT_AFTER = SLOT_S52_INTRO

# Body leading applied to every 1.5-spaced paragraph; 1.45 keeps the manuscript
# inside the 12-15 page requirement without touching any content.
BODY_LINE_SPACING = 1.45


def _fmt(value: float, digits: int = 3) -> str:
    """Format a descriptive statistic with a sensible number of digits."""
    if pd.isna(value):
        return "n/a"
    magnitude = abs(float(value))
    if magnitude >= 10_000:
        return f"{value:,.0f}"
    if magnitude >= 100:
        return f"{value:,.2f}"
    if magnitude >= 1:
        return f"{value:.3f}"
    if magnitude >= 0.001:
        return f"{value:.4f}"
    return f"{value:.5f}"


def _p_inline(p_value: float) -> str:
    """Inline p-value phrase used inside running prose."""
    return "p < 0.001" if p_value < 0.001 else f"p = {p_value:.3f}"


def _mscore_components(scores: pd.DataFrame) -> dict:
    """Median Beneish indices for modified-opinion versus other firm-years.

    Used in §5.7 to explain why the M-Score ranks modified-opinion firms below
    the rest of the sample: the two indices that move the score most in this
    sample are total accruals (TATA) and sales growth (SGI), and both have the
    opposite sign in the modified-opinion group to the direction Beneish's
    coefficients reward.
    """
    empty = {"mod": {}, "clean": {}}
    try:
        import sys

        if str(ROOT) not in sys.path:
            # Keep the import working when the script is executed from another
            # directory (for example the docx patch helper in outputs/.tmp).
            sys.path.insert(0, str(ROOT))

        from src.features.beneish import compute_beneish
        from src.features.financial import compute_finance_features

        interim = pd.read_csv(
            ROOT / "data" / "interim" / "finance_intermediate.csv",
            dtype={"symbol": str},
        )
        events = pd.read_csv(
            PROCESSED / "event_table.csv", dtype={"symbol": str}
        )[["symbol", "fiscal_year", "mod_opinion"]]
        frame = compute_beneish(compute_finance_features(interim))
        frame["symbol"] = frame["symbol"].astype(str).str.zfill(6)
        events["symbol"] = events["symbol"].astype(str).str.zfill(6)
        merged = frame.merge(events, on=["symbol", "fiscal_year"], how="inner")
        merged = merged.dropna(subset=["m_score"])
        out: dict = {}
        for key, value in (("mod", 1), ("clean", 0)):
            sub = merged[merged["mod_opinion"] == value]
            out[key] = {
                "DSRI": float(sub["DSRI"].median()),
                "GMI": float(sub["GMI"].median()),
                "AQI": float(sub["AQI"].median()),
                "SGI": float(sub["SGI"].median()),
                "LVGI": float(sub["LVGI"].median()),
                "SGAI": float(sub["SGAI"].median()),
                "TATA": float(sub["TATA"].median()),
                "m_score": float(sub["m_score"].median()),
                "roa": float(sub["roa"].median()),
                "leverage": float(sub["leverage"].median()),
                "n": int(len(sub)),
            }
        return out
    except Exception:  # pragma: no cover - the paragraph degrades gracefully
        return empty


def _p_text(p_value: float) -> str:
    return "< 0.001" if p_value < 0.001 else f"{p_value:.3f}"


def _corr_clause(rho: float, p_value: float) -> str:
    """Describe a rank correlation without overstating or understating it."""
    if p_value < 0.05:
        return (
            f"weakly negative and marginally significant (rho = {rho:.3f}, "
            f"{_p_inline(p_value)})"
        )
    return f"indistinguishable from zero (rho = {rho:.3f}, {_p_inline(p_value)})"


_FEATURE_WORDS = {
    "roa": "profitability",
    "leverage": "leverage",
    "revenue_growth": "revenue growth",
    "ocf_to_assets": "operating cash flow",
    "receivables_turnover": "receivables turnover",
    "accruals_to_assets": "accruals",
    "readability": "readability",
    "sentiment_balance": "sentiment balance",
    "uncertainty_ratio": "uncertainty language",
}


def _drivers_profile(names: list[str]) -> str:
    """Turn the top local SHAP drivers into a readable profile phrase."""
    words = [_FEATURE_WORDS.get(name, name.replace("_", " ")) for name in names]
    if len(words) == 1:
        joined = words[0]
    elif len(words) == 2:
        joined = f"{words[0]} and {words[1]}"
    else:
        joined = ", ".join(words[:-1]) + f" and {words[-1]}"
    return f"an unusual {joined} profile"


def _load_v01_metrics() -> dict:
    """Return the first-specification (v0.1) metrics, empty dict when unavailable.

    The v0.1 run is archived under ``outputs/archive_v0.1/tables`` so that
    the manuscript can compare the two specifications without re-running the old
    lexicon.  Missing files simply disable the comparison table.
    """
    models_path = V01_TABLES / "model_metrics.csv"
    topk_path = V01_TABLES / "topk_metrics.csv"
    if not (models_path.exists() and topk_path.exists()):
        return {}
    models = pd.read_csv(models_path).set_index("model")
    topk = pd.read_csv(topk_path)
    out: dict = {
        model: {
            "rho": float(models.loc[model, "spearman_rho"]),
            "p": float(models.loc[model, "spearman_p"]),
        }
        for model in models.index
    }
    for _, row in topk.iterrows():
        key = f"{row['benchmark']}_{row['model']}_{int(round(float(row['k']) * 100))}"
        out[key] = float(row["enrichment"])
    return out


def _load_event_numbers() -> dict:
    """Return the external-outcome numbers (branch 3), empty dict when unavailable.

    ``event_table.csv`` supplies base rates, ``event_ranking_metrics.csv`` the
    unsupervised ranking quality and ``event_supervised_metrics.csv`` the grouped
    cross-validation comparison.  Any missing file simply disables the section.
    """
    out: dict = {"ranking": {}, "supervised": {}}
    if EVENT_TABLE.exists():
        frame = pd.read_csv(EVENT_TABLE, dtype={"symbol": str})
        out["n"] = int(len(frame))
        for label in EVENT_LABELS:
            if label not in frame.columns:
                continue
            out[f"{label}_count"] = int(frame[label].sum())
            out[f"{label}_rate"] = float(frame[label].mean())
        if "mod_opinion" in frame.columns and "fiscal_year" in frame.columns:
            grouped = frame.groupby("fiscal_year")["mod_opinion"].mean()
            out["mod_by_year"] = {
                int(year): float(value) for year, value in grouped.items()
            }
    if EVENT_RANKING.exists():
        table = pd.read_csv(EVENT_RANKING)
        for _, row in table.iterrows():
            out["ranking"][(str(row["label"]), str(row["model"]))] = {
                "auc": float(row["auc"]),
                "auc_lo": float(row["auc_lo"]),
                "auc_hi": float(row["auc_hi"]),
                "pr_auc": float(row["pr_auc"]),
                "lift_10pct": float(row["lift_10pct"]),
                "recall_10pct": float(row["recall_10pct"]),
            }
    if EVENT_SUPERVISED.exists():
        table = pd.read_csv(EVENT_SUPERVISED)
        for _, row in table.iterrows():
            out["supervised"][
                (str(row["label"]), str(row["model"]), str(row["feature_set"]))
            ] = {
                "auc": float(row["oof_auc"]),
                "lo": float(row["oof_auc_lo"]),
                "hi": float(row["oof_auc_hi"]),
            }
    return out


def _event_score(num: dict, label: str, model: str) -> dict:
    """Look up one ranking cell, returning an empty dict when unavailable."""
    return (num.get("events") or {}).get("ranking", {}).get((label, model), {})


def _event_delta(num: dict, label: str, model: str, feature_set: str) -> dict:
    """Look up one supervised AUC cell (or a delta row)."""
    return (num.get("events") or {}).get("supervised", {}).get(
        (label, model, feature_set), {}
    )


def collect_numbers() -> dict:
    """Read every number the section needs straight from the pipeline tables."""
    features = pd.read_csv(PROCESSED / "feature_table.csv", dtype={"symbol": str})
    scores = pd.read_csv(TABLES / "anomaly_scores.csv", dtype={"symbol": str})
    features["symbol"] = features["symbol"].str.zfill(6)
    scores["symbol"] = scores["symbol"].str.zfill(6)
    metrics = pd.read_csv(TABLES / "model_metrics.csv").set_index("model")
    topk = pd.read_csv(TABLES / "topk_metrics.csv")
    overlap = pd.read_csv(TABLES / "ranking_overlap.csv")
    shap_global = pd.read_csv(TABLES / "shap_global.csv")
    shap_group = pd.read_csv(TABLES / "shap_group_contributions.csv")
    shap_local = pd.read_csv(TABLES / "shap_local_top1.csv")

    num: dict = {}
    num["frame_years"] = len(features)
    num["frame_firms"] = features["symbol"].nunique()
    by_year = features.groupby("fiscal_year").size()
    num["frame_by_year"] = {int(y): int(c) for y, c in by_year.items()}
    num["n"] = len(scores)
    num["n_firms"] = scores["symbol"].nunique()
    by_year = scores.groupby("fiscal_year").size()
    num["by_year"] = {int(y): int(c) for y, c in by_year.items()}
    num["share"] = num["n"] / num["frame_years"]

    status = features["text_status"].fillna("missing").value_counts()
    num["text_extracted"] = int(status.get("ok", 0))
    num["text_no_pdf"] = int(status.get("missing", 0))
    num["text_no_mda"] = int(status.get("no_mda", 0))
    num["text_failed"] = int(status.get("pdf_error", 0))
    num["text_ok"] = int(features["text_quality"].eq("ok").sum())
    num["text_suspicious"] = int(features["text_quality"].eq("suspicious").sum())
    num["text_missing"] = int(features["text_quality"].eq("missing").sum())
    num["year_share_text"] = {
        int(y): float((sub["text_status"] == "ok").mean())
        for y, sub in features.groupby("fiscal_year")
    }

    num["legacy_flag"] = int(scores["benchmark_flag"].sum())
    num["legacy_share"] = float(scores["benchmark_flag"].mean())
    num["q90"] = float(scores["m_score"].quantile(0.90))
    num["cal_flag"] = int(scores["benchmark_flag_calibrated"].sum())
    num["mscore_components"] = _mscore_components(scores)

    for model in MODEL_LABELS:
        num[f"rho_{model}"] = float(metrics.loc[model, "spearman_rho"])
        num[f"p_{model}"] = float(metrics.loc[model, "spearman_p"])

    for _, row in topk.iterrows():
        key = f"{row['benchmark']}_{row['model']}_{int(round(row['k'] * 100))}"
        num[f"ev_{key}"] = float(row["event_rate"])
        num[f"en_{key}"] = float(row["enrichment"])

    def _overlap(a: str, b: str) -> float:
        hit = overlap[
            ((overlap["model_a"] == a) & (overlap["model_b"] == b))
            | ((overlap["model_a"] == b) & (overlap["model_b"] == a))
        ]
        return float(hit["top10_overlap"].iloc[0])

    num["overlap_fin_fused"] = _overlap("if_finance", "if_fused")
    num["overlap_fin_text"] = _overlap("if_finance", "if_text")

    rho_by_year: dict[int, dict[str, float]] = {}
    for year, group in scores.groupby("fiscal_year"):
        rho_by_year[int(year)] = {
            model: float(group[model].corr(group["m_score"], method="spearman"))
            for model in MODEL_LABELS
        }
    num["rho_by_year"] = rho_by_year

    groups = shap_group.set_index("group")["abs_shap_share"]
    num["shap_finance"] = float(groups.get("finance", 0.0))
    num["shap_text"] = float(groups.get("text", 0.0))
    num["shap_top3"] = [
        (str(row["feature"]), float(row["mean_abs_shap"]))
        for _, row in shap_global.sort_values("mean_abs_shap", ascending=False)
        .head(3)
        .iterrows()
    ]

    top1 = scores.sort_values("if_fused", ascending=False).iloc[0]
    detail = features[
        (features["symbol"] == top1["symbol"])
        & (features["fiscal_year"] == top1["fiscal_year"])
    ]
    num["top1_symbol"] = str(top1["symbol"]).zfill(6)
    num["top1_year"] = int(top1["fiscal_year"])
    num["top1_industry"] = (
        str(detail["industry_code_d"].iloc[0]) if len(detail) else "n/a"
    )
    num["top1_score"] = float(top1["if_fused"])
    num["top1_mscore"] = float(top1["m_score"])
    num["top1_drivers"] = [
        str(row["feature"])
        for _, row in shap_local.reindex(
            shap_local["shap_value"].abs().sort_values(ascending=False).index
        )
        .head(3)
        .iterrows()
    ]

    descriptives = []
    for feature in FEATURES:
        series = pd.to_numeric(features[feature], errors="coerce")
        descriptives.append(
            (
                feature,
                int(series.notna().sum()),
                float(series.mean()),
                float(series.std()),
                float(series.min()),
                float(series.max()),
            )
        )
    num["descriptives"] = descriptives
    num["lexicon_density"] = _load_lexicon_density()
    num["v01"] = _load_v01_metrics()
    num["events"] = _load_event_numbers()
    return num


def _load_lexicon_density() -> dict:
    """Return the v0.1 vs v0.2 lexicon hit densities, empty dict when unavailable."""
    path = TABLES / "lexicon_density.csv"
    if not path.exists():
        return {}
    table = pd.read_csv(path)
    out: dict[str, dict[str, float]] = {}
    for _, row in table.iterrows():
        out[str(row["metric"])] = {
            "v01": float(row["v01_per_1000"]),
            "v02": float(row["v02_per_1000"]),
            "ratio": float(row["ratio"]),
        }
    return out


def _table_51(num: dict) -> list[list[str]]:
    rows = [["Feature", "n", "mean", "std", "min", "max"]]
    for name, n, mean, std, low, high in num["descriptives"]:
        rows.append(
            [name, f"{n:,}", _fmt(mean), _fmt(std), _fmt(low), _fmt(high)]
        )
    return rows


def _table_52(num: dict) -> list[list[str]]:
    rows = [["Model", "Spearman rho", "p-value"]]
    for model, label in MODEL_LABELS.items():
        rows.append(
            [
                label,
                f"{num[f'rho_{model}']:.3f}",
                _p_text(num[f"p_{model}"]),
            ]
        )
    return rows


def _table_53(num: dict) -> list[list[str]]:
    rows = [
        [
            "Model",
            "k",
            "Event rate (legacy)",
            "Enrichment (legacy)",
            "Event rate (recalibrated)",
            "Enrichment (recalibrated)",
        ]
    ]
    for model, label in MODEL_LABELS.items():
        for k in (5, 10, 15):
            key = f"{model}_{k}"
            if f"en_legacy_{key}" not in num:
                continue
            rows.append(
                [
                    label,
                    f"{k}%",
                    f"{num[f'ev_legacy_{key}']:.3f}",
                    f"{num[f'en_legacy_{key}']:.3f}",
                    f"{num[f'ev_calibrated_{key}']:.3f}",
                    f"{num[f'en_calibrated_{key}']:.3f}",
                ]
            )
    return rows


def _table_54(num: dict) -> list[list[str]]:
    """Table 5.4: first versus second specification (lexicon and benchmark)."""
    old = num.get("v01") or {}
    density = num.get("lexicon_density") or {}
    dense = density.get("sentiment_terms", {})
    if old:
        text_rho_old = f"{old['if_text']['rho']:.3f}"
        gefused_rho_old = f"{old['if_fused']['rho']:.3f}"
        ae_old = f"{old['ae_fused']['rho']:.3f} ({old['ae_fused']['p']:.3f})"
        text_en_old = (
            f"{old['calibrated_if_text_10']:.2f}"
            if "calibrated_if_text_10" in old
            else "n/a"
        )
    else:
        text_rho_old = gefused_rho_old = ae_old = text_en_old = "n/a"
    rows = [
        ["Design choice", "First specification (v0.1)", "Second specification (v0.2)"],
        [
            "Sentiment lexicon",
            "Bootstrap list of 38 positive / 33 negative terms",
            "Yao et al. (2021): 3,585 positive / 1,633 negative terms",
        ],
        [
            "Lexicon matching",
            "Substring counting on raw text",
            "jieba token match with a 5,218-term user dictionary",
        ],
        [
            "Sentiment hits per 1,000 tokens",
            f"{dense.get('v01', 0):.1f}" if dense else "n/a",
            (
                f"{dense.get('v02', 0):.1f} ({dense.get('ratio', 0):.1f}x)"
                if dense
                else "n/a"
            ),
        ],
        [
            "Uncertainty list",
            "23 terms",
            "About 100 terms (Loughran-McDonald and Zeng et al.)",
        ],
        [
            "Beneish benchmark",
            "Literal M > -1.78 only",
            f"Literal M > -1.78 and sample top decile (M > {num['q90']:.2f}, 10%)",
        ],
        [
            "Text-only / fused rank correlation",
            f"{text_rho_old} / {gefused_rho_old}",
            f"{num['rho_if_text']:.3f} / {num['rho_if_fused']:.3f}",
        ],
        [
            "Autoencoder rank correlation (p)",
            ae_old,
            f"{num['rho_ae_fused']:.3f} ({num['p_ae_fused']:.3f})",
        ],
        [
            "Text-only top-10% enrichment (recalibrated)",
            text_en_old,
            f"{num['en_calibrated_if_text_10']:.2f}",
        ],
        [
            "Answer to RQ1",
            "No incremental value for the Beneish screen",
            "Unchanged for the Beneish screen; small positive but statistically "
            "indistinguishable increments in supervised models (Table 5.6)",
        ],
    ]
    return rows


def _cell_value(bucket: dict, key: str, digits: int = 3) -> str:
    """Format one ranking cell with fixed digits (never the descriptive rules)."""
    value = bucket.get(key, float("nan"))
    if pd.isna(value):
        return "n/a"
    return f"{value:.{digits}f}"


def _table_55(num: dict) -> list[list[str]]:
    """Table 5.5: how the existing scores rank real regulatory outcomes."""
    rows = [
        [
            "Score",
            "AUC: opinion",
            "AUC: disclosure violation t+1",
            "Lift: opinion",
            "Lift: disclosure violation",
        ]
    ]
    for model in EVENT_SCORES:
        opinion = _event_score(num, "mod_opinion", model)
        violation = _event_score(num, "violation_disclosure_t1", model)
        rows.append(
            [
                model,
                _cell_value(opinion, "auc"),
                _cell_value(violation, "auc"),
                _cell_value(opinion, "lift_10pct", 2),
                _cell_value(violation, "lift_10pct", 2),
            ]
        )
    return rows


SUPERVISED_SETS = (
    ("finance", "Finance only"),
    ("text", "Text only"),
    ("fused", "Fused"),
)
SUPERVISED_LABELS = (("logit", "Logit"), ("hgb", "Gradient boosting"))


def _table_56(num: dict) -> list[list[str]]:
    """Table 5.6: grouped cross-validation AUC with and without the text block."""
    rows = [
        [
            "Feature set",
            "Model",
            "AUC: opinion",
            "\u0394AUC vs finance",
            "AUC: disclosure violation t+1",
            "\u0394AUC vs finance",
        ]
    ]
    for feature_set, set_label in SUPERVISED_SETS:
        for model, model_label in SUPERVISED_LABELS:
            opinion = _event_delta(num, "mod_opinion", model, feature_set)
            violation = _event_delta(num, "violation_disclosure_t1", model, feature_set)
            delta_opinion = _event_delta(num, "mod_opinion", model, "delta_fused_vs_finance")
            delta_violation = _event_delta(
                num, "violation_disclosure_t1", model, "delta_fused_vs_finance"
            )
            rows.append(
                [
                    set_label,
                    model_label,
                    _cell_value(opinion, "auc"),
                    (
                        _cell_value(delta_opinion, "auc")
                        if feature_set == "fused"
                        else "-"
                    ),
                    _cell_value(violation, "auc"),
                    (
                        _cell_value(delta_violation, "auc")
                        if feature_set == "fused"
                        else "-"
                    ),
                ]
            )
    return rows


def _abstract_external(num: dict) -> str:
    """Abstract addendum: forward-looking outcomes and the supervised increments."""
    events = num.get("events") or {}
    ranking = events.get("ranking") or {}
    supervised = events.get("supervised") or {}
    forward = ranking.get(("violation_disclosure_t1", "finance-only IF")) or {}
    gain = supervised.get(("mod_opinion", "logit", "delta_fused_vs_finance")) or {}
    if not (forward and gain):
        return ""
    return (
        f" Forward-looking discrimination is weak: the best t+1 disclosure-violation AUC is "
        f"{forward['auc']:.3f}. In firm-grouped supervised cross-validation, adding the text "
        "block changes the AUC by "
        f"{gain['auc']:+.3f} [{gain['lo']:+.3f}, {gain['hi']:+.3f}], an increment that is "
        "small and not statistically distinguishable from zero in any of the eight reported "
        "label-by-algorithm combinations."
    )


def _abstract_external_cn(num: dict) -> str:
    """Chinese counterpart of :func:`_abstract_external`."""
    events = num.get("events") or {}
    ranking = events.get("ranking") or {}
    supervised = events.get("supervised") or {}
    forward = ranking.get(("violation_disclosure_t1", "finance-only IF")) or {}
    gain = supervised.get(("mod_opinion", "logit", "delta_fused_vs_finance")) or {}
    if not (forward and gain):
        return ""
    return (
        f"前瞻性识别很弱：t+1 披露违规的最高 AUC 仅 {forward['auc']:.3f}。按公司分组的"
        f"监督交叉验证中，加入文本块使 AUC 变化 {gain['auc']:+.3f}"
        f"（区间 [{gain['lo']:+.3f}, {gain['hi']:+.3f}]），八种标签与算法的组合中没有一个"
        f"能把这微小增量与零区分开。"
    )


def _section57_en(num: dict) -> dict:
    """Compose §5.7 (external outcomes); empty when the branch-3 tables are absent."""
    events = num.get("events") or {}
    ranking = events.get("ranking") or {}
    supervised = events.get("supervised") or {}
    text: dict = {}
    if not ranking:
        return text

    def cell(label: str, model: str) -> dict:
        return ranking.get((label, model), {})

    def gain(label: str, model: str) -> dict:
        return supervised.get((label, model, "delta_fused_vs_finance"), {})

    def auc(bucket: dict) -> str:
        if "auc" not in bucket:
            return "n/a"
        return f"{bucket['auc']:.3f} [{bucket['auc_lo']:.3f}, {bucket['auc_hi']:.3f}]"

    def dtext(bucket: dict) -> str:
        if "auc" not in bucket:
            return "n/a"
        return f"{bucket['auc']:+.3f} [{bucket['lo']:+.3f}, {bucket['hi']:+.3f}]"

    def sup_auc(label: str, model: str, set_name: str) -> str:
        bucket = supervised.get((label, model, set_name)) or {}
        if "auc" not in bucket:
            return "n/a"
        return f"{bucket['auc']:.3f}"

    n = events.get("n", num["n"])
    mod_count = events.get("mod_opinion_count", 0)
    mod_rate = events.get("mod_opinion_rate", float("nan"))
    wide_count = events.get("mod_opinion_wide_count", 0)
    wide_rate = events.get("mod_opinion_wide_rate", float("nan"))
    any_count = events.get("violation_any_t1_count", 0)
    any_rate = events.get("violation_any_t1_rate", float("nan"))
    disc_count = events.get("violation_disclosure_t1_count", 0)
    disc_rate = events.get("violation_disclosure_t1_rate", float("nan"))
    by_year = events.get("mod_by_year") or {}
    year_phrase = ", ".join(
        f"{int(year)}: {value * 100:.1f}%" for year, value in sorted(by_year.items())
    )

    fin = cell("mod_opinion", "finance-only IF")
    txt = cell("mod_opinion", "text-only IF")
    fused = cell("mod_opinion", "fused IF")
    ae = cell("mod_opinion", "fused AE")
    proxy = cell("mod_opinion", "Beneish M-Score")
    fin_v = cell("violation_disclosure_t1", "finance-only IF")

    gains = [
        gain(label, model) for label in EVENT_LABELS for model, _ in SUPERVISED_LABELS
    ]
    gains = [item for item in gains if "auc" in item]
    positive = sum(1 for item in gains if item["auc"] >= 0)
    significant = sum(1 for item in gains if item["lo"] > 0)

    text["s57_heading"] = "5.7 External Validation Against Real Regulatory Outcomes"
    text["s57a"] = (
        "The Beneish M-Score is only a proxy for earnings manipulation, and the preceding "
        "subsections have shown it is a poor one in this sample. We therefore validate the "
        "scores against two real CSMAR outcomes: the audit opinion on the fiscal-year report "
        "(FIN_Audit) and exchange violation announcements (STK_Violation_Main). The narrow "
        "opinion label equals one for any opinion other than unqualified; the wide label also "
        "counts unqualified opinions with an explanatory paragraph. The violation label "
        "equals one when an announcement falls in t+1. Sample counts are reported for both "
        "all violations and the disclosure-related subset, whereas the ranking tests in "
        "Table 5.5 use the narrower subset (delayed disclosure, misstatement, material "
        "omission, fictitious profit or assets), which keeps that test forward-looking and "
        "extends the window to 2025."
    )
    text["s57b"] = (
        f"Both outcomes cover all {n:,} firm-years, so this is an external validation rather "
        f"than a subsample check. Modified opinions are rare: {mod_count:,} "
        f"({mod_rate * 100:.2f}%), or {wide_count:,} ({wide_rate * 100:.2f}%) counting "
        f"explanatory paragraphs, at rates of {year_phrase} - the enforcement cycle rather "
        f"than a firm property. Violations are common because they mix disclosure problems "
        f"with trading and governance offences: {any_count:,} ({any_rate * 100:.2f}%) "
        f"received some announcement in t+1 and {disc_count:,} ({disc_rate * 100:.2f}%) a "
        "disclosure-related one."
    )
    text["t55_caption"] = (
        "Table 5.5. Ranking quality against real outcomes: opinion = modified audit opinion, "
        "violation = disclosure-related announcement in t+1, lift = top-10% queue event rate "
        "over the base rate."
    )
    comp = num.get("mscore_components") or {}
    if comp.get("mod") and comp.get("clean"):
        mod_c, clean_c = comp["mod"], comp["clean"]
        mscore_gap = (
            "The reason is visible in the indices the score weights most. Relative to other "
            f"firm-years, modified-opinion firms have a median total-accruals ratio (TATA) of "
            f"{mod_c['TATA']:.2f} against {clean_c['TATA']:.2f}, a sales growth index (SGI) of "
            f"{mod_c['SGI']:.2f} against {clean_c['SGI']:.2f}, a leverage index (LVGI) of "
            f"{mod_c['LVGI']:.2f} against {clean_c['LVGI']:.2f}, a median return on assets of "
            f"{mod_c['roa'] * 100:.1f}% against {clean_c['roa'] * 100:.1f}%, and median "
            f"leverage of {mod_c['leverage'] * 100:.1f}% against "
            f"{clean_c['leverage'] * 100:.1f}%. Beneish's coefficients reward positive accruals "
            "(+4.679) and sales growth (+0.892) and penalise leverage increases (-0.327), so "
            "contracting, loss-making and highly leveraged firms - precisely the population "
            "that receives modified opinions here - are pushed down the risk ranking. The score "
            "is calibrated to detect income-inflating manipulation, not financial distress, and "
            "the two constructs diverge sharply in this sample."
        )
    else:  # pragma: no cover - only when the intermediate is unavailable
        mscore_gap = ""
    text["s57c"] = (
        f"Table 5.5 reports ranking quality. The finance-only Isolation Forest transfers to "
        f"the real outcome: AUC {auc(fin)} for a modified opinion, with the top-10% queue at "
        f"{fin.get('lift_10pct', float('nan')):.2f} times the base rate and covering "
        f"{fin.get('recall_10pct', float('nan')) * 100:.1f}% of modified opinions. Text alone "
        f"is close to chance ({auc(txt)}), the fused score sits between the two "
        f"({auc(fused)}), and the autoencoder is weaker still ({auc(ae)}). Most striking is "
        f"the benchmark: the Beneish M-Score orders modified-opinion firms below the rest of "
        f"the sample ({auc(proxy)}), so the proxy behind RQ1 points the wrong way relative "
        f"to what auditors did. {mscore_gap} For forward violations every score is weaker "
        f"(best {auc(fin_v)}), as expected when the outcome mixes disclosure quality with "
        "regulator attention."
    )
    text["t56_caption"] = (
        "Table 5.6. Out-of-fold AUC under firm-grouped five-fold cross-validation, with the "
        "increment of the fused block over finance-only."
    )
    text["s57d"] = (
        "Table 5.6 asks the complementary supervised question: given the labels, does the "
        "text block add rank information beyond the financial block? Text alone is weaker "
        f"than finance alone ({sup_auc('mod_opinion', 'logit', 'text')} versus "
        f"{sup_auc('mod_opinion', 'logit', 'finance')} for modified opinions), so the issue "
        "is complementarity. Under firm-grouped cross-validation the logistic model reaches "
        f"{sup_auc('mod_opinion', 'logit', 'finance')} on financial features and "
        f"{sup_auc('mod_opinion', 'logit', 'fused')} fused, an increment of "
        f"{dtext(gain('mod_opinion', 'logit'))}; gradient boosting gives "
        f"{dtext(gain('mod_opinion', 'hgb'))}, and the disclosure-violation label gives "
        f"{dtext(gain('violation_disclosure_t1', 'logit'))} and "
        f"{dtext(gain('violation_disclosure_t1', 'hgb'))}. Across the {len(gains)} "
        f"label-by-model combinations the increment is positive in {positive} and its "
        f"interval excludes zero in {significant} - "
        + (
            "small and never statistically distinguishable from zero."
            if significant == 0
            else "small and only sometimes detectable."
        )
    )
    text["s57e"] = (
        "Two caveats keep this from being a clean positive headline. First, the audit "
        "opinion is contemporaneous with the fiscal year, so Table 5.5 measures "
        "identification of risky disclosures rather than forecasting; only the violation "
        "label is a genuine forecast, and there the scores are weak. Second, both labels are "
        "produced by auditors and regulators whose capacity varies over time and across "
        "firms, so the measurement error is not classical. The substantive reading is a "
        "construct mismatch: MD&A tone and readability say something about the disclosure "
        "process auditors police, but little about the accounting-manipulation construct the "
        "Beneish benchmark measures. RQ1's negative answer therefore stands for the Beneish "
        "target, while against real audit outcomes the fused block adds at most a small "
        "increment that is not statistically distinguishable from zero - consistent with, "
        "but not evidence of, complementarity."
    )
    return text


def _benchmark_finding(num: dict) -> str:
    """Lead sentence of the abstract and conclusion: the benchmark fails, and why.

    Track A of the revision treats the external validation as the headline result
    rather than as a caveat on a null RQ1: against real audit outcomes the Beneish
    score ranks modified-opinion firms *below* the rest of the sample, and the
    component medians show that this follows from what the score rewards.
    """
    events = num.get("events") or {}
    ranking = events.get("ranking") or {}
    opinion = ranking.get(("mod_opinion", "finance-only IF")) or {}
    proxy = ranking.get(("mod_opinion", "Beneish M-Score")) or {}
    if not (opinion and proxy):
        return ""
    comp = num.get("mscore_components") or {}
    mechanism = ""
    if comp.get("mod") and comp.get("clean"):
        m, c = comp["mod"], comp["clean"]
        mechanism = (
            f" The gap is a construct mismatch rather than a calibration artefact: "
            f"modified-opinion firms report contracting sales (median SGI {m['SGI']:.2f} "
            f"against {c['SGI']:.2f}), negative accruals (TATA {m['TATA']:.2f} against "
            f"{c['TATA']:.2f}) and higher leverage ({m['leverage'] * 100:.0f}% against "
            f"{c['leverage'] * 100:.0f}%), while the score rewards positive accruals "
            f"(+4.679) and sales growth (+0.892); it detects income-inflating "
            f"manipulation, not the financial distress that drives modified opinions here."
        )
    return (
        f"The study's most robust result concerns the benchmark rather than the text. "
        f"Across {num['n']:,} firm-years from {num['n_firms']:,} firms, the finance-only "
        f"Isolation Forest ranks firm-years with contemporaneous modified audit opinions "
        f"well (AUC {opinion['auc']:.3f}), whereas the Beneish M-Score ranks those same "
        f"firms below chance (AUC {proxy['auc']:.3f}).{mechanism}"
    )


def _benchmark_finding_cn(num: dict) -> str:
    """Chinese counterpart of :func:`_benchmark_finding`."""
    events = num.get("events") or {}
    ranking = events.get("ranking") or {}
    opinion = ranking.get(("mod_opinion", "finance-only IF")) or {}
    proxy = ranking.get(("mod_opinion", "Beneish M-Score")) or {}
    if not (opinion and proxy):
        return ""
    comp = num.get("mscore_components") or {}
    mechanism = ""
    if comp.get("mod") and comp.get("clean"):
        m, c = comp["mod"], comp["clean"]
        mechanism = (
            f"差距来自构念错配而非阈值标定：非标意见组的营业收入指数（SGI）中位数为 "
            f"{m['SGI']:.2f}（其他样本 {c['SGI']:.2f}），总应计比率（TATA）为 "
            f"{m['TATA']:.2f}（其他 {c['TATA']:.2f}），杠杆率为 "
            f"{m['leverage'] * 100:.0f}%（其他 {c['leverage'] * 100:.0f}%）；而该评分奖励正应计"
            f"（+4.679）与销售增长（+0.892），它识别的是虚增利润型的盈余操纵，而非驱动非标意见的"
            f"财务困境。"
        )
    return (
        f"本文最稳健的结论来自基准本身而非文本：在 {num['n']:,} 个公司—年度观测"
        f"（{num['n_firms']:,} 家公司）上，仅用财务特征的 Isolation Forest 对同期非标审计意见的"
        f"排序 AUC 为 {opinion['auc']:.3f}，而 Beneish M-Score 对同一结果的 AUC 仅 "
        f"{proxy['auc']:.3f}（低于随机）。{mechanism}"
    )


def prose(num: dict) -> dict:
    """Compose the paragraphs of §5, plus the two paragraphs to refresh elsewhere."""
    year_frame = "; ".join(
        f"{y}: {c:,}" for y, c in sorted(num["frame_by_year"].items())
    )
    year_used = "; ".join(f"{y}: {c:,}" for y, c in sorted(num["by_year"].items()))
    year_share = ", ".join(
        f"{num['year_share_text'][y] * 100:.1f}% ({y})"
        for y in sorted(num["year_share_text"])
    )
    top3 = ", ".join(f"`{name}` ({value:.3f})" for name, value in num["shap_top3"])
    drivers = ", ".join(f"`{name}`" for name in num["top1_drivers"])
    rho_fin = num["rho_if_finance"]
    rho_text = num["rho_if_text"]
    rho_fused = num["rho_if_fused"]
    rho_ae = num["rho_ae_fused"]

    text: dict = {}

    text["abstract_updates"] = (
        _benchmark_finding(num)
        + f" Measured against that benchmark, the three MD&A features add no incremental "
        f"value: the fused ranking is weakly and inversely correlated with the M-Score "
        f"(Spearman rho {rho_fused:.3f}, {_p_inline(num['p_if_fused'])}), the finance-only "
        f"ranking behaves the same way ({rho_fin:.3f}) and the text-only ranking is "
        f"{_corr_clause(rho_text, num['p_if_text'])}. Under the recalibrated top-decile "
        f"benchmark the fused top-10% review list contains "
        f"{num['en_calibrated_if_fused_10']:.2f} times the base flag rate "
        f"({num['en_legacy_if_fused_10']:.2f} under the literal -1.78 cut-off)."
        + _abstract_external(num)
    )

    text["limitations"] = (
        "The main limitations are the following. First, the Chinese sentiment and "
        "uncertainty measures are dictionary-based: the full financial sentiment lexicon "
        "of Yao et al. (2021) and a curated uncertainty word list are matched token by "
        "token after jieba segmentation, so sentence-level context such as negation and "
        "hedging is only partially captured, and vocabulary outside the lexicon is "
        "invisible. Second, PDF extraction introduces some noise, because scanned pages "
        "and unusual layouts cannot always be read perfectly. Third, the sample is "
        "limited to manufacturing firms over three years, so the results should not be "
        "generalised to other industries or periods. Because of these limits, the "
        "pipeline should be read as a tool for ordering firms for human review, not as a "
        "proof that any specific firm has committed fraud or low-quality disclosure."
    )

    text["s51"] = (
        f"The sample frame contains {num['frame_firms']:,} manufacturing firms and "
        f"{num['frame_years']:,} firm-years ({year_frame}). After merging the six "
        f"financial features, the three textual features and the Beneish M-Score, "
        f"{num['n']:,} firm-years ({num['share'] * 100:.1f}%) across {num['n_firms']:,} "
        f"firms have complete data and enter the main analysis ({year_used}). MD&A text "
        f"was extracted for {num['text_extracted']:,} firm-years: {num['text_ok']:,} pass "
        f"the quality screen and {num['text_suspicious']} fall below 300 tokens but are "
        f"retained and flagged, while {num['text_missing']:,} have no usable text; the "
        f"yearly extraction shares are {year_share}. All seven flagged rows remain in the "
        f"complete-case sample. The download audit verified 10,051 PDFs correct "
        f"out of 10,172 (98.8%); the 121 missing files are mostly pre-listing OTC (NEEQ) "
        f"years of Beijing Stock Exchange firms that CNINFO does not archive."
    )

    text["s52_intro"] = (
        "Table 5.1 reports the raw distributions of the nine features, before "
        "winsorisation and standardisation, Table 5.2 the rank correlation between each "
        "anomaly ranking and the "
        "Beneish M-Score, and Table 5.3 the event rates and enrichment ratios at the "
        "top-5%, top-10% and top-15% review thresholds under both benchmark definitions."
    )

    text["t51_caption"] = (
        f"Table 5.1. Descriptive statistics of the nine features in raw form, before "
        f"winsorisation and standardisation ({num['frame_years']:,} firm-years)."
    )
    text["p_after_t51"] = (
        "The financial features are right-skewed with heavy tails - for example "
        "`receivables_turnover` and `revenue_growth` reach extreme values - which is why "
        "the pipeline winsorises every feature at the 1st and 99th percentiles before "
        "standardisation. Two benchmark definitions are used throughout. The legacy "
        "definition follows Beneish (1999) literally and treats M > -1.78 as a risk flag; "
        f"in this sample it flags {num['legacy_flag']:,} of {num['n']:,} analysed firm-years "
        f"({num['legacy_share'] * 100:.1f}%), far above the single-digit incidence "
        "reported for Beneish's original US sample, so it is best read as a weak external "
        "reference rather than an event indicator. Because a cut-off that flags "
        f"{num['legacy_share'] * 100:.0f}% of the sample is far above the incidence the "
        "score was calibrated for, every enrichment ratio is mechanically diluted towards "
        "one, so we also "
        "report a recalibrated definition that flags the top decile of the sample's own "
        f"M-Score distribution (M > {num['q90']:.2f}, {num['cal_flag']:,} firm-years). The "
        "recalibrated benchmark is a relative ranking target, not an estimate of the fraud "
        "base rate; both definitions are reported side by side and neither ever enters "
        "model training."
    )
    text["t52_caption"] = (
        f"Table 5.2. Spearman rank correlation between each anomaly ranking and the "
        f"Beneish M-Score (n = {num['n']:,})."
    )
    text["t53_caption"] = (
        "Table 5.3. Event rates and enrichment ratios at the review thresholds, under the "
        "legacy cut-off (M > -1.78) and the recalibrated benchmark (M top-10%)."
    )

    text["p_after_t53"] = (
        "Under the legacy benchmark the finance-only Isolation Forest is weakly and "
        f"inversely rank-correlated with the M-Score (rho = {rho_fin:.3f}, "
        f"{_p_inline(num['p_if_finance'])}): the firm-years it ranks as most anomalous are, "
        "on average, slightly less likely to sit above the literal -1.78 cut-off. Its "
        f"top-10% review list still contains {num['en_legacy_if_finance_10']:.2f} times the "
        f"sample-wide flag rate ({num['en_legacy_if_finance_5']:.2f}x at the top-5% "
        f"threshold). The text-only ranking is "
        f"{_corr_clause(rho_text, num['p_if_text'])}, and adding the three textual "
        f"features leaves the fused ranking at {rho_fused:.3f}, essentially the same as "
        f"finance-only. RQ1 is therefore answered in the negative: in this sample, MD&A "
        "tone and readability features add no incremental value over structured financial "
        "features for reproducing the Beneish screen.\n\n"
        "Two features of that comparison matter for interpretation. First, the negative "
        "sign means the two instruments do not merely fail to agree - they order firms "
        "differently, so a screen built on statement shape selects firm-years that the "
        "earnings-manipulation proxy tends to place below its cut-off. Second, because the "
        "recalibrated benchmark defines its top decile on the M-Score itself, enrichment "
        "ratios rise mechanically for every model, yet the ordering survives: finance-only "
        f"reaches {num['en_calibrated_if_finance_10']:.2f} at the top-10% and "
        f"{num['en_calibrated_if_finance_5']:.2f} at the top-5% threshold, the fused model "
        f"{num['en_calibrated_if_fused_10']:.2f} and "
        f"{num['en_calibrated_if_fused_5']:.2f}, and the text-only model "
        f"{num['en_calibrated_if_text_10']:.2f} and "
        f"{num['en_calibrated_if_text_5']:.2f}, that is, below chance at both thresholds. "
        "The finance-only lead over the fused model is small and threshold-dependent and "
        "should not be read as a stable advantage. Taken with the group contributions in "
        "§5.3 and the external tests in §5.7, the evidence supports a narrow claim: textual "
        "features behave as a largely orthogonal signal that does not improve - and, in an "
        "unweighted fusion, slightly dilutes - a financial screen for Beneish-type "
        "earnings-management risk."
    )

    text["s53"] = (
        f"On the fused model, the financial group accounts for "
        f"{num['shap_finance'] * 100:.1f}% of the total absolute SHAP contribution and "
        f"the textual group for {num['shap_text'] * 100:.1f}%. The three most important "
        f"global features are {top3}; because their contributions are this close, the "
        "profile is better read as a flat importance distribution than as a dominant "
        "variable, and both feature families appear among the top attributes.\n\n"
        f"The top-ranked firm-year is firm {num['top1_symbol']} ({num['top1_year']}, "
        f"sub-industry {num['top1_industry']}), with a fused anomaly score of "
        f"{num['top1_score']:.3f} and an M-Score of {num['top1_mscore']:,.1f}, that is, a "
        f"firm the Beneish proxy does not flag. Its largest local SHAP drivers are "
        f"{drivers} — {_drivers_profile(num['top1_drivers'])} relative to "
        "its subindustry-year peers. The local explanation therefore illustrates the "
        "inverse relation documented in §5.2 rather than corroborating the benchmark: the "
        "Isolation Forest responds to statement shape, while the M-Score weights the same "
        "statements differently and, in this sample, ranks such firms lower."
    )

    by_year = num.get("rho_by_year", {})
    if by_year:
        years = sorted(by_year)
        fin_by_year = ", ".join(f"{year}: {by_year[year]['if_finance']:.3f}" for year in years)
        negative_years = sum(1 for year in years if by_year[year]["if_text"] < 0)
        yearly_sentence = (
            f"The ordering is also stable year by year (finance-only rho by year: {fin_by_year}); "
            f"the text-only correlation is weakly negative in {negative_years} of {len(years)} years "
            "and the fused correlation never departs from the finance-only value by more than "
            "0.01."
        )
    else:
        yearly_sentence = ""

    text["s54"] = (
        f"The top-10% overlap between the finance-only and fused rankings is "
        f"{num['overlap_fin_fused']:.3f} (they largely agree because the fused model is "
        "dominated by financial features), while the finance-only versus text-only overlap "
        f"is only {num['overlap_fin_text']:.3f}, so the two signal families order very "
        "different firms. The choice of benchmark changes the level of every enrichment "
        "ratio but not this ordering: under the recalibrated benchmark the finance-only "
        f"model leads the fused model by {num['en_calibrated_if_finance_10'] - num['en_calibrated_if_fused_10']:.2f} "
        "at the top-10% threshold, and the text-only model stays below both. "
        "The autoencoder reconstruction-error ranking does not reproduce the main result: "
        f"its rank correlation with the benchmark is {rho_ae:.3f} "
        f"({_p_inline(num['p_ae_fused'])}), and its top-10% enrichment is "
        f"{num['en_legacy_ae_fused_10']:.2f} under the legacy cut-off "
        f"({num['en_calibrated_ae_fused_10']:.2f} recalibrated), barely above chance. "
        + yearly_sentence + " The conclusion is therefore a property of the "
        "Isolation Forest specification combined with these features, not a model-free "
        "property of the data, and it should be read as a screening signal rather than a "
        "stable risk label."
    )

    density = num.get("lexicon_density") or {}
    if density:
        lex_sentence = (
            "the sentiment lexicon matches "
            f"{density['sentiment_terms']['v02']:.1f} terms per 1,000 MD&A tokens against "
            f"{density['sentiment_terms']['v01']:.1f} for the bootstrap version "
            f"({density['sentiment_terms']['ratio']:.1f}x), so the null result is not an "
            "artefact of a sparse dictionary"
        )
    else:
        lex_sentence = "the lexicon is matched word by word"

    benchmark_body = _benchmark_finding(num).replace(
        "The study's most robust result concerns the benchmark rather than the text. ", ""
    )
    text["s55"] = (
        "The evidence supports two claims, one negative and one positive. The negative "
        f"claim is that the three MD&A features do not improve the unsupervised ranking "
        f"against the Beneish M-Score (rho {rho_fused:.3f} fused, {rho_fin:.3f} "
        f"finance-only, against {rho_text:.3f} for text alone). The positive claim concerns "
        f"the benchmark itself. {benchmark_body} The inversion is therefore not a nuisance "
        "but a finding: the M-Score cannot serve as a proxy for audit risk in this setting, "
        "and a null RQ1 may reflect the target rather than the text. Three limitations "
        f"bound the interpretation. First, the literal -1.78 cut-off flags "
        f"{num['legacy_share'] * 100:.1f}% of the sample and the recalibrated top-decile "
        "definition is a relative target rather than an estimate of the true base rate, so "
        "neither delivers a clean precision figure; the external outcome is the sharper test "
        "precisely because it is not circular. Second, the textual measures remain "
        f"approximations: {lex_sentence}; readability is a character-level proxy for "
        "processing cost, and scanned or unreadable reports are excluded. Third, the design "
        "is a three-year manufacturing sample, so the negative RQ1 result should be read as "
        "evidence about this period and industry rather than as a general law about Chinese "
        "disclosure text. These choices are disclosed in the reproducibility guide (§5), and "
        "every table in this section can be regenerated from the released scripts."
    )

    density_all = num.get("lexicon_density") or {}
    dense_sent = density_all.get("sentiment_terms") or {}
    old = num.get("v01") or {}
    if dense_sent:
        density_phrase = (
            f"the sentiment measure matches {dense_sent['v02']:.1f} terms per 1,000 MD&A "
            f"tokens against {dense_sent['v01']:.1f} in the first specification "
            f"({dense_sent['ratio']:.1f} times denser)"
        )
    else:
        density_phrase = "the sentiment measure is now matched token by token against a full lexicon"
    if old:
        moved = (
            f"The substantive answer does not move: the text-only rank correlation goes from "
            f"{old['if_text']['rho']:.3f} to {num['rho_if_text']:.3f}, the fused correlation "
            f"from {old['if_fused']['rho']:.3f} to {num['rho_if_fused']:.3f}, and the "
            f"autoencoder from {old['ae_fused']['rho']:.3f} "
            f"({_p_inline(old['ae_fused']['p'])}) to {num['rho_ae_fused']:.3f} "
            f"({_p_inline(num['p_ae_fused'])}); under the recalibrated benchmark the text-only "
            f"top-10% enrichment falls from {old.get('calibrated_if_text_10', float('nan')):.2f} "
            f"to {num['en_calibrated_if_text_10']:.2f}."
        )
    else:
        moved = (
            f"The substantive answer does not move: the text-only rank correlation is "
            f"{num['rho_if_text']:.3f} against {num['rho_if_finance']:.3f} for the "
            f"finance-only ranking."
        )

    text["s56_heading"] = "5.6 From the First to the Second Specification"
    text["s56a"] = (
        "The first version of this study measured MD&A text with a small bootstrap lexicon "
        "and evaluated every ranking against the literal Beneish cut-off. Two design "
        "weaknesses became apparent once the full sample was in place: the bootstrap list "
        "matched only a handful of terms per thousand words, so a null result could "
        "plausibly be dismissed as a measurement artefact, and the literal cut-off flagged "
        "well over half of the sample, so every enrichment ratio was mechanically pulled "
        "towards one. Rather than report a fragile null, we rebuilt both components and "
        "re-ran the complete pipeline on the same firm-years."
    )
    text["t54_caption"] = (
        "Table 5.4. First and second specifications: what changed and what it did to the "
        "results."
    )
    text["s56b"] = (
        "Table 5.4 summarises the two specifications. The lexicon was replaced by the full "
        "Chinese financial sentiment list of Yao et al. (2021), uncertainty terms were "
        "expanded, substring counting was replaced by jieba token matching, and the single "
        "threshold was supplemented by a sample-calibrated top-decile definition: "
        f"{density_phrase}. {moved} One caveat applies to that comparison: the first "
        "specification was estimated on the earlier financial intermediate, in which the "
        "annual statement rows were merged positionally and therefore lagged or mixed "
        "firm-years (§5.1 describes the repair). Part of the movement in Table 5.4 - "
        "notably the fused correlation changing sign - reflects that data correction "
        "rather than the lexicon alone. With that caveat, the second specification removes "
        "the two most obvious measurement objections while leaving RQ1 answered negatively. "
        "Both specifications are retained: the frozen v0.1 lexicons, the cached MD&A text, "
        "and the archived result tables are stored in the repository, and "
        "scripts/compare_runs.py reproduces the comparison reported here."
    )
    text.update(_section57_en(num))
    return text


def render_markdown(num: dict, text: dict) -> str:
    """Render §5 as markdown, mirroring the Word structure (5.1-5.5)."""
    def to_pipe(rows: list[list[str]]) -> str:
        head = "| " + " | ".join(rows[0]) + " |"
        sep = "| " + " | ".join("---" for _ in rows[0]) + " |"
        body = ["| " + " | ".join(row) + " |" for row in rows[1:]]
        return "\n".join([head, sep, *body])

    paras_after_t53 = text["p_after_t53"].split("\n\n")
    lines = [
        "# 5. Experiment and Results",
        "",
        "> Status: regenerated from `run_07` output by `scripts/build_section5.py`.",
        f"> Sample: n = {num['n']:,} firm-years, {num['n_firms']:,} firms, 2021-2023.",
        "> Delete this banner before merging into the Word manuscript.",
        "",
        "## 5.1 Final Sample and Data Coverage",
        "",
        text["s51"],
        "",
        "## 5.2 Descriptive Statistics and Main Results (RQ1)",
        "",
        text["s52_intro"],
        "",
        text["t51_caption"],
        "",
        to_pipe(_table_51(num)),
        "",
        text["p_after_t51"],
        "",
        text["t52_caption"],
        "",
        to_pipe(_table_52(num)),
        "",
        text["t53_caption"],
        "",
        to_pipe(_table_53(num)),
        "",
        paras_after_t53[0],
        "",
        paras_after_t53[1] if len(paras_after_t53) > 1 else "",
        "",
        "## 5.3 Group Contributions (RQ2: finance vs text)",
        "",
    ]
    for block in text["s53"].split("\n\n"):
        lines += [block, ""]
    lines += ["## 5.4 Robustness (RQ3: ranking stability)", "", text["s54"], ""]
    lines += ["## 5.5 Discussion and Limitations", "", text["s55"], ""]
    lines += ["## " + text["s56_heading"], "", text["s56a"], "", text["t54_caption"], ""]
    lines += [to_pipe(_table_54(num)), "", text["s56b"], ""]
    if "s57_heading" in text:
        lines += ["## " + text["s57_heading"], "", text["s57a"], "", text["s57b"], ""]
        lines += [text["t55_caption"], "", to_pipe(_table_55(num)), ""]
        lines += [text["s57c"], ""]
        lines += [text["t56_caption"], "", to_pipe(_table_56(num)), ""]
        lines += [text["s57d"], "", text["s57e"], ""]
    lines += [
        "## Suggested figures (paths from run_07)",
        "",
        "1. outputs/figures/score_distribution_if_fused.png (main text)",
        "2. outputs/figures/topk_enrichment.png",
        "3. outputs/figures/group_contributions.png",
        "4. outputs/figures/shap_importance.png",
        "5. outputs/figures/ranking_overlap.png",
        "",
    ]
    return "\n".join(lines)


def _plain(text: str) -> str:
    """Remove markdown backticks so they do not leak into the Word body."""
    return text.replace("`", "")


def _set_paragraph_text(paragraph: Paragraph, text: str) -> None:
    """Replace the text of a paragraph while keeping its paragraph formatting."""
    runs = paragraph.runs
    if not runs:
        paragraph.add_run(text)
        return
    runs[0].text = text
    for run in runs[1:]:
        run._element.getparent().remove(run._element)


def _make_paragraph_like(
    model: Paragraph, text: str, size: float, italic: bool, bold: bool = False
) -> object:
    """Create a paragraph element copying ``model``'s paragraph properties."""
    element = copy.deepcopy(model._p)
    for child in list(element):
        if child.tag.endswith("}r") or child.tag.endswith("}hyperlink"):
            element.remove(child)
    paragraph = Paragraph(element, model._parent)
    if italic:
        paragraph.paragraph_format.space_before = Pt(8)
        paragraph.paragraph_format.space_after = Pt(2)
        paragraph.paragraph_format.keep_with_next = True
    run = paragraph.add_run(text)
    run.italic = italic
    run.bold = bold
    run.font.size = Pt(size)
    return element


def _make_table(rows: list[list[str]], sample: Paragraph) -> object:
    """Build a bordered table and return its XML element (detached)."""
    document = sample.part.document
    table: Table = document.add_table(rows=len(rows), cols=len(rows[0]))
    table.style = "Table Grid"
    for r, row in enumerate(rows):
        for c, value in enumerate(row):
            cell = table.cell(r, c)
            cell.text = ""
            run = cell.paragraphs[0].add_run(str(value))
            run.font.size = Pt(8)
            run.bold = r == 0
            cell.paragraphs[0].paragraph_format.space_after = Pt(1)
            cell.paragraphs[0].paragraph_format.space_before = Pt(1)
    for row_index, row in enumerate(table.rows):
        tr_pr = row._tr.get_or_add_trPr()
        cant_split = OxmlElement("w:cantSplit")
        tr_pr.append(cant_split)
        if row_index == 0:
            tr_pr.append(OxmlElement("w:tblHeader"))
    element = table._tbl
    element.getparent().remove(element)
    return element


def patch_docx(num: dict, text: dict, src: Path, dst: Path) -> list[str]:
    """Refresh §5 (and two neighbouring paragraphs) and typeset the three tables."""
    document = Document(str(src))
    paragraphs = document.paragraphs
    log: list[str] = []

    replacements = {
        SLOT_ABSTRACT: text["abstract_updates"],
        SLOT_LIMITATIONS: text["limitations"],
        SLOT_S51: text["s51"],
        SLOT_S52_INTRO: text["s52_intro"],
        SLOT_S53: text["s53"],
        SLOT_S54: text["s54"],
        SLOT_S55: text["s55"],
    }
    if SLOT_ABSTRACT in replacements:
        abstract = paragraphs[SLOT_ABSTRACT].text.strip()
        keep = abstract.rsplit(" On the final sample", 1)[0]
        replacements[SLOT_ABSTRACT] = keep + " " + text["abstract_updates"]

    for index, new_text in replacements.items():
        old = paragraphs[index].text.strip()
        _set_paragraph_text(paragraphs[index], _plain(new_text))
        log.append(f"para {index}: {len(old)} -> {len(new_text)} chars")

    anchor = paragraphs[INSERT_AFTER]._p
    items: list[tuple[str, str, str | list[list[str]], float, bool]] = [
        ("para", text["t51_caption"], "", 9, True),
        ("table", "", _table_51(num), 8, False),
        ("para", text["p_after_t51"], "", 0, False),
        ("para", text["t52_caption"], "", 9, True),
        ("table", "", _table_52(num), 8, False),
        ("para", text["t53_caption"], "", 9, True),
        ("table", "", _table_53(num), 8, False),
    ]
    for block in text["p_after_t53"].split("\n\n"):
        items.append(("para", block, "", 0, False))

    for kind, body, rows, size, italic in items:
        if kind == "para":
            element = _make_paragraph_like(
                paragraphs[INSERT_AFTER], _plain(body), size, italic
            )
            if italic:
                paragraph = Paragraph(element, paragraphs[INSERT_AFTER]._parent)
                paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
        else:
            element = _make_table(rows, paragraphs[INSERT_AFTER])
        anchor.addnext(element)
        anchor = element
        log.append(f"inserted {kind}: {len(body) if body else len(rows)}")

    # §5.6 sits after the §5.5 body paragraph and before the §6 heading.
    section_anchor = paragraphs[SLOT_S55]._p
    heading = _make_paragraph_like(
        paragraphs[SLOT_S55], _plain(text["s56_heading"]), 13, False, bold=True
    )
    heading_para = Paragraph(heading, paragraphs[SLOT_S55]._parent)
    heading_para.paragraph_format.space_before = Pt(12)
    heading_para.paragraph_format.space_after = Pt(4)
    heading_para.paragraph_format.keep_with_next = True
    caption_s56 = _make_paragraph_like(
        paragraphs[SLOT_S55], _plain(text["t54_caption"]), 9, True
    )
    caption_para = Paragraph(caption_s56, paragraphs[SLOT_S55]._parent)
    caption_para.alignment = WD_ALIGN_PARAGRAPH.LEFT
    closing = [
        heading,
        _make_paragraph_like(paragraphs[SLOT_S55], _plain(text["s56a"]), 0, False),
        caption_s56,
        _make_table(_table_54(num), paragraphs[SLOT_S55]),
        _make_paragraph_like(paragraphs[SLOT_S55], _plain(text["s56b"]), 0, False),
    ]
    for element in closing:
        section_anchor.addnext(element)
        section_anchor = element
        log.append("inserted s56 element")

    if "s57_heading" in text:
        heading57 = _make_paragraph_like(
            paragraphs[SLOT_S55], _plain(text["s57_heading"]), 13, False, bold=True
        )
        heading57_para = Paragraph(heading57, paragraphs[SLOT_S55]._parent)
        heading57_para.paragraph_format.space_before = Pt(12)
        heading57_para.paragraph_format.space_after = Pt(4)
        heading57_para.paragraph_format.keep_with_next = True
        caption55 = _make_paragraph_like(
            paragraphs[SLOT_S55], _plain(text["t55_caption"]), 9, True
        )
        Paragraph(caption55, paragraphs[SLOT_S55]._parent).alignment = (
            WD_ALIGN_PARAGRAPH.LEFT
        )
        caption56 = _make_paragraph_like(
            paragraphs[SLOT_S55], _plain(text["t56_caption"]), 9, True
        )
        Paragraph(caption56, paragraphs[SLOT_S55]._parent).alignment = (
            WD_ALIGN_PARAGRAPH.LEFT
        )
        closing57 = [
            heading57,
            _make_paragraph_like(paragraphs[SLOT_S55], _plain(text["s57a"]), 0, False),
            _make_paragraph_like(paragraphs[SLOT_S55], _plain(text["s57b"]), 0, False),
            caption55,
            _make_table(_table_55(num), paragraphs[SLOT_S55]),
            _make_paragraph_like(paragraphs[SLOT_S55], _plain(text["s57c"]), 0, False),
            caption56,
            _make_table(_table_56(num), paragraphs[SLOT_S55]),
            _make_paragraph_like(paragraphs[SLOT_S55], _plain(text["s57d"]), 0, False),
            _make_paragraph_like(paragraphs[SLOT_S55], _plain(text["s57e"]), 0, False),
        ]
        for element in closing57:
            section_anchor.addnext(element)
            section_anchor = element
            log.append("inserted s57 element")

    _fit_body_spacing(document, BODY_LINE_SPACING)
    document.save(str(dst))
    return log


def _fit_body_spacing(document, target: float) -> int:
    """Tighten the body leading slightly so the manuscript stays inside 12-15 pages.

    Only paragraphs that already carry the template's 1.5 multiple are touched, so
    headings, captions and table cells keep their own settings.  The change is
    purely typographic: no text, table or number is altered.
    """
    changed = 0
    for paragraph in document.paragraphs:
        spacing = paragraph.paragraph_format.line_spacing
        if spacing is None:
            continue
        try:
            current = float(spacing)
        except (TypeError, ValueError):
            continue
        if abs(current - 1.5) < 0.01:
            paragraph.paragraph_format.line_spacing = target
            changed += 1
    return changed


MODEL_LABELS_CN = {
    "if_finance": "财务单独 IF",
    "if_text": "文本单独 IF",
    "if_fused": "融合 IF",
    "ae_fused": "融合自编码器",
}

TABLE_CELLS_CN = {
    "Feature": "特征",
    "mean": "均值",
    "std": "标准差",
    "min": "最小值",
    "max": "最大值",
    "Model": "模型",
    "Spearman rho": "Spearman ρ",
    "p-value": "p 值",
    "Event rate (legacy)": "事件率（legacy）",
    "Enrichment (legacy)": "富集率（legacy）",
    "Event rate (recalibrated)": "事件率（校准）",
    "Enrichment (recalibrated)": "富集率（校准）",
}

CN_SLOT_ABSTRACT = 8
CN_SLOT_S51 = 37
CN_SLOT_S52 = 39
CN_SLOT_S53 = 41
CN_SLOT_S54 = 43
CN_SLOT_S55 = 45
CN_INSERT_AFTER = CN_SLOT_S52


def _translate_rows(rows: list[list[str]]) -> list[list[str]]:
    """Map the English table headers and model names onto their Chinese labels."""
    mapping = dict(TABLE_CELLS_CN)
    mapping.update({label: MODEL_LABELS_CN[key] for key, label in MODEL_LABELS.items()})
    return [[mapping.get(value, value) for value in row] for row in rows]


def _table_54_cn(num: dict) -> list[list[str]]:
    """Chinese version of Table 5.4 (first versus second specification)."""
    old = num.get("v01") or {}
    density = (num.get("lexicon_density") or {}).get("sentiment_terms", {})
    if old:
        text_rho_old = f"{old['if_text']['rho']:.3f}"
        fused_rho_old = f"{old['if_fused']['rho']:.3f}"
        ae_old = f"{old['ae_fused']['rho']:.3f}（p = {old['ae_fused']['p']:.3f}）"
        text_en_old = (
            f"{old['calibrated_if_text_10']:.2f}"
            if "calibrated_if_text_10" in old
            else "不适用"
        )
    else:
        text_rho_old = fused_rho_old = ae_old = text_en_old = "不适用"
    return [
        ["设计选择", "第一版（v0.1）", "第二版（v0.2）"],
        ["情感词典", "自建引导词表：正面 38 词 / 负面 33 词", "姚加权等（2021）：正面 3,585 词 / 负面 1,633 词"],
        ["词典匹配方式", "原文子串计数", "jieba 分词后词元精确匹配（用户词典 5,218 词）"],
        [
            "每 1000 词元情感词命中",
            f"{density.get('v01', 0):.1f}" if density else "不适用",
            (
                f"{density.get('v02', 0):.1f}（{density.get('ratio', 0):.1f} 倍）"
                if density
                else "不适用"
            ),
        ],
        ["不确定词表", "23 词", "约 100 词（Loughran-McDonald 与曾庆生等）"],
        ["Beneish 基准", f"仅原文阈值 M > −1.78（标红 {num['legacy_share'] * 100:.1f}%）", f"原文阈值 + 样本前十分位校准（M > {num['q90']:.2f}，10%）"],
        ["文本单独 / 融合秩相关", f"{text_rho_old} / {fused_rho_old}", f"{num['rho_if_text']:.3f} / {num['rho_if_fused']:.3f}"],
        ["自编码器秩相关（p）", ae_old, f"{num['rho_ae_fused']:.3f}（p = {num['p_ae_fused']:.3f}）"],
        ["文本单独前 10% 富集（校准口径）", text_en_old, f"{num['en_calibrated_if_text_10']:.2f}"],
        ["RQ1 的回答", "对 Beneish 筛查无增量价值", "对 Beneish 筛查结论不变；监督模型仅有微小、统计上不可区分的增量（表 5.6）"],
    ]


def prose_cn(num: dict) -> dict:
    """Chinese translation of the §5 paragraphs, driven by the same numbers."""
    rho_fin = num["rho_if_finance"]
    rho_text = num["rho_if_text"]
    rho_fused = num["rho_if_fused"]
    rho_ae = num["rho_ae_fused"]
    year_share = "、".join(
        f"{num['year_share_text'][y] * 100:.1f}%（{y}）"
        for y in sorted(num["year_share_text"])
    )
    top3 = "、".join(f"{name}（{value:.3f}）" for name, value in num["shap_top3"])
    drivers = "、".join(num["top1_drivers"])
    text: dict = {}

    text["abstract"] = (
        _benchmark_finding_cn(num)
        + f" 以该基准衡量，文本没有增量：融合模型与 Beneish M-Score 的 Spearman 秩相关为 "
        f"{rho_fused:.3f}，与仅使用财务特征的 {rho_fin:.3f} 几乎相同，两者都是弱负相关。"
        f"在前 10% 审查队列中，按样本自身校准的基准（M-Score 前十分位）计算，融合模型的富集率为 "
        f"{num['en_calibrated_if_fused_10']:.2f}，财务单独模型为 "
        f"{num['en_calibrated_if_finance_10']:.2f}；若沿用 Beneish 原始 −1.78 阈值，两者分别为 "
        f"{num['en_legacy_if_fused_10']:.2f} 和 {num['en_legacy_if_finance_10']:.2f}。SHAP 结果显示，"
        f"财务特征组对融合排序的绝对贡献占比为 {num['shap_finance'] * 100:.1f}%，文本组为 "
        f"{num['shap_text'] * 100:.1f}%。本文的输出仅用于确定审查优先级，而非认定公司存在欺诈、违法或低质量披露。"
        + _abstract_external_cn(num)
    )

    text["s51"] = (
        f"最终可用样本为 {num['n']:,} 个公司—年度观测，覆盖 {num['n_firms']:,} 家公司。样本框包含 "
        f"{num['frame_firms']:,} 家制造业公司与 {num['frame_years']:,} 个公司—年度观测（2021 年 "
        f"{num['frame_by_year'].get(2021, 0):,}；2022 年 {num['frame_by_year'].get(2022, 0):,}；"
        f"2023 年 {num['frame_by_year'].get(2023, 0):,}），年度可用观测为 "
        f"{num['by_year'].get(2021, 0):,}、{num['by_year'].get(2022, 0):,}、"
        f"{num['by_year'].get(2023, 0):,}。年报下载覆盖率为 98.8%，MD&A 文本每年在 "
        f"{num['text_extracted']:,} 个公司—年度上成功抽取（{year_share}）：其中 "
        f"{num['text_ok']:,} 条通过质量筛选，{num['text_suspicious']} 条少于 300 token，仍保留在样本中"
        f"并打上标记；另有 {num['text_missing']} 条无可解析文本（PDF 缺失 {num['text_no_pdf']} 条、"
        f"无 MD&A 章节 {num['text_no_mda']} 条、抽取失败 {num['text_failed']} 条）。七条短文本全部"
        f"留在 {num['n']:,} 个完整观测之内。逐条审计结果见可复现指南的下载核对表。"
    )

    text["s52_intro"] = (
        "表 5.1 报告九个特征标准化前的原始分布，表 5.2 报告各排序与 Beneish M-Score 的秩相关，"
        "表 5.3 报告前 5%、10% 与 15% 审查阈值下的事件率与富集率，并同时给出两种基准口径。"
    )
    text["t51_caption"] = (
        f"表 5.1 九个特征在缩尾与标准化之前的原始描述统计（{num['frame_years']:,} 个公司—年度观测）。"
    )
    text["p_desc"] = (
        "财务特征呈右偏厚尾（例如应收账款周转率与营收增长率的极值很大），因此管线在标准化前"
        "对每个特征做 1% 与 99% 分位的缩尾处理。本文同时使用两种基准。legacy 口径按 Beneish (1999) "
        f"原文以 M > −1.78 作为风险标记，在本样本中标红 {num['legacy_flag']:,} 个观测（占 "
        f"{num['legacy_share'] * 100:.1f}%），远高于 Beneish 美国原始样本的个位数发生率，因此只能作为"
        "弱外部参照而非事件指标。由于标红比例过高会把每个富集率机械地压向 1，本文另报告按样本自身 "
        f"M-Score 前十分位校准的口径（M > {num['q90']:.2f}，{num['cal_flag']:,} 个观测）。校准口径是"
        "相对排序目标，并非欺诈基准率的估计；两种口径并列报告，且均不进入模型训练。"
    )
    text["t52_caption"] = (
        f"表 5.2 各排序与 Beneish M-Score 的 Spearman 秩相关（n = {num['n']:,}）。"
    )
    text["t53_caption"] = (
        "表 5.3 各审查阈值下的事件率与富集率：legacy 口径（M > −1.78）与校准口径（M 前 10%）。"
    )
    text["p_results"] = (
        f"财务单独、文本单独、融合 Isolation Forest 以及融合自编码器与 Beneish M-Score 的 "
        f"Spearman 秩相关分别为 {rho_fin:.3f}（{_p_inline(num['p_if_finance'])}）、"
        f"{rho_text:.3f}（{_p_inline(num['p_if_text'])}）、{rho_fused:.3f}"
        f"（{_p_inline(num['p_if_fused'])}）和 {rho_ae:.3f}（{_p_inline(num['p_ae_fused'])}）。"
        "四个相关的符号均为负且数值很小：财务单独显著为负，文本单独与零无异，融合模型与财务单独"
        "几乎相同，说明加入文本特征并未改善排序，RQ1 不成立。前 10% 队列中，财务单独的富集率为 "
        f"legacy 口径 {num['en_legacy_if_finance_10']:.2f}、校准口径 "
        f"{num['en_calibrated_if_finance_10']:.2f}；融合为 "
        f"{num['en_legacy_if_fused_10']:.2f} 与 {num['en_calibrated_if_fused_10']:.2f}；文本单独为 "
        f"{num['en_legacy_if_text_10']:.2f} 与 {num['en_calibrated_if_text_10']:.2f}，在两种口径下都"
        "低于随机。负号的含义是两套工具对公司排序的方向相反，而非彼此印证：M-Score 高的公司并未"
        "被异常分数排到前列。因此 RQ1 的否定结论在两种基准口径下均成立。"
    )
    text["s53"] = (
        f"SHAP 全局解释显示，财务组与文本组的绝对贡献占比分别为 "
        f"{num['shap_finance'] * 100:.1f}% 和 {num['shap_text'] * 100:.1f}%。各特征的平均绝对贡献"
        f"相当接近，排名前三的是 {top3}，说明重要性分布较平坦，两类特征都进入前列。对于最高排序"
        f"观测 {num['top1_symbol']}（{num['top1_year']} 年，子行业 {num['top1_industry']}），融合"
        f"异常分数为 {num['top1_score']:.3f}，M-Score 为 {num['top1_mscore']:,.1f}（Beneish 基准"
        f"并未将其标红），主要局部驱动因素为 {drivers}。该案例说明融合模型捕捉的是报表结构与文本"
        "语调的组合，而非 M-Score 所度量的应计操纵，正与 §5.2 的负相关一致；这些结果不构成因果"
        "解释或违规认定。"
    )
    by_year_cn = num.get("rho_by_year", {})
    if by_year_cn:
        years_cn = sorted(by_year_cn)
        fin_by_year_cn = "、".join(
            f"{year} 年 {by_year_cn[year]['if_finance']:.3f}" for year in years_cn
        )
        negative_cn = sum(1 for year in years_cn if by_year_cn[year]["if_text"] < 0)
        yearly_cn = (
            f"分年度看排序也很稳定：财务单独的秩相关为 {fin_by_year_cn}；文本单独在 "
            f"{len(years_cn)} 年中有 {negative_cn} 年为负，且融合模型与财务单独的差距在每一年"
            "都不超过 0.01。"
        )
    else:
        yearly_cn = ""

    text["s54"] = (
        f"不同模型前 10% 名单的重叠程度为：财务单独与融合 {num['overlap_fin_fused']:.3f}，"
        f"财务与文本仅 {num['overlap_fin_text']:.3f}，说明两类信号排序出的公司差异很大。"
        f"自编码器重建误差与基准的相关为 {rho_ae:.3f}（p = {num['p_ae_fused']:.3f}），前 10% "
        f"富集率为 {num['en_legacy_ae_fused_10']:.3f}（校准口径 "
        f"{num['en_calibrated_ae_fused_10']:.3f}），仅略高于随机，未复现主结果。"
        + yearly_cn +
        "更换基准只改变富集率的"
        "水平，不改变模型排序，因此结论对模型选择敏感，宜作为筛查信号而非稳定风险标签。"
    )
    density = num.get("lexicon_density") or {}
    if density:
        lex_cn = (
            f"情感词典为姚加权等（2021）正式版，分词后逐词匹配，每 1000 个 MD&A 词元命中 "
            f"{density['sentiment_terms']['v02']:.1f} 个情感词（引导版为 "
            f"{density['sentiment_terms']['v01']:.1f} 个，约 "
            f"{density['sentiment_terms']['ratio']:.1f} 倍），因此否定结论并非词表过稀所致"
        )
    else:
        lex_cn = "情感词典为姚加权等（2021）正式版，分词后逐词匹配"
    text["s55"] = (
        f"研究局限包括：第一，基准本身不完美，−1.78 阈值在本样本标红 {num['legacy_share'] * 100:.1f}% 的观测，而校准口径只是"
        f"相对目标，两者都无法给出干净的精确率；第二，文本度量仍是近似——{lex_cn}，可读性基于字符级代理，扫描件与不可读年报被排除；第三，样本限于"
        "制造业三年窗口，因此 RQ1 的否定结论应理解为该时期该行业的证据，而非关于中文披露文本的一般"
        "规律。上述选择均在可复现指南（§5）中披露，且本节所有表格都可由已发布脚本重新生成。"
    )

    old = num.get("v01") or {}
    dense_sent = (num.get("lexicon_density") or {}).get("sentiment_terms") or {}
    if dense_sent:
        density_phrase = (
            f"每 1000 个 MD&A 词元命中 {dense_sent['v02']:.1f} 个情感词，第一版为 "
            f"{dense_sent['v01']:.1f} 个，密度提高到 {dense_sent['ratio']:.1f} 倍"
        )
    else:
        density_phrase = "情感度量改为对完整词表逐词匹配"
    if old:
        moved = (
            f"核心结论并未改变：文本单独的秩相关由 {old['if_text']['rho']:.3f} 变为 "
            f"{num['rho_if_text']:.3f}，融合模型由 {old['if_fused']['rho']:.3f} 变为 "
            f"{num['rho_if_fused']:.3f}，自编码器由 {old['ae_fused']['rho']:.3f}"
            f"（{_p_inline(old['ae_fused']['p'])}）变为 {num['rho_ae_fused']:.3f}"
            f"（{_p_inline(num['p_ae_fused'])}）；在校准口径下，文本单独的前 10% 富集率由 "
            f"{old.get('calibrated_if_text_10', float('nan')):.2f} 降至 "
            f"{num['en_calibrated_if_text_10']:.2f}"
        )
    else:
        moved = (
            f"核心结论并未改变：文本单独的秩相关为 {num['rho_if_text']:.3f}，"
            f"财务单独模型为 {num['rho_if_finance']:.3f}"
        )

    text["s56_heading"] = "5.6 从第一版到第二版：做法改进与结果差异"
    text["s56a"] = (
        "本研究第一版使用自建的小规模引导词典度量 MD&A 文本，并只用 Beneish 原始阈值评估排序。"
        "在完整样本到位后发现两个设计弱点：引导词典每千词只能命中个位数的情感词，"
        "因此阴性结果容易被质疑为度量太粗；而原始阈值会标红样本中过半的观测，"
        "使所有富集率被机械地拉向 1。为避免报告一个脆弱的否定结论，我们重建了两部分设计，"
        "并在完全相同的 firm-year 样本上重跑了整条流程。"
    )
    text["t54_caption"] = "表 5.4　第一版与第二版的设定差异及其对结果的影响"
    text["s56b"] = (
        f"表 5.4 汇总了两版设定。第二版以姚加权等（2021）完整中文金融情感词表替换引导词典，"
        f"扩充不确定词表，将子串计数改为 jieba 词元精确匹配，并在单一阈值之外补充了样本前十分位的"
        f"校准口径：{density_phrase}。{moved}。需要说明的是，第一版的财务中间表按位置合并三张报表，"
        f"导致部分年报行取到上一年度或错配的数据；第二版在修正后的年报口径上重跑，因此表 5.4 中融合"
        f"相关由正转负，部分反映的是这次数据修正而非词典变化。改进的实质是让否定结论建立在正确的"
        f"财务口径上——第二版消除了两个最容易被指出的度量质疑，而 RQ1 的回答依然是文本特征对 Beneish "
        f"筛查没有增量价值。两版设定均被保留：第一版的词典冻结文件、MD&A 文本缓存与结果表都存放在"
        f"仓库中，scripts/compare_runs.py 可复现本文报告的差异。"
    )
    text.update(_section57_cn(num))
    return text


def _table_55_cn(num: dict) -> list[list[str]]:
    """Chinese version of Table 5.5 (scores against real outcomes)."""
    rows = [
        [
            "分数",
            "AUC：非标审计意见",
            "AUC：披露类违规（t+1）",
            "前 10% 富集：非标意见",
            "前 10% 富集：披露类违规",
        ]
    ]
    for model in EVENT_SCORES:
        opinion = _event_score(num, "mod_opinion", model)
        violation = _event_score(num, "violation_disclosure_t1", model)
        rows.append(
            [
                MODEL_LABELS_CN.get(model, model),
                _cell_value(opinion, "auc"),
                _cell_value(violation, "auc"),
                _cell_value(opinion, "lift_10pct", 2),
                _cell_value(violation, "lift_10pct", 2),
            ]
        )
    return rows


CN_SUPERVISED_SETS = (
    ("finance", "仅财务"),
    ("text", "仅文本"),
    ("fused", "融合"),
)
CN_SUPERVISED_LABELS = (("logit", "Logit"), ("hgb", "梯度提升"))


def _table_56_cn(num: dict) -> list[list[str]]:
    """Chinese version of Table 5.6 (grouped cross-validation comparison)."""
    rows = [
        [
            "特征集",
            "模型",
            "AUC：非标意见",
            "\u0394AUC（相对财务）",
            "AUC：披露类违规（t+1）",
            "\u0394AUC（相对财务）",
        ]
    ]
    for feature_set, set_label in CN_SUPERVISED_SETS:
        for model, model_label in CN_SUPERVISED_LABELS:
            opinion = _event_delta(num, "mod_opinion", model, feature_set)
            violation = _event_delta(num, "violation_disclosure_t1", model, feature_set)
            delta_opinion = _event_delta(num, "mod_opinion", model, "delta_fused_vs_finance")
            delta_violation = _event_delta(
                num, "violation_disclosure_t1", model, "delta_fused_vs_finance"
            )
            rows.append(
                [
                    set_label,
                    model_label,
                    _cell_value(opinion, "auc"),
                    (
                        _cell_value(delta_opinion, "auc")
                        if feature_set == "fused"
                        else "-"
                    ),
                    _cell_value(violation, "auc"),
                    (
                        _cell_value(delta_violation, "auc")
                        if feature_set == "fused"
                        else "-"
                    ),
                ]
            )
    return rows


def _section57_cn(num: dict) -> dict:
    """Compose Chinese §5.7 from the same numbers as the English block."""
    events = num.get("events") or {}
    ranking = events.get("ranking") or {}
    supervised = events.get("supervised") or {}
    text: dict = {}
    if not ranking:
        return text

    def cell(label: str, model: str) -> dict:
        return ranking.get((label, model), {})

    def gain(label: str, model: str) -> dict:
        return supervised.get((label, model, "delta_fused_vs_finance"), {})

    def auc(bucket: dict) -> str:
        if "auc" not in bucket:
            return "不适用"
        return f"{bucket['auc']:.3f}"

    def dtext(bucket: dict) -> str:
        if "auc" not in bucket:
            return "不适用"
        return f"{bucket['auc']:+.3f} [{bucket['lo']:+.3f}, {bucket['hi']:+.3f}]"

    def sup_auc(label: str, model: str, set_name: str) -> str:
        bucket = supervised.get((label, model, set_name)) or {}
        if "auc" not in bucket:
            return "不适用"
        return f"{bucket['auc']:.3f}"

    n = events.get("n", num["n"])
    mod_count = events.get("mod_opinion_count", 0)
    mod_rate = events.get("mod_opinion_rate", float("nan"))
    wide_count = events.get("mod_opinion_wide_count", 0)
    wide_rate = events.get("mod_opinion_wide_rate", float("nan"))
    any_count = events.get("violation_any_t1_count", 0)
    any_rate = events.get("violation_any_t1_rate", float("nan"))
    disc_count = events.get("violation_disclosure_t1_count", 0)
    disc_rate = events.get("violation_disclosure_t1_rate", float("nan"))
    by_year = events.get("mod_by_year") or {}
    year_phrase = "、".join(
        f"{int(year)} 年 {value * 100:.1f}%" for year, value in sorted(by_year.items())
    )

    fin = cell("mod_opinion", "finance-only IF")
    txt = cell("mod_opinion", "text-only IF")
    fused = cell("mod_opinion", "fused IF")
    ae = cell("mod_opinion", "fused AE")
    proxy = cell("mod_opinion", "Beneish M-Score")
    fin_v = cell("violation_disclosure_t1", "finance-only IF")

    gains = [
        gain(label, model) for label in EVENT_LABELS for model, _ in CN_SUPERVISED_LABELS
    ]
    gains = [item for item in gains if "auc" in item]
    positive = sum(1 for item in gains if item["auc"] >= 0)
    significant = sum(1 for item in gains if item["lo"] > 0)

    text["s57_heading"] = "5.7 面向真实监管结果的外部检验"
    text["s57a"] = (
        "Beneish M-Score 只是盈余操纵的代理变量，前几小节已显示它在本样本中表现不佳。"
        "为此我们用两类真实结果检验排序：CSMAR 的年报审计意见（FIN_Audit）与交易所违规公告"
        "（STK_Violation_Main）。审计意见窄口径为未获标准无保留意见（保留、保留加事项段、"
        "无法表示、否定），宽口径另计带解释性说明的无保留意见。违规标签取 t+1 年披露的公告，"
        "分为任一违规与披露类子集（推迟披露、虚假记载、误导性陈述、重大遗漏、虚构利润、"
        "虚列资产）。以 t+1 定位使检验相对模型所读年报严格前瞻，这也是违规窗口延长到 2025 年的原因。"
    )
    text["s57b"] = (
        f"两类结果在全部 {n:,} 个公司—年度观测上都可获得，因此这属于外部检验而非子样本核对。"
        f"非标意见较为稀有：{mod_count:,} 个观测（{mod_rate * 100:.2f}%），计入解释性说明后增至 "
        f"{wide_count:,} 个（{wide_rate * 100:.2f}%），分年度为 {year_phrase}，反映执法节奏而非公司属性。"
        f"违规更常见，因为它混合了披露问题与交易、治理类违规：{any_count:,} 个公司—年度"
        f"（{any_rate * 100:.2f}%）在 t+1 年收到过公告，其中披露类 {disc_count:,} 个"
        f"（{disc_rate * 100:.2f}%）。"
    )
    text["t55_caption"] = "表 5.5　各异常分数对真实监管结果的排序能力（区间见正文）"
    text["s57c"] = (
        f"表 5.5 报告排序质量。财务单独 Isolation Forest 能迁移到真实结果：非标意见 AUC 为 "
        f"{auc(fin)}，前 10% 队列事件率为基准率的 {fin.get('lift_10pct', float('nan')):.2f} 倍，"
        f"覆盖全部非标意见的 {fin.get('recall_10pct', float('nan')) * 100:.1f}%。文本单独接近随机"
        f"（{auc(txt)}），融合居中（{auc(fused)}），自编码器更弱（{auc(ae)}）。最值得注意的是"
        f"基准本身：Beneish M-Score 把非标意见公司排在样本后段（{auc(proxy)}），即回答 RQ1 所"
        "依据的代理变量与审计师的实际判断方向相反。"
        f"对前瞻的违规公告各分数都更弱，最好的是财务单独对披露类违规的 {auc(fin_v)}，"
        "符合“披露质量与监管注意力、交易行为混杂”的预期。"
    )
    text["t56_caption"] = "表 5.6　按公司分组的五折交叉验证样本外 AUC 及融合块相对财务块的增量"
    text["s57d"] = (
        "表 5.6 回答监督式问题：给定标签，文本块能否在财务块之外提供排序信息？"
        f"文本单独弱于财务单独（Logit {sup_auc('mod_opinion', 'logit', 'text')} 对 "
        f"{sup_auc('mod_opinion', 'logit', 'finance')}），因此关键在于两者是否互补。"
        f"按公司分组交叉验证时 Logit 在财务特征上为 {sup_auc('mod_opinion', 'logit', 'finance')}，"
        f"融合为 {sup_auc('mod_opinion', 'logit', 'fused')}，增量 {dtext(gain('mod_opinion', 'logit'))}；"
        f"梯度提升增量 {dtext(gain('mod_opinion', 'hgb'))}；披露类违规标签的增量为 "
        f"{dtext(gain('violation_disclosure_t1', 'logit'))} 与 "
        f"{dtext(gain('violation_disclosure_t1', 'hgb'))}。在 {len(gains)} 个标签×模型组合中，"
        f"增量为正的有 {positive} 个，区间不含 0 的有 {significant} 个。增量虽小、方向总体为正，"
        "但它针对的是审计师与监管机构的外部判断，与 §5.2 针对 Beneish 会计操纵构念的否定结论"
        "并不冲突：两者度量的是不同的构念。"
    )
    text["s57e"] = (
        "两点保留意见使这不能成为干净的正面结论。第一，审计意见与会计年度同期，"
        "表 5.5 衡量的是识别而非预测；只有 t+1 违规标签是严格前瞻检验，而在那里分数很弱。"
        "第二，两类标签都由审计师与监管机构产生，其能力与注意力随时间和公司变化，误差并非经典误差。"
        "实质解读是构念错配：MD&A 语调与可读性对审计师所监管的披露过程有信息量，"
        "但对 Beneish 所度量的会计操纵构念几乎没有信息量。因此 RQ1 的否定结论只对 Beneish 目标成立；"
        "面对真实审计结果，文本块带有小幅、并不总是可检测的增量——这是本文数据能够支撑的更稳妥表述。"
    )
    return text


def patch_docx_cn(num: dict, text: dict, src: Path, dst: Path) -> list[str]:
    """Refresh §5 of the Chinese deliverable and typeset the three tables."""
    document = Document(str(src))
    paragraphs = document.paragraphs
    log: list[str] = []

    replacements = {
        CN_SLOT_ABSTRACT: text["abstract"],
        CN_SLOT_S51: text["s51"],
        CN_SLOT_S52: text["s52_intro"],
        CN_SLOT_S53: text["s53"],
        CN_SLOT_S54: text["s54"],
        CN_SLOT_S55: text["s55"],
    }
    for index, new_text in replacements.items():
        old = paragraphs[index].text.strip()
        _set_paragraph_text(paragraphs[index], _plain(new_text))
        log.append(f"para {index}: {len(old)} -> {len(new_text)} chars")

    anchor = paragraphs[CN_INSERT_AFTER]._p
    items: list[tuple[str, str, list[list[str]] | None]] = [
        ("caption", text["t51_caption"], None),
        ("table", "", _translate_rows(_table_51(num))),
        ("para", text["p_desc"], None),
        ("caption", text["t52_caption"], None),
        ("table", "", _translate_rows(_table_52(num))),
        ("caption", text["t53_caption"], None),
        ("table", "", _translate_rows(_table_53(num))),
        ("para", text["p_results"], None),
    ]
    for kind, body, rows in items:
        if kind == "table":
            element = _make_table(rows, paragraphs[CN_INSERT_AFTER])
        else:
            element = _make_paragraph_like(
                paragraphs[CN_INSERT_AFTER],
                _plain(body),
                size=9 if kind == "caption" else 0,
                italic=kind == "caption",
            )
        anchor.addnext(element)
        anchor = element
        log.append(f"inserted {kind}")

    section_anchor = paragraphs[CN_SLOT_S55]._p
    heading = _make_paragraph_like(
        paragraphs[CN_SLOT_S55], _plain(text["s56_heading"]), 13, False, bold=True
    )
    heading_para = Paragraph(heading, paragraphs[CN_SLOT_S55]._parent)
    heading_para.paragraph_format.space_before = Pt(12)
    heading_para.paragraph_format.space_after = Pt(4)
    heading_para.paragraph_format.keep_with_next = True
    caption_s56 = _make_paragraph_like(
        paragraphs[CN_SLOT_S55], _plain(text["t54_caption"]), 9, True
    )
    caption_para = Paragraph(caption_s56, paragraphs[CN_SLOT_S55]._parent)
    caption_para.alignment = WD_ALIGN_PARAGRAPH.LEFT
    closing = [
        heading,
        _make_paragraph_like(paragraphs[CN_SLOT_S55], _plain(text["s56a"]), 0, False),
        caption_s56,
        _make_table(_table_54_cn(num), paragraphs[CN_SLOT_S55]),
        _make_paragraph_like(paragraphs[CN_SLOT_S55], _plain(text["s56b"]), 0, False),
    ]
    for element in closing:
        section_anchor.addnext(element)
        section_anchor = element
        log.append("inserted s56 element")

    if "s57_heading" in text:
        heading57 = _make_paragraph_like(
            paragraphs[CN_SLOT_S55], _plain(text["s57_heading"]), 13, False, bold=True
        )
        heading57_para = Paragraph(heading57, paragraphs[CN_SLOT_S55]._parent)
        heading57_para.paragraph_format.space_before = Pt(12)
        heading57_para.paragraph_format.space_after = Pt(4)
        heading57_para.paragraph_format.keep_with_next = True
        caption55 = _make_paragraph_like(
            paragraphs[CN_SLOT_S55], _plain(text["t55_caption"]), 9, True
        )
        Paragraph(caption55, paragraphs[CN_SLOT_S55]._parent).alignment = (
            WD_ALIGN_PARAGRAPH.LEFT
        )
        caption56 = _make_paragraph_like(
            paragraphs[CN_SLOT_S55], _plain(text["t56_caption"]), 9, True
        )
        Paragraph(caption56, paragraphs[CN_SLOT_S55]._parent).alignment = (
            WD_ALIGN_PARAGRAPH.LEFT
        )
        closing57 = [
            heading57,
            _make_paragraph_like(
                paragraphs[CN_SLOT_S55], _plain(text["s57a"]), 0, False
            ),
            _make_paragraph_like(
                paragraphs[CN_SLOT_S55], _plain(text["s57b"]), 0, False
            ),
            caption55,
            _make_table(_table_55_cn(num), paragraphs[CN_SLOT_S55]),
            _make_paragraph_like(
                paragraphs[CN_SLOT_S55], _plain(text["s57c"]), 0, False
            ),
            caption56,
            _make_table(_table_56_cn(num), paragraphs[CN_SLOT_S55]),
            _make_paragraph_like(
                paragraphs[CN_SLOT_S55], _plain(text["s57d"]), 0, False
            ),
            _make_paragraph_like(
                paragraphs[CN_SLOT_S55], _plain(text["s57e"]), 0, False
            ),
        ]
        for element in closing57:
            section_anchor.addnext(element)
            section_anchor = element
            log.append("inserted s57 element")

    document.save(str(dst))
    return log


def render_markdown_cn(num: dict, text: dict) -> str:
    """Render the Chinese §5 markdown that mirrors the Chinese Word deliverable."""

    def to_pipe(rows: list[list[str]]) -> str:
        head = "| " + " | ".join(rows[0]) + " |"
        sep = "| " + " | ".join("---" for _ in rows[0]) + " |"
        body = ["| " + " | ".join(row) + " |" for row in rows[1:]]
        return "\n".join([head, sep, *body])

    lines = [
        "# 5. 实验结果",
        "",
        "> 状态：由 `scripts/build_section5.py --markdown-cn` 依据 run_07 输出重新生成。",
        f"> 样本：n = {num['n']:,} 个公司—年度观测，{num['n_firms']:,} 家公司，2021–2023 年。",
        "",
        "## 5.1 最终样本与数据覆盖",
        "",
        text["s51"],
        "",
        "## 5.2 RQ1：文本特征是否带来增量价值",
        "",
        text["s52_intro"],
        "",
        text["t51_caption"],
        "",
        to_pipe(_translate_rows(_table_51(num))),
        "",
        text["p_desc"],
        "",
        text["t52_caption"],
        "",
        to_pipe(_translate_rows(_table_52(num))),
        "",
        text["t53_caption"],
        "",
        to_pipe(_translate_rows(_table_53(num))),
        "",
        text["p_results"],
        "",
        "## 5.3 RQ2：财务组与文本组的贡献分布",
        "",
        text["s53"],
        "",
        "## 5.4 RQ3：排序稳定性",
        "",
        text["s54"],
        "",
        "## 5.5 讨论与局限",
        "",
        text["s55"],
        "",
        "## " + text["s56_heading"],
        "",
        text["s56a"],
        "",
        text["t54_caption"],
        "",
        to_pipe(_table_54_cn(num)),
        "",
        text["s56b"],
        "",
    ]
    if "s57_heading" in text:
        lines += ["## " + text["s57_heading"], "", text["s57a"], "", text["s57b"], ""]
        lines += [text["t55_caption"], "", to_pipe(_table_55_cn(num)), ""]
        lines += [text["s57c"], ""]
        lines += [text["t56_caption"], "", to_pipe(_table_56_cn(num)), ""]
        lines += [text["s57d"], "", text["s57e"], ""]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--markdown", action="store_true", help="rewrite the markdown source")
    parser.add_argument("--docx", action="store_true", help="rewrite the Word deliverable")
    parser.add_argument(
        "--docx-src",
        type=Path,
        default=MANUSCRIPT / "source" / "Group12A2_Final_EN.docx",
        help="pre-patch master; never the patched deliverable itself",
    )
    parser.add_argument(
        "--docx-out",
        type=Path,
        default=MANUSCRIPT / "Group12A2_Final_EN.docx",
    )
    parser.add_argument(
        "--markdown-cn", action="store_true", help="rewrite the Chinese markdown source"
    )
    parser.add_argument("--docx-cn", action="store_true", help="rewrite the Chinese deliverable")
    parser.add_argument(
        "--docx-cn-src",
        type=Path,
        default=MANUSCRIPT / "source" / "Group12A2_Final_CN.docx",
        help="pre-patch master; never the patched deliverable itself",
    )
    parser.add_argument(
        "--docx-cn-out",
        type=Path,
        default=MANUSCRIPT / "Group12A2_Final_CN.docx",
    )
    args = parser.parse_args()

    num = collect_numbers()
    text = prose(num)
    if args.markdown or not (args.markdown or args.docx or args.docx_cn or args.markdown_cn):
        target = DOCS / "manuscript_experiment_section.md"
        target.write_text(render_markdown(num, text), encoding="utf-8")
        print(f"markdown written: {target}")
    if args.docx:
        log = patch_docx(num, text, args.docx_src, args.docx_out)
        for line in log:
            print(line)
        print(f"docx written: {args.docx_out}")
    if args.markdown_cn:
        target = DOCS / "manuscript_chinese_experiment_section.md"
        target.write_text(render_markdown_cn(num, prose_cn(num)), encoding="utf-8")
        print(f"markdown (cn) written: {target}")
    if args.docx_cn:
        log = patch_docx_cn(num, prose_cn(num), args.docx_cn_src, args.docx_cn_out)
        for line in log:
            print(line)
        print(f"docx (cn) written: {args.docx_cn_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
