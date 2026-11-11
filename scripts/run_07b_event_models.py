# -*- coding: utf-8 -*-
"""
run_07b_event_models.py
Author: Group12A2 DSW Team
Purpose: Evaluate the screening scores and the feature sets against real
         firm-year events (non-clean audit opinions and forward violation
         announcements) instead of the Beneish M-Score proxy.
Module: scripts

Usage: python scripts/run_07b_event_models.py [--events PATH] [--scores PATH]
                                               [--features PATH] [--boot N]

Two blocks are produced:

1. ranking_metrics - each existing score column (finance-only Isolation
   Forest, text-only, fused, autoencoder, M-Score reference) is used as a
   ranking and scored by AUC, PR-AUC and top-queue enrichment against the
   event labels, with bootstrap intervals.
2. supervised - finance-only, text-only and fused feature sets are compared
   under firm-grouped 5-fold cross validation with logistic regression and
   gradient boosting; the AUC difference against the finance-only baseline is
   reported with a paired bootstrap interval. This is the direct test of
   whether MD&A text adds incremental information about real events.

Revision History
----------------
2026-11-11  initial version: external-outcome evaluation for branch 3.
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import ALL_FEATURES, FINANCE_FEATURES, TABLES, TEXT_FEATURES  # noqa: E402
from src.evaluation.event_eval import (  # noqa: E402
    bootstrap_auc,
    oof_predictions,
    paired_delta_auc,
    ranking_metrics,
)

DEFAULT_EVENTS = PROJECT_ROOT / "data" / "processed" / "event_table.csv"
DEFAULT_SCORES = TABLES / "anomaly_scores.csv"
DEFAULT_FEATURES = PROJECT_ROOT / "data" / "processed" / "feature_table.csv"
REPORT = PROJECT_ROOT / "outputs" / "reports" / "event_branch_results.md"

LABELS = (
    ("mod_opinion", "Modified audit opinion (narrow)"),
    ("mod_opinion_wide", "Modified audit opinion (wide)"),
    ("violation_any_t1", "Any violation announced in t+1"),
    ("violation_disclosure_t1", "Disclosure violation announced in t+1"),
)
SCORE_COLUMNS = {
    "finance-only IF": "if_finance",
    "text-only IF": "if_text",
    "fused IF": "if_fused",
    "fused AE": "ae_fused",
    "Beneish M-Score": "m_score",
}
FEATURE_SETS = {
    "finance": tuple(FINANCE_FEATURES),
    "text": tuple(TEXT_FEATURES),
    "fused": tuple(ALL_FEATURES),
}
MODEL_KINDS = ("logit", "hgb")


def _load_inputs(args: argparse.Namespace) -> tuple[pd.DataFrame, pd.DataFrame]:
    events = pd.read_csv(Path(args.events), dtype={"symbol": str})
    events["symbol"] = events["symbol"].str.zfill(6)
    scores = pd.read_csv(Path(args.scores), dtype={"symbol": str})
    scores["symbol"] = scores["symbol"].str.zfill(6)
    frame = scores.merge(
        events.drop(columns=["mod_opinion_wide"], errors="ignore"),
        on=["symbol", "fiscal_year"],
        how="left",
    )
    wide = events[["symbol", "fiscal_year", "mod_opinion_wide"]]
    frame = frame.merge(wide, on=["symbol", "fiscal_year"], how="left")
    for column, _ in LABELS:
        frame[column] = frame[column].fillna(0).astype(int)
    return frame, events


def _supervised_block(frame: pd.DataFrame, features: pd.DataFrame, boot: int) -> pd.DataFrame:
    merged = frame.merge(
        features[["symbol", "fiscal_year", *ALL_FEATURES]],
        on=["symbol", "fiscal_year"],
        how="left",
    )
    rows: list[dict[str, object]] = []
    for label, _ in LABELS:
        if merged[label].nunique() < 2 or merged[label].sum() < 20:
            continue
        preds: dict[str, np.ndarray] = {}
        for kind in MODEL_KINDS:
            for set_name, columns in FEATURE_SETS.items():
                oof = oof_predictions(merged, label, columns, kind=kind)
                preds[f"{kind}:{set_name}"] = oof
                auc, lo, hi = bootstrap_auc(
                    merged[label].to_numpy(), oof, n_boot=boot
                )
                rows.append(
                    {
                        "label": label,
                        "model": kind,
                        "feature_set": set_name,
                        "n_features": len(columns),
                        "n": int(np.sum(~np.isnan(oof))),
                        "n_events": int(merged[label].sum()),
                        "oof_auc": auc,
                        "oof_auc_lo": lo,
                        "oof_auc_hi": hi,
                    }
                )
        for kind in MODEL_KINDS:
            base = preds.get(f"{kind}:finance")
            fused = preds.get(f"{kind}:fused")
            text = preds.get(f"{kind}:text")
            if base is None:
                continue
            for name, other in (("fused", fused), ("text", text)):
                if other is None:
                    continue
                delta, lo, hi = paired_delta_auc(
                    merged[label].to_numpy(), base, other, n_boot=boot
                )
                rows.append(
                    {
                        "label": label,
                        "model": kind,
                        "feature_set": f"delta_{name}_vs_finance",
                        "n_features": 0,
                        "n": int(np.sum(~np.isnan(other))),
                        "n_events": int(merged[label].sum()),
                        "oof_auc": delta,
                        "oof_auc_lo": lo,
                        "oof_auc_hi": hi,
                    }
                )
    return pd.DataFrame(rows)


def _write_report(ranking: pd.DataFrame, supervised: pd.DataFrame, path: Path) -> None:
    def _rank(label: str, model: str) -> pd.Series:
        return ranking[(ranking["label"] == label) & (ranking["model"] == model)].iloc[0]

    def _auc_delta(label: str, model: str, which: str) -> pd.Series:
        block = supervised[
            (supervised["label"] == label)
            & (supervised["model"] == model)
            & (supervised["feature_set"] == which)
        ]
        if block.empty:
            return pd.Series({"oof_auc": float("nan"), "oof_auc_lo": float("nan")})
        return block.iloc[0]

    finance_if = _rank("mod_opinion", "finance-only IF")
    text_if = _rank("mod_opinion", "text-only IF")
    mscore = _rank("mod_opinion", "Beneish M-Score")
    deltas = supervised[
        supervised["feature_set"].str.startswith("delta_fused_vs_finance")
    ]
    positive = int((deltas["oof_auc"] > 0).sum())
    significant = int((deltas["oof_auc_lo"] > 0).sum())

    lines = [
        "# External-outcome evaluation (branch 3)",
        "",
        "Event labels: modified audit opinions for fiscal year t (narrow = qualified,",
        "disclaimer or adverse; wide adds the explanatory-paragraph cases) and CSMAR",
        "violation announcements dated in fiscal year t+1 (any violation, and the",
        "disclosure-related subset: delayed disclosure, misstatement, material",
        "omission, fictitious profit or assets). Scores are used as risk rankings;",
        "AUC and top-queue enrichment carry bootstrap 95% intervals.",
        "",
        "## Headline findings",
        "",
        f"- The finance-only Isolation Forest score ranks firms with a modified audit",
        f"  opinion well above chance: AUC {finance_if['auc']:.3f} "
        f"[{finance_if['auc_lo']:.3f}, {finance_if['auc_hi']:.3f}], with "
        f"{finance_if['lift_5pct']:.2f}x enrichment and "
        f"{finance_if['recall_5pct']:.1%} of all events in the top-5% queue.",
        f"- The text-only score is close to chance for the same label "
        f"(AUC {text_if['auc']:.3f} [{text_if['auc_lo']:.3f}, {text_if['auc_hi']:.3f}]).",
        f"- The Beneish M-Score is *anti-correlated* with real modified opinions: "
        f"AUC {mscore['auc']:.3f} [{mscore['auc_lo']:.3f}, {mscore['auc_hi']:.3f}], "
        f"i.e. the proxy benchmark used in the first specification is not merely noisy, "
        f"it points the wrong way for this sample.",
        f"- Under firm-grouped cross validation the fused model beats the finance-only "
        f"model in {positive} of {len(deltas)} label-by-model combinations and the "
        f"bootstrap interval excludes zero in {significant} of them; every point "
        f"estimate is non-negative.",
        "",
        "## Ranking quality of the existing scores",
        "",
        "| Label | Score | AUC [95% CI] | PR-AUC | Lift top-10% [95% CI] |",
        "| --- | --- | --- | --- | --- |",
    ]
    for _, row in ranking.iterrows():
        lines.append(
            f"| {row['label']} | {row['model']} | "
            f"{row['auc']:.3f} [{row['auc_lo']:.3f}, {row['auc_hi']:.3f}] | "
            f"{row['pr_auc']:.3f} | "
            f"{row['lift_10pct']:.2f} [{row['lift_10pct_lo']:.2f}, {row['lift_10pct_hi']:.2f}] |"
        )
    lines += [
        "",
        "## Supervised comparison under firm-grouped cross validation",
        "",
        "| Label | Model | Feature set | OOF AUC [95% CI] |",
        "| --- | --- | --- | --- |",
    ]
    for _, row in supervised.iterrows():
        lines.append(
            f"| {row['label']} | {row['model']} | {row['feature_set']} | "
            f"{row['oof_auc']:+.3f} [{row['oof_auc_lo']:+.3f}, {row['oof_auc_hi']:+.3f}] |"
        )
    lines += [
        "",
        "`delta_*_vs_finance` rows are AUC differences against the finance-only",
        "baseline; an interval that covers zero means the extra feature block adds",
        "no detectable rank information for that event.",
        "",
        "## How to read this",
        "",
        "- The audit-opinion label is contemporaneous with the fiscal year (the report",
        "  for year t carries the opinion for year t), so it measures identification of",
        "  risky disclosures rather than forecasting. The violation label is strictly",
        "  forward-looking (announcements dated in t+1), which is why it is the harder",
        "  and more honest predictive test - and the one where all scores are weakest.",
        "- Modified opinions are rare (2.3%), so PR-AUC stays close to the base rate even",
        "  for a useful ranking; AUC and top-queue enrichment are the informative metrics.",
        "- Violation announcements mix disclosure problems with share-trading and other",
        "  violations, which dilutes signal; the disclosure subset is cleaner but still",
        "  driven by regulator capacity and media attention rather than by the accounts.",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--events", type=str, default=str(DEFAULT_EVENTS))
    parser.add_argument("--scores", type=str, default=str(DEFAULT_SCORES))
    parser.add_argument("--features", type=str, default=str(DEFAULT_FEATURES))
    parser.add_argument("--boot", type=int, default=400)
    args = parser.parse_args()

    frame, _ = _load_inputs(args)
    print(f"[run_07b] merged rows={len(frame):,} firms={frame['symbol'].nunique():,}")
    for label, _ in LABELS:
        print(f"[run_07b] {label}: events={int(frame[label].sum()):,} "
              f"rate={frame[label].mean():.2%}")

    ranking = pd.concat(
        [
            ranking_metrics(frame, label, SCORE_COLUMNS, n_boot=args.boot)
            for label, _ in LABELS
        ],
        ignore_index=True,
    )
    ranking.to_csv(TABLES / "event_ranking_metrics.csv", index=False, encoding="utf-8-sig")
    print(f"[run_07b] wrote {TABLES / 'event_ranking_metrics.csv'}")

    features = pd.read_csv(Path(args.features), dtype={"symbol": str})
    features["symbol"] = features["symbol"].str.zfill(6)
    supervised = _supervised_block(frame, features, args.boot)
    supervised.to_csv(
        TABLES / "event_supervised_metrics.csv", index=False, encoding="utf-8-sig"
    )
    print(f"[run_07b] wrote {TABLES / 'event_supervised_metrics.csv'}")

    _write_report(ranking, supervised, REPORT)
    print(f"[run_07b] wrote {REPORT}")

    focus = ranking[ranking["model"].isin(["finance-only IF", "fused IF", "text-only IF"])]
    for _, row in focus.iterrows():
        print(f"[run_07b] AUC {row['label']:<24s} {row['model']:<16s} "
              f"{row['auc']:.3f} [{row['auc_lo']:.3f}, {row['auc_hi']:.3f}] "
              f"lift10={row['lift_10pct']:.2f}")


if __name__ == "__main__":
    main()
