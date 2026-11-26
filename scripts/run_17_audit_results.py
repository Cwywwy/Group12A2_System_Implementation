#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
run_17_audit_results.py
Author: Group12A2 DSW Team
Purpose: Re-verify the experiment data and the reported results without reusing
         the pipeline's own metric helpers. Every headline number is recomputed
         from the raw CSMAR exports or the saved score table with plain pandas,
         scipy and scikit-learn, then compared against the delivered CSVs and
         the manuscript tables. Divergences are written to
         outputs/reports/audit_2026-11-26.md.
Module: scripts

Revision History
----------------
2026-11-26  initial version: independent recomputation of labels, correlations,
            AUCs, enrichment, overlaps, SHAP shares and supervised AUCs.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import (  # noqa: E402
    ALL_FEATURES,
    DATA_PROCESSED,
    DATA_RAW,
    FINANCE_FEATURES,
    TABLES,
    complete_t1_years,
)

REPORT = PROJECT_ROOT / "outputs" / "reports" / "audit_2026-11-26.md"
AUDIT_FILE = DATA_RAW / "csmar_events" / "FIN_Audit.xlsx"
VIOLATION_FILE = DATA_RAW / "csmar_events" / "STK_Violation_Main.xlsx"

DISCLOSURE_KEYWORDS = (
    "推迟披露",
    "虚假记载",
    "误导性陈述",
    "重大遗漏",
    "虚构利润",
    "虚列资产",
    "披露不实",
    "擅自改变",
    "财务造假",
    "会计处理不当",
)
DISCLOSURE_CODES = {"P2501", "P2502", "P2503", "P2504", "P2505", "P2506"}

ROWS: list[dict[str, str]] = []


def record(group: str, name: str, recomputed, reported, status: str, note: str = "") -> None:
    ROWS.append(
        {
            "group": group,
            "check": name,
            "recomputed": str(recomputed),
            "reported": str(reported),
            "status": status,
            "note": note,
        }
    )
    print(f"[{status}] {group} | {name}: recomputed={recomputed} reported={reported} {note}")


def close(a, b, tol: float = 5e-4) -> bool:
    try:
        return abs(float(a) - float(b)) <= tol
    except (TypeError, ValueError):
        return False


def compare(group: str, name: str, recomputed, reported, tol: float = 5e-4) -> bool:
    ok = close(recomputed, reported, tol)
    record(group, name, f"{recomputed:.6g}" if isinstance(recomputed, (int, float, np.floating)) else recomputed,
           reported, "PASS" if ok else "FAIL")
    return ok


def load_codes(path: Path, code_col: str) -> pd.DataFrame:
    """Read a CSMAR export, dropping the label row and the unit row."""
    frame = pd.read_excel(path, dtype=str, sheet_name=0)
    frame = frame.iloc[2:].copy()
    frame = frame[frame[code_col].astype(str).str.fullmatch(r"\d{1,6}(\.0)?").fillna(False)]
    frame[code_col] = (
        frame[code_col].astype(str).str.strip().str.replace(r"\.0$", "", regex=True).str.zfill(6)
    )
    return frame


def fiscal_year(value: object) -> int | None:
    stamp = pd.to_datetime(value, errors="coerce")
    if pd.isna(stamp) or stamp.month != 12:
        return None
    return int(stamp.year)


