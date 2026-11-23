"""Add the Phase 4 supplementary tables and closing sentences to the manuscript.

Phase 4 closes the remaining evidence gaps: sample attrition, the definitions
and counts of the four external outcome labels, the paired increment for every
label and model, the overlap definition, the Beijing Stock Exchange coverage
and the tail of the Beneish score. Tables are generated from ``outputs/tables``
so the prose cannot drift from the results.

Author: Jinyu Wang
Purpose: patch the compact body, the appendix and the 23-page twin in place.
Module: scripts
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd
from docx import Document

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:  # allow "python scripts/patch_manuscript_v04.py"
    sys.path.insert(0, str(PROJECT_ROOT))

from src.reporting.docx_blocks import append_sentence, insert_block_after, replace_text  # noqa: E402
from src.reporting.docx_patch import paragraph_texts  # noqa: E402

BASE = PROJECT_ROOT / "11.23base"
FULL = BASE / "Group12A2_Final_EN_corrected.docx"
COMPACT = BASE / "Group12A2_Final_EN_corrected_compact.docx"
APPENDIX = BASE / "Group12A2_Final_EN_corrected_compact_appendix.docx"
TABLES = PROJECT_ROOT / "outputs" / "tables"
PROCESSED = PROJECT_ROOT / "data" / "processed"
FRAME_ROWS = 10172
SAMPLE_ROWS = 9239

LABEL_TEXT = {
    "mod_opinion": "Modified audit opinion (narrow)",
    "mod_opinion_wide": "Modified audit opinion (wide)",
    "violation_any_t1": "Any violation announced in t+1",
    "violation_any_t1_strict": "Any violation announced in t+1",
    "violation_disclosure_t1": "Disclosure violation announced in t+1",
    "violation_disclosure_t1_strict": "Disclosure violation announced in t+1",
}
MODEL_TEXT = {"logit": "Logistic", "hgb": "Gradient boosting"}
DEFINITION_TEXT = {"loose": "Calendar-year t+1", "strict": "Strict gate"}


def _interval(value: float, low: float, high: float) -> str:
    return f"{value:+.3f} [{low:+.3f}, {high:+.3f}]"


def load_deltas(path: Path) -> list[list[str]]:
    """Return one row per label and model, with both paired increments filled."""

    table = pd.read_csv(path)
    table = table[table["feature_set"].str.startswith("delta_")]
    definition = DEFINITION_TEXT["strict" if path.stem.endswith("_strict") else "loose"]
    cells: dict[tuple[str, str], dict[str, str]] = {}
    for _, row in table.iterrows():
        key = (row["label"], row["model"])
        bucket = cells.setdefault(key, {"fused": "", "text": ""})
        kind = "fused" if row["feature_set"] == "delta_fused_vs_finance" else "text"
        bucket[kind] = _interval(row["oof_auc"], row["oof_auc_lo"], row["oof_auc_hi"])
    rows = [
        [definition, LABEL_TEXT[label], MODEL_TEXT[model], bucket["fused"], bucket["text"]]
        for (label, model), bucket in cells.items()
    ]
    rows.sort(key=lambda item: (item[0] != "Calendar-year t+1", item[1], item[2]))
    return rows


def delta_table() -> list[list[str]]:
    loose = load_deltas(TABLES / "event_supervised_metrics.csv")
    strict = load_deltas(TABLES / "event_supervised_metrics_strict.csv")
    rows = loose + strict
    if len(rows) != 16:
        raise SystemExit(f"expected 16 paired increments, found {len(rows)}")
    return rows


def attrition_counts() -> dict[str, int]:
    """Recompute the step-by-step attrition and assert that it closes."""
    features = pd.read_csv(PROCESSED / "feature_table.csv", dtype={"symbol": str})
    if len(features) != FRAME_ROWS:
        raise SystemExit(f"frame has {len(features)} rows, expected {FRAME_ROWS}")
    finance_cols = [
        "roa",
        "leverage",
        "revenue_growth",
        "ocf_to_assets",
        "receivables_turnover",
        "accruals_to_assets",
    ]
    text_cols = ["readability", "sentiment_balance", "uncertainty_ratio"]
    has_score = features["m_score"].notna()
    has_finance = features[finance_cols].notna().all(axis=1)
    has_text = features[text_cols].notna().all(axis=1)
    step1 = features[has_score]
    step2 = step1[has_finance[step1.index]]
    step3 = step2[has_text[step2.index]]
    if len(step3) != SAMPLE_ROWS:
        raise SystemExit(f"attrition closes at {len(step3)}, expected {SAMPLE_ROWS}")
    return {
        "frame": FRAME_ROWS,
        "score": FRAME_ROWS - len(step1),
        "finance": len(step1) - len(step2),
        "text": len(step2) - len(step3),
        "sample": len(step3),
    }


def attrition_rows() -> list[list[str]]:
    counts = attrition_counts()
    return [
        ["0", "Manufacturing firm-year frame, 2021-2023", "-", f"{counts['frame']:,}"],
        [
            "1",
            "Beneish M-Score computable (previous-year statement available)",
            f"{counts['score']:,}",
            f"{FRAME_ROWS - counts['score']:,}",
        ],
        [
            "2",
            "All six financial features non-missing",
            f"{counts['finance']:,}",
            f"{FRAME_ROWS - counts['score'] - counts['finance']:,}",
        ],
        [
            "3",
            "All three MD&A features non-missing",
            f"{counts['text']:,}",
            f"{counts['sample']:,}",
        ],
        ["", "Analysis sample (3,488 firms)", "-", f"{counts['sample']:,}"],
    ]


def label_rows() -> list[list[str]]:
    events = pd.read_csv(PROCESSED / "event_table.csv", dtype={"symbol": str})
    strict = pd.read_csv(TABLES / "event_strict_diagnostics.csv").set_index("label")
    total = len(events)

    def count(name: str) -> str:
        return f"{int(events[name].sum()):,} ({events[name].mean() * 100:.1f}%)"

    def gated(name: str) -> str:
        loose = int(strict.loc[name, "n_loose"])
        kept = int(strict.loc[name, "n_strict"])
        return f"{kept:,} of {loose:,} ({kept / total * 100:.1f}%)"

    return [
        ["Modified audit opinion (narrow)", "Any opinion other than unqualified in t", count("mod_opinion"), "Not applicable"],
        [
            "Modified audit opinion (wide)",
            "Also counts unqualified opinions with an explanatory paragraph in t",
            count("mod_opinion_wide"),
            "Not applicable",
        ],
        [
            "Any violation announced in t+1",
            "Any STK_Violation announcement dated in the calendar year after the report",
            count("violation_any_t1"),
            gated("violation_any_t1_strict"),
        ],
        [
            "Disclosure violation announced in t+1",
            "Delayed disclosure, misstatement, material omission, fictitious profit or assets",
            count("violation_disclosure_t1"),
            gated("violation_disclosure_t1_strict"),
        ],
    ]


DEFAULT_SAMPLE_SENTENCE = (
    "Table B5 reports the resulting attrition: {score:,} firm-years drop because the Beneish score cannot be "
    "computed, {finance} more because a financial ratio is undefined, and {text:,} because no usable MD&A text "
    "exists. Because the frame is defined by the industry code rather than by exchange membership, it also "
    "contains Beijing Stock Exchange listings together with their pre-listing NEEQ years: 202 firms and 408 "
    "firm-years (4.4% of the analysis sample) carry a BSE series code, so Chinese A-share manufacturing here "
    "means manufacturing firms with a CSMAR series code rather than exchange-listed A-shares only."
)

FULL_SAMPLE_SENTENCE = (
    "The attrition runs from {frame:,} frame rows to {sample:,} analysed firm-years: {score:,} drop because the "
    "Beneish score cannot be computed, {finance} because a financial ratio is undefined and {text:,} because no "
    "usable MD&A text exists. The frame is defined by the industry code rather than by exchange membership, so "
    "it also contains Beijing Stock Exchange listings and their pre-listing NEEQ years: 202 firms and 408 "
    "firm-years (4.4% of the analysis sample) carry a BSE series code."
)

SCORE_SENTENCE = (
    "The score itself is left unwinsorised: in the analysis sample it ranges from -387.1 to 9,182.9, and 33 "
    "firm-years (0.4%) exceed an absolute value of 20. Those tails belong to the benchmark rather than to the "
    "features, which are clipped at the 1st and 99th percentiles before standardisation."
)

SUPERVISED_SENTENCE = (
    "Table B4 lists the paired increment for every label and model. Under the calendar-year label the fused "
    "increment is positive in 8 of 8 cells and no interval excludes zero; under the strict gate 6 of 8 remain "
    "positive, the two exceptions sitting on the disclosure label (-0.002 [-0.011, +0.005] for the logistic "
    "model and -0.001 [-0.011, +0.009] for gradient boosting), and again no interval excludes zero. The two "
    "audit-opinion labels are not timing-gated, so their rows repeat across the two definitions. The paired "
    "text-block increment is negative in every one of the sixteen listed cells, with an interval excluding zero "
    "in each of them."
)

SUPERVISED_SENTENCE_FULL = SUPERVISED_SENTENCE.replace("Table B4 lists", "The supplementary tables list")

OVERLAP_SENTENCE = (
    "Both overlap figures are intersections divided by the size of one top decile (|A and B| / |A|); because "
    "every decile holds the same number of firm-years the two directions coincide, and the figure is the share "
    "of a top decile recovered by the other ranking rather than a Jaccard index over the union."
)

APPENDIX_INTRO_OLD = "summarises in a single sentence."
APPENDIX_INTRO_NEW = (
    "summarises in a single sentence; B.3 adds the sample attrition, the outcome-label definitions and the "
    "paired increments for every label and model."
)


def _append(document: Document, anchor: str, sentence: str) -> str:
    for paragraph in document.paragraphs:
        if anchor in paragraph.text:
            return "applied" if append_sentence(paragraph, sentence) else "skipped"
    return "miss"


def apply_compact() -> dict[str, str]:
    document = Document(str(COMPACT))
    counts = attrition_counts()
    result = {
        "sample": _append(
            document,
            "pre-listing OTC (NEEQ) years of Beijing Stock Exchange firms that CNINFO does not archive.",
            DEFAULT_SAMPLE_SENTENCE.format(**counts),
        ),
        "score": _append(document, "neither ever enters model training.", SCORE_SENTENCE),
        "supervised": _append(
            document,
            "small and never statistically distinguishable from zero.",
            SUPERVISED_SENTENCE,
        ),
        "overlap": _append(document, "0.797", OVERLAP_SENTENCE),
    }
    document.save(str(COMPACT))
    return result


def apply_full() -> dict[str, str]:
    document = Document(str(FULL))
    counts = attrition_counts()
    result = {
        "sample": _append(
            document,
            "pre-listing OTC (NEEQ) years of Beijing Stock Exchange firms that CNINFO does not archive.",
            FULL_SAMPLE_SENTENCE.format(**counts),
        ),
        "score": _append(document, "neither ever enters model training.", SCORE_SENTENCE),
        "supervised": _append(
            document,
            "small and never statistically distinguishable from zero.",
            SUPERVISED_SENTENCE_FULL,
        ),
        "overlap": _append(document, "0.797", OVERLAP_SENTENCE),
    }
    document.save(str(FULL))
    return result


def apply_appendix() -> dict[str, str]:
    document = Document(str(APPENDIX))
    result = {"intro": "miss"}
    texts = paragraph_texts(APPENDIX)
    if any(APPENDIX_INTRO_NEW in text for text in texts):
        result["intro"] = "skipped"
    else:
        for paragraph in document.paragraphs:
            if replace_text(paragraph, APPENDIX_INTRO_OLD, APPENDIX_INTRO_NEW):
                result["intro"] = "applied"
                break
    if any(text.startswith("Table B4.") for text in texts):
        result["tables"] = "skipped"
    else:
        anchor = None
        for paragraph in document.paragraphs:
            if "scripts/compare_runs.py reproduces the comparison reported here." in paragraph.text:
                anchor = paragraph
                break
        if anchor is None:
            result["tables"] = "miss"
        else:
            labels = (
                "Calendar-year t+1 labels: a t+1 announcement is any violation dated in the calendar year after "
                "the fiscal year, whether or not it post-dates the annual report."
            )
            blocks = [
                ("heading", "Appendix B.3 Additional tables"),
                ("text", labels),
                (
                    "caption",
                    "Table B4. Paired increments of the fused and the text block over the financial block: "
                    "out-of-fold AUC under firm-grouped five-fold cross-validation, with 95% bootstrap intervals "
                    "in brackets.",
                ),
                (
                    "table",
                    ["Definition", "Outcome label", "Model", "Fused - finance", "Text - finance"],
                    delta_table(),
                ),
                (
                    "caption",
                    "Table B5. Attrition from the manufacturing firm-year frame to the analysis sample.",
                ),
                (
                    "table",
                    ["Step", "Rule applied", "Firm-years dropped", "Firm-years retained"],
                    attrition_rows(),
                ),
                (
                    "caption",
                    "Table B6. Definitions and counts of the four external outcome labels.",
                ),
                (
                    "table",
                    ["Outcome label", "Definition", "Calendar-year t+1", "Strict gate"],
                    label_rows(),
                ),
            ]
            insert_block_after(anchor, document, blocks)
            result["tables"] = "applied"
    document.save(str(APPENDIX))
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Add the Phase 4 tables and sentences to the manuscript.")
    parser.add_argument("--apply", action="store_true", help="write the changes (default is a dry run)")
    args = parser.parse_args()
    if not args.apply:
        rows = delta_table()
        print(f"[dry-run] Table B4 would list {len(rows)} paired increments")
        print(f"[dry-run] Table B5 would list {len(attrition_rows())} attrition steps")
        print(f"[dry-run] Table B6 would list {len(label_rows())} outcome labels")
        return 0
    for name, outcome in apply_compact().items():
        print(f"[compact] {name}: {outcome}")
    for name, outcome in apply_appendix().items():
        print(f"[appendix] {name}: {outcome}")
    for name, outcome in apply_full().items():
        print(f"[full] {name}: {outcome}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