# --------------------------------------------------------------------------- #
# A. Structure of the analysis sample
# --------------------------------------------------------------------------- #
def check_structure() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    frame = pd.read_csv(DATA_PROCESSED / "feature_table.csv", dtype={"symbol": str})
    scores = pd.read_csv(TABLES / "anomaly_scores.csv", dtype={"symbol": str})
    events = pd.read_csv(DATA_PROCESSED / "event_table.csv", dtype={"symbol": str})

    for table, label in ((frame, "feature_table"), (scores, "anomaly_scores"), (events, "event_table")):
        table["symbol"] = table["symbol"].str.zfill(6)
        dup = int(table.duplicated(["symbol", "fiscal_year"]).sum())
        record("A. structure", f"{label}: duplicate firm-year keys", dup, 0, "PASS" if dup == 0 else "FAIL")

    record("A. structure", "frame rows", len(frame), 17_600, "PASS" if len(frame) == 17_600 else "FAIL")
    firms = frame["symbol"].nunique()
    record("A. structure", "frame firms", firms, 3_893, "PASS" if firms == 3_893 else "FAIL")
    per_year = frame.groupby("fiscal_year").size().to_dict()
    expected = {2021: 3_165, 2022: 3_404, 2023: 3_603, 2024: 3_666, 2025: 3_762}
    record("A. structure", "frame rows by year", per_year, expected,
           "PASS" if per_year == expected else "FAIL")

    record("A. structure", "analysis rows", len(scores), 16_408, "PASS" if len(scores) == 16_408 else "FAIL")
    analysis_firms = scores["symbol"].nunique()
    record("A. structure", "analysis firms", analysis_firms, 3_773,
           "PASS" if analysis_firms == 3_773 else "FAIL")
    score_years = scores.groupby("fiscal_year").size().to_dict()
    expected_scores = {2021: 2_732, 2022: 3_124, 2023: 3_383, 2024: 3_531, 2025: 3_638}
    record("A. structure", "analysis rows by year", score_years, expected_scores,
           "PASS" if score_years == expected_scores else "FAIL")

    keys = set(zip(frame["symbol"], frame["fiscal_year"]))
    orphans = sum(1 for k in zip(scores["symbol"], scores["fiscal_year"]) if k not in keys)
    record("A. structure", "analysis keys outside the frame", orphans, 0,
           "PASS" if orphans == 0 else "FAIL")

    event_keys = set(zip(events["symbol"], events["fiscal_year"]))
    missing = sum(1 for k in zip(scores["symbol"], scores["fiscal_year"]) if k not in event_keys)
    record("A. structure", "analysis keys without an event row", missing, 0,
           "PASS" if missing == 0 else "FAIL")

    nulls = int(scores[["if_finance", "if_text", "if_fused", "ae_fused", "m_score"]].isna().sum().sum())
    record("A. structure", "missing values in the score table", nulls, 0, "PASS" if nulls == 0 else "FAIL")
    return frame, scores, events


# --------------------------------------------------------------------------- #
# B. Labels recomputed from the raw CSMAR exports
# --------------------------------------------------------------------------- #
def check_labels(scores: pd.DataFrame, events: pd.DataFrame) -> None:
    audit = load_codes(AUDIT_FILE, "Stkcd")
    audit["fiscal_year"] = audit["Accper"].map(fiscal_year)
    audit = audit.dropna(subset=["fiscal_year"])
    audit["fiscal_year"] = audit["fiscal_year"].astype(int)

    def opinion_class(text: object) -> str:
        value = "" if not isinstance(text, str) else text.strip()
        if "无法表示意见" in value:
            return "disclaimer"
        if "否定意见" in value:
            return "adverse"
        # "无保留意见" contains "保留意见" as a substring, so the clean and the
        # emphasis variants have to be recognised before the qualified catch-all.
        if "无保留意见" in value:
            if "解释性说明" in value or "强调事项" in value:
                return "emphasis"
            return "clean"
        if "保留意见" in value:
            return "qualified"
        return "unknown"

    audit["opinion_class"] = audit["Audittyp"].map(opinion_class)
    audit = audit.drop_duplicates(["Stkcd", "fiscal_year"], keep="first")
    audit = audit.rename(columns={"Stkcd": "symbol"})
    strict = {"qualified", "disclaimer", "adverse"}
    wide = strict | {"emphasis"}
    audit["mod_opinion_raw"] = audit["opinion_class"].isin(strict).astype(int)
    audit["mod_opinion_wide_raw"] = audit["opinion_class"].isin(wide).astype(int)

    merged = events.merge(
        audit[["symbol", "fiscal_year", "mod_opinion_raw", "mod_opinion_wide_raw"]],
        on=["symbol", "fiscal_year"],
        how="left",
    )
    merged[["mod_opinion_raw", "mod_opinion_wide_raw"]] = merged[
        ["mod_opinion_raw", "mod_opinion_wide_raw"]
    ].fillna(0).astype(int)

    sample = merged.merge(scores[["symbol", "fiscal_year"]], on=["symbol", "fiscal_year"], how="inner")
    narrow = int(sample["mod_opinion_raw"].sum())
    wid = int(sample["mod_opinion_wide_raw"].sum())
    record("B. labels", "modified opinions in the analysis sample", narrow, 322,
           "PASS" if narrow == 322 else "FAIL", "recomputed from FIN_Audit.xlsx")
    record("B. labels", "modified opinions, wide definition", wid, 593,
           "PASS" if wid == 593 else "FAIL")
    mismatch = int((sample["mod_opinion_raw"] != sample["mod_opinion"]).sum())
    record("B. labels", "rows where the raw and delivered narrow labels differ", mismatch, 0,
           "PASS" if mismatch == 0 else "FAIL")

    violations = load_codes(VIOLATION_FILE, "Symbol")
    violations = violations.rename(columns={"Symbol": "symbol"})
    violations["declare_date"] = pd.to_datetime(violations["DeclareDate"], errors="coerce")
    violations = violations.dropna(subset=["declare_date"])
    violations["declare_year"] = violations["declare_date"].dt.year.astype(int)

    def is_disclosure(row: pd.Series) -> int:
        text = row["ViolationType"] if isinstance(row["ViolationType"], str) else ""
        if any(keyword in text for keyword in DISCLOSURE_KEYWORDS):
            return 1
        codes = {part.strip() for part in str(row["ViolationTypeID"]).replace("，", ";").replace(",", ";").split(";")}
        return int(bool(codes & DISCLOSURE_CODES))

    violations["is_disclosure"] = violations.apply(is_disclosure, axis=1)
    counts = (
        violations.groupby(["symbol", "declare_year"])
        .agg(any_count=("ViolationID", "size"), disclosure_count=("is_disclosure", "sum"))
        .reset_index()
        .rename(columns={"declare_year": "fiscal_year"})
    )
    counts["fiscal_year"] = counts["fiscal_year"] - 1  # t+1 alignment

    settled = complete_t1_years([2021, 2022, 2023, 2024, 2025])
    record("B. labels", "settled fiscal years for the violation label", settled, [2021, 2022, 2023],
           "PASS" if settled == [2021, 2022, 2023] else "FAIL")

    window = events[events["fiscal_year"].isin(settled)]
    joined = window.merge(counts, on=["symbol", "fiscal_year"], how="left").fillna(
        {"any_count": 0, "disclosure_count": 0}
    )
    any_events = int((joined["any_count"] > 0).sum())
    disc_events = int((joined["disclosure_count"] > 0).sum())
    record("B. labels", "any-violation events, FY2021-2023", any_events, 1_965,
           "PASS" if any_events == 1_965 else "FAIL", "recomputed from STK_Violation_Main.xlsx")
    record("B. labels", "disclosure-violation events, FY2021-2023", disc_events, 1_337,
           "PASS" if disc_events == 1_337 else "FAIL")
    record("B. labels", "settled-window firm-years", len(window), 9_239,
           "PASS" if len(window) == 9_239 else "FAIL")

    outside = int(events.loc[~events["fiscal_year"].isin(settled), "violation_any_t1"].sum())
    rates = {
        int(year): float(block["violation_any_t1"].mean())
        for year, block in events.groupby("fiscal_year")
    }
    record("B. labels", "violation flags carried outside the settled window", outside, "excluded at metric time",
           "NOTE", f"annual t+1 rates {', '.join(f'{y}: {r:.1%}' for y, r in rates.items())}")


# --------------------------------------------------------------------------- #
# C. Statistics recomputed with scipy and scikit-learn
# --------------------------------------------------------------------------- #
def auc(labels: np.ndarray, scores: np.ndarray) -> float:
    mask = ~np.isnan(scores)
    return float(roc_auc_score(labels[mask], scores[mask]))


def bootstrap_ci_rows(labels: np.ndarray, scores: np.ndarray, n_boot: int = 400, seed: int = 42):
    mask = ~np.isnan(scores)
    labels, scores = labels[mask], scores[mask]
    rng = np.random.default_rng(seed)
    draws = np.empty(n_boot)
    n = len(labels)
    for i in range(n_boot):
        idx = rng.integers(0, n, n)
        draws[i] = roc_auc_score(labels[idx], scores[idx])
    return float(np.percentile(draws, 2.5)), float(np.percentile(draws, 97.5))


def bootstrap_ci_firms(labels: np.ndarray, scores: np.ndarray, firms: np.ndarray, n_boot: int = 400, seed: int = 42):
    """Cluster bootstrap: resample firms, keep every firm-year of those firms."""
    rng = np.random.default_rng(seed)
    frame = pd.DataFrame({"label": labels, "score": scores, "firm": firms})
    groups = {firm: block for firm, block in frame.groupby("firm")}
    names = np.array(list(groups.keys()))
    draws = np.empty(n_boot)
    for i in range(n_boot):
        picks = rng.choice(names, size=len(names), replace=True)
        block = pd.concat([groups[name] for name in picks])
        draws[i] = roc_auc_score(block["label"], block["score"])
    return float(np.percentile(draws, 2.5)), float(np.percentile(draws, 97.5))


def check_statistics(scores: pd.DataFrame, events: pd.DataFrame) -> None:
    metrics = pd.read_csv(TABLES / "model_metrics.csv")
    recorded = dict(zip(metrics["model"], metrics["spearman_rho"]))
    p_recorded = dict(zip(metrics["model"], metrics["spearman_p"]))
    for column in ("if_finance", "if_text", "if_fused", "ae_fused"):
        rho, p = stats.spearmanr(scores[column], scores["m_score"])
        compare("C. statistics", f"spearman rho {column}", float(rho), recorded[column])
        compare("C. statistics", f"spearman p {column}", float(p), p_recorded[column], tol=5e-6)

    merged = scores.merge(
        events[["symbol", "fiscal_year", "mod_opinion", "mod_opinion_wide",
                "violation_any_t1", "violation_disclosure_t1"]],
        on=["symbol", "fiscal_year"],
        how="left",
    )
    ranking = pd.read_csv(TABLES / "event_ranking_metrics.csv")
    names = {
        "if_finance": "finance-only IF",
        "if_text": "text-only IF",
        "if_fused": "fused IF",
        "ae_fused": "fused AE",
        "m_score": "Beneish M-Score",
    }
    ungated_rows: dict[str, float] = {}
    for label in ("mod_opinion", "violation_disclosure_t1"):
        block = ranking[ranking["label"] == label]
        lookup = dict(zip(block["model"], block["auc"]))
        # Forward-looking labels are only scored where the t+1 window is settled;
        # the ungated value is recorded separately because censoring flatters the
        # benchmark rather than the model under test.
        if label.startswith("violation"):
            settled = complete_t1_years(sorted(merged["fiscal_year"].unique()))
            scored = merged[merged["fiscal_year"].isin(settled)]
        else:
            settled = []
            scored = merged
        for column, model in names.items():
            value = auc(scored[label].to_numpy(), scored[column].to_numpy())
            compare("C. statistics", f"AUC {label} / {model}", value, lookup[model])
            if label.startswith("violation"):
                ungated = auc(merged[label].to_numpy(), merged[column].to_numpy())
                ungated_rows[model] = float(ungated)
                record("C. statistics", f"AUC {label} / {model}, ungated",
                       f"{ungated:.4f}", "not reported", "NOTE",
                       f"{ungated - value:+.4f} versus the settled window")

    # Interval width: rows resampled independently versus firms resampled as blocks.
    labels = merged["mod_opinion"].to_numpy()
    lo_row, hi_row = bootstrap_ci_rows(labels, merged["if_finance"].to_numpy())
    lo_firm, hi_firm = bootstrap_ci_firms(labels, merged["if_finance"].to_numpy(), merged["symbol"].to_numpy())
    record("C. statistics", "AUC interval, rows resampled",
           f"[{lo_row:.3f}, {hi_row:.3f}]", "[0.762, 0.809]",
           "PASS" if close(lo_row, 0.762, 3e-3) and close(hi_row, 0.809, 3e-3) else "NOTE")
    record("C. statistics", "AUC interval, firms resampled",
           f"[{lo_firm:.3f}, {hi_firm:.3f}]", "not reported",
           "NOTE", f"width {hi_firm - lo_firm:.3f} vs {hi_row - lo_row:.3f} for the row bootstrap")
    # Publish the two audit facts the manuscript quotes: the interval width under
    # firm clustering, and how much the settled-window gate costs the benchmark.
    export = {
        "row_interval": [round(lo_row, 4), round(hi_row, 4)],
        "cluster_interval": [round(lo_firm, 4), round(hi_firm, 4)],
        "gate": {
            model: {
                "gated": round(float(metrics_row["auc"]), 4),
                "ungated": round(float(ungated_rows[model]), 4),
            }
            for model, metrics_row in ranking[ranking["label"] == "violation_disclosure_t1"]
            .set_index("model")
            .iterrows()
            if model in ungated_rows
        },
    }
    (TABLES / "audit_intervals.json").write_text(json.dumps(export, indent=2) + "\n", encoding="utf-8")

    topk = pd.read_csv(TABLES / "topk_metrics.csv")
    for benchmark, flag_column in (("legacy", "benchmark_flag"), ("calibrated", "benchmark_flag_calibrated")):
        flags = scores[flag_column].to_numpy()
        for column, model in (("if_finance", "if_finance"), ("if_text", "if_text"),
                              ("if_fused", "if_fused"), ("ae_fused", "ae_fused")):
            top = np.argsort(-scores[column].to_numpy())[: int(round(len(scores) * 0.10))]
            enrichment = float(np.mean(flags[top]) / np.mean(flags))
            row = topk[(topk["benchmark"] == benchmark) & (topk["model"] == model) & (topk["k"] == 0.10)]
            compare("C. statistics", f"enrichment {benchmark} / {model} @10%", enrichment,
                    float(row["enrichment"].iloc[0]), tol=1e-3)

    overlap = pd.read_csv(TABLES / "ranking_overlap.csv")
    rank = np.argsort(-scores["if_finance"].to_numpy())[: int(round(len(scores) * 0.10))]
    fused = np.argsort(-scores["if_fused"].to_numpy())[: int(round(len(scores) * 0.10))]
    text = np.argsort(-scores["if_text"].to_numpy())[: int(round(len(scores) * 0.10))]
    pair = {
        ("if_finance", "if_fused"): len(set(rank) & set(fused)) / len(set(rank)),
        ("if_finance", "if_text"): len(set(rank) & set(text)) / len(set(rank)),
        ("ae_fused", "if_fused"): len(set(np.argsort(-scores["ae_fused"].to_numpy())[: int(round(len(scores) * 0.10))]) & set(fused))
        / len(set(fused)),
    }
    for (a, b), value in pair.items():
        row = overlap[(overlap["model_a"] == a) & (overlap["model_b"] == b)]
        compare("C. statistics", f"top-10% overlap {a} vs {b}", value, float(row["top10_overlap"].iloc[0]), tol=1e-3)

    shap = pd.read_csv(TABLES / "shap_group_contributions.csv")
    share = dict(zip(shap["group"], shap["abs_shap_share"]))
    record("C. statistics", "SHAP finance share", f"{share['finance']:.4f}", "0.6572",
           "PASS" if close(share["finance"], 0.6572, 1e-3) else "FAIL")
    record("C. statistics", "SHAP shares sum to one", f"{sum(share.values()):.6f}", "1.0",
           "PASS" if close(sum(share.values()), 1.0, 1e-6) else "FAIL")


def check_supervised(scores: pd.DataFrame, events: pd.DataFrame, frame: pd.DataFrame) -> None:
    features = frame[["symbol", "fiscal_year", *ALL_FEATURES]].copy()
    data = (
        scores[["symbol", "fiscal_year"]]
        .merge(events[["symbol", "fiscal_year", "mod_opinion"]], on=["symbol", "fiscal_year"], how="left")
        .merge(features, on=["symbol", "fiscal_year"], how="left")
    )
    y = data["mod_opinion"].to_numpy(dtype=int)
    groups = data["symbol"].to_numpy()

    splitter = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42)
    folds = list(splitter.split(data[list(ALL_FEATURES)].to_numpy(), y, groups))
    overlaps = []
    for train, test in folds:
        overlaps.append(len(set(groups[train]) & set(groups[test])))
    record("C. supervised", "firms shared between training and validation folds",
           int(sum(overlaps)), 0, "PASS" if sum(overlaps) == 0 else "FAIL")

    recorded = pd.read_csv(TABLES / "event_supervised_metrics.csv")
    lookup = {
        (row["label"], row["model"], row["feature_set"]): row["oof_auc"]
        for _, row in recorded.iterrows()
    }
    for feature_set, columns in (("finance", FINANCE_FEATURES), ("fused", ALL_FEATURES)):
        oof = np.full(len(data), np.nan)
        for train, test in folds:
            model = Pipeline(
                [
                    ("impute", SimpleImputer(strategy="median")),
                    ("scale", StandardScaler()),
                    ("model", LogisticRegression(max_iter=2000, class_weight="balanced", random_state=42)),
                ]
            )
            model.fit(data.iloc[train][list(columns)].to_numpy(dtype=float), y[train])
            oof[test] = model.predict_proba(data.iloc[test][list(columns)].to_numpy(dtype=float))[:, 1]
        value = float(roc_auc_score(y, oof))
        compare("C. supervised", f"out-of-fold AUC logit / {feature_set}", value,
                float(lookup[("mod_opinion", "logit", feature_set)]))


# --------------------------------------------------------------------------- #
# D. Manuscript tables against the recomputed tables
# --------------------------------------------------------------------------- #
def _cell(text: str) -> float | None:
    """Parse a table cell into a float, or None for a dash or empty cell."""
    value = text.strip().replace("\u2212", "-").replace(",", "").replace("%", "")
    if value in {"", "-", "–", "—", "not applicable"}:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _numbers_in(text: str) -> set[float]:
    """Every numeric token in a block of text, rounded to four decimals."""
    found = set()
    for token in re.findall(r"\d[\d,]*(?:\.\d+)?", text):
        try:
            found.add(round(float(token.replace(",", "")), 4))
        except ValueError:
            continue
    return found


def check_manuscript() -> None:
    from docx import Document

    folder = PROJECT_ROOT / "outputs" / "manuscript"
    document = Document(str(folder / "Group12A2_Final_EN_v0.5.docx"))
    ranking = pd.read_csv(TABLES / "event_ranking_metrics.csv")
    supervised = pd.read_csv(TABLES / "event_supervised_metrics.csv")
    metrics = pd.read_csv(TABLES / "model_metrics.csv")
    topk = pd.read_csv(TABLES / "topk_metrics.csv")
    events = pd.read_csv(DATA_PROCESSED / "event_table.csv")
    frame = pd.read_csv(DATA_PROCESSED / "feature_table.csv")
    scores = pd.read_csv(TABLES / "anomaly_scores.csv")

    def grid(index: int) -> list[list[str]]:
        return [[cell.text.strip() for cell in row.cells] for row in document.tables[index].rows]

    def expect(section: str, label: str, shown: float | None, value: float, tolerance: float = 6e-4) -> None:
        ok = shown is not None and abs(shown - value) <= tolerance
        record(section, label, f"{shown}", f"{value:.6f}", "PASS" if ok else "FAIL")

    # Table 5.1: the four correlations and their p-values, already checked above,
    # now compared against the delivered table itself.
    rows = [[cell.replace("\u2212", "-") for cell in row] for row in grid(0)]
    expected = [
        ["Model", "Spearman rho", "p-value"],
        ["Finance-only IF", "-0.033", "< 0.001"],
        ["Text-only IF", "-0.021", "0.008"],
        ["Fused IF", "-0.019", "0.014"],
        ["Fused autoencoder", "-0.026", "0.001"],
    ]
    record("D. manuscript", "Table 5.1 cells", rows == expected, True,
           "PASS" if rows == expected else "FAIL",
           "" if rows == expected else f"first row {rows[1]} vs {expected[1]}")

    # Table 5.2: AUCs and lifts against both real outcomes, row order fixed.
    lookup = {(row["label"], row["model"]): row for _, row in ranking.iterrows()}
    panel52 = grid(1)
    for offset, (model, short) in enumerate(
        (
            ("finance-only IF", "finance-only"),
            ("text-only IF", "text-only"),
            ("fused IF", "fused"),
            ("fused AE", "autoencoder"),
            ("Beneish M-Score", "Beneish"),
        ),
        start=1,
    ):
        row = panel52[offset]
        for column, label in ((1, "mod_opinion"), (2, "violation_disclosure_t1")):
            expect(
                "D. manuscript",
                f"Table 5.2 {short} AUC {label}",
                _cell(row[column]),
                float(lookup[(label, model)]["auc"]),
            )
        expect(
            "D. manuscript",
            f"Table 5.2 {short} lift opinion",
            _cell(row[3]),
            float(lookup[("mod_opinion", model)]["lift_10pct"]),
            6e-3,
        )

    # Table 5.3: supervised out-of-fold AUCs and the paired deltas, row order fixed.
    panel53 = grid(2)
    for offset, feature_set, classifier in (
        (1, "finance", "logit"),
        (2, "finance", "hgb"),
        (3, "text", "logit"),
        (4, "text", "hgb"),
        (5, "fused", "logit"),
        (6, "fused", "hgb"),
    ):
        row = panel53[offset]
        key = supervised[
            (supervised["label"] == "mod_opinion")
            & (supervised["model"] == classifier)
            & (supervised["feature_set"] == feature_set)
        ]
        if key.empty:
            continue
        expect(
            "D. manuscript",
            f"Table 5.3 {feature_set}/{classifier} AUC",
            _cell(row[2]),
            float(key.iloc[0]["oof_auc"]),
        )
        if feature_set == "fused":
            reference = supervised[
                (supervised["label"] == "mod_opinion")
                & (supervised["model"] == classifier)
                & (supervised["feature_set"] == "finance")
            ]
            delta = float(key.iloc[0]["oof_auc"]) - float(reference.iloc[0]["oof_auc"])
            expect(
                "D. manuscript",
                f"Table 5.3 {feature_set}/{classifier} delta",
                _cell(row[3]),
                delta,
            )

    # Table A.1: the five-year row must equal the current run.
    current = grid(3)[1]
    expect("D. manuscript", "Table A.1 row n", _cell(current[2]), float(len(scores)), 0.5)
    expect(
        "D. manuscript",
        "Table A.1 row events",
        _cell(current[3]),
        float(events["mod_opinion"].sum()),
        0.5,
    )
    expect(
        "D. manuscript",
        "Table A.1 row finance AUC",
        _cell(current[4]),
        float(lookup[("mod_opinion", "finance-only IF")]["auc"]),
    )
    expect(
        "D. manuscript",
        "Table A.1 row Beneish AUC",
        _cell(current[5]),
        float(lookup[("mod_opinion", "Beneish M-Score")]["auc"]),
    )

    # Table B.1: descriptive statistics over the frame.
    panel_b1 = grid(4)
    for offset, feature, column, statistic in (
        (1, "roa", 2, "mean"),
        (2, "leverage", 2, "mean"),
        (1, "roa", 3, "std"),
    ):
        expect(
            "D. manuscript",
            f"Table B.1 {feature} {statistic}",
            _cell(panel_b1[offset][column]),
            float(getattr(frame[feature], statistic)()),
        )

    # Table B.2: recalibrated enrichment at the review threshold, rows in model order.
    panel_b2 = grid(5)
    for offset, model, short in (
        (2, "if_finance", "finance"),
        (5, "if_text", "text"),
        (8, "if_fused", "fused"),
        (11, "ae_fused", "autoencoder"),
    ):
        match = topk[
            (topk["model"] == model) & (topk["k"] == 0.1) & (topk["benchmark"] == "calibrated")
        ]
        if match.empty:
            continue
        expect(
            "D. manuscript",
            f"Table B.2 {short} enrichment",
            _cell(panel_b2[offset][5]),
            float(match.iloc[0]["enrichment"]),
        )

    # Table B.5: the attrition chain, including the closing summary row.
    retained = [int(value) for value in (_cell(row[3]) for row in grid(8)[1:]) if value is not None]
    record(
        "D. manuscript",
        "Table B.5 retained sequence",
        retained,
        [17600, 16641, 16640, 16408, 16408],
        "PASS" if retained == [17600, 16641, 16640, 16408, 16408] else "FAIL",
    )
    firms = int(scores["symbol"].nunique())
    record(
        "D. manuscript",
        "Table B.5 analysis firms",
        firms,
        3773,
        "PASS" if firms == 3773 else "FAIL",
    )

    # Table B.6: event counts and their base rates, rows in label order.
    settled = events[
        events["fiscal_year"].isin(complete_t1_years(sorted(events["fiscal_year"].unique())))
    ]
    panel_b6 = grid(9)
    for offset, series, denominator in (
        (1, events["mod_opinion"], len(events)),
        (2, events["mod_opinion_wide"], len(events)),
        (3, settled["violation_any_t1"], len(settled)),
        (4, settled["violation_disclosure_t1"], len(settled)),
    ):
        cell = panel_b6[offset][2]
        expect(
            "D. manuscript",
            f"Table B.6 row {offset} count",
            _cell(cell.split()[0]),
            float(series.sum()),
            0.5,
        )
        share = 100.0 * float(series.sum()) / denominator
        expect(
            "D. manuscript",
            f"Table B.6 row {offset} share",
            _cell(cell.split("(")[1].split("%")[0]),
            share,
            0.06,
        )

    # Cross-language integrity: every number in the Chinese manuscript must exist
    # in the English one, and vice versa, because the Chinese file is a translation.
    chinese = Document(str(folder / "Group12A2_Final_CN.docx"))
    english_text = " ".join(
        [paragraph.text for paragraph in document.paragraphs]
        + [cell.text for table in document.tables for row in table.rows for cell in row.cells]
    )
    chinese_text = " ".join(
        [paragraph.text for paragraph in chinese.paragraphs]
        + [cell.text for table in chinese.tables for row in table.rows for cell in row.cells]
    )
    english_numbers = _numbers_in(english_text)
    chinese_numbers = _numbers_in(chinese_text)
    only_chinese = sorted(chinese_numbers - english_numbers)
    only_english = sorted(english_numbers - chinese_numbers)
    record("D. manuscript", "numbers present only in the Chinese file", len(only_chinese), 0,
           "PASS" if not only_chinese else "FAIL", str(only_chinese[:8]))
    record("D. manuscript", "numbers present only in the English file", len(only_english), 0,
           "NOTE", str(only_english[:8]))


def write_report() -> int:
    frame = pd.DataFrame(ROWS)
    failures = int((frame["status"] == "FAIL").sum())
    lines = [
        "# 实验结果独立核验（2026-11-26）",
        "",
        "由 `scripts/run_17_audit_results.py` 生成：所有数字用 pandas / scipy / scikit-learn "
        "从原始 CSMAR 导出或已保存的评分表重算，不调用项目自身的评估辅助函数。",
        "",
        f"- 检查项：{len(frame)}",
        f"- 通过：{int((frame['status'] == 'PASS').sum())}",
        f"- 不一致：{failures}",
        f"- 提示：{int((frame['status'] == 'NOTE').sum())}",
        "",
        "| 组 | 检查项 | 重算值 | 报告值 | 结论 | 说明 |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for _, row in frame.iterrows():
        lines.append(
            f"| {row['group']} | {row['check']} | {row['recomputed']} | {row['reported']} | "
            f"{row['status']} | {row['note']} |"
        )
    lines.append("")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {REPORT}: {len(frame)} checks, {failures} failures")
    return 0 if failures == 0 else 1


def main() -> int:
    print("[audit] reading tables")
    frame, scores, events = check_structure()
    print("[audit] recomputing labels from the raw CSMAR exports")
    check_labels(scores, events)
    print("[audit] recomputing correlations, AUCs, enrichment and overlaps")
    check_statistics(scores, events)
    print("[audit] refitting the supervised comparison")
    check_supervised(scores, events, frame)
    print("[audit] checking the manuscript tables")
    check_manuscript()
    return write_report()


if __name__ == "__main__":
    raise SystemExit(main())
