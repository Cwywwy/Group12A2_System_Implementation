# -*- coding: utf-8 -*-
"""
patch_manuscript_v03.py
Author: Group12A2 DSW Team
Purpose: Apply the v0.3 consistency fixes to the English manuscript sources,
         assemble the single submission file (body plus appendix) and export
         the PDF. Every replacement is anchored on a verbatim sentence, and a
         replacement that does not match exactly once aborts the run. Long
         paragraphs are rewritten whole through an old_prefix anchor; the
         numbers they carry are checked against the Phase 2 tables before
         anything is written.
Module: scripts

Usage:
    python scripts/patch_manuscript_v03.py --dry-run     # report matches only
    python scripts/patch_manuscript_v03.py --apply       # rewrite the sources
    python scripts/patch_manuscript_v03.py --merge       # build the merged copy
    python scripts/patch_manuscript_v03.py --pdf         # export the PDF

The engine lives in src.reporting.manuscript_revision, the docx primitives in
src.reporting.docx_patch, the number audit in src.reporting.revision_checks
and the PDF export in src.reporting.pdf_export; this file holds the fix list
and the command line.

Revision History
----------------
2026-11-24  initial version: v0.3 text closure, merged deliverable, PDF export.
2026-11-24  phase 2: whole-paragraph rewrites for the strict-timing labels, the
            lexicon control and the DEPI disclosure, with number verification.
2026-11-24  thinned: the engine, checks and export moved into src.reporting.
"""
import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.reporting.docx_patch import merge_documents  # noqa: E402
from src.reporting.manuscript_revision import apply_fixes  # noqa: E402
from src.reporting.pdf_export import export_pdf  # noqa: E402
from src.reporting.revision_checks import check_v03_numbers  # noqa: E402

BASE = PROJECT_ROOT / "11.23base"
FULL = BASE / "Group12A2_Final_EN_corrected.docx"
COMPACT = BASE / "Group12A2_Final_EN_corrected_compact.docx"
APPENDIX = BASE / "Group12A2_Final_EN_corrected_compact_appendix.docx"
MERGED = PROJECT_ROOT / "outputs" / "manuscript" / "Group12A2_Final_EN_v0.3.docx"
MERGED_PDF = PROJECT_ROOT / "outputs" / "manuscript" / "Group12A2_Final_EN_v0.3.pdf"

BOTH = ("full", "compact")
DOCUMENTS = {"full": FULL, "compact": COMPACT, "appendix": APPENDIX}

# Each fix: id, target files, verbatim anchor, replacement.
FIXES = [
    dict(
        id="A1a",
        files=BOTH,
        old="and an M-Score of 14.3, that is, a firm the Beneish proxy does not flag.",
        new=(
            "and an M-Score of 14.3, so the Beneish proxy flags this firm-year as well, under "
            "both the legacy and the recalibrated definition."
        ),
    ),
    dict(
        id="A1b",
        files=BOTH,
        old=(
            "The local explanation therefore illustrates the inverse relation documented in "
            "§5.2 rather than corroborating the benchmark: the Isolation Forest responds to "
            "statement shape, while the M-Score weights the same statements differently and, in "
            "this sample, ranks such firms lower."
        ),
        new=(
            "This case therefore corroborates the benchmark rather than contradicting it: the "
            "ranking and the M-Score agree, and the same firm-year carries a disclosure "
            "violation announced in t+1, an outcome that neither the proxy nor the "
            "modified-opinion label is designed to rank."
        ),
    ),
    dict(
        id="A2",
        files=BOTH,
        old="Spearman correlation with the Beneish M-Score of 0.009, p = 0.409",
        new="Spearman correlation with the Beneish M-Score of -0.007, p = 0.528",
    ),
    dict(
        id="A3",
        files=BOTH,
        old="and the text-only model 0.91 and 1.10, that is, below chance at both thresholds.",
        new=(
            "and the text-only model 0.91 at the top-10% and 1.10 at the top-5%, that is, "
            "above chance at the narrower threshold but not at the wider one."
        ),
    ),
    dict(
        id="A4",
        files=BOTH,
        old=(
            "and its top-10% enrichment is 1.57 under the legacy cut-off (1.96 recalibrated), "
            "barely above chance."
        ),
        new=(
            "and its top-10% enrichment is 1.57 under the legacy cut-off (1.96 recalibrated), "
            "roughly 1.6 to 2.0 times chance, falling to 1.49 and 1.78 at the top-15% threshold."
        ),
    ),
    dict(
        id="A5",
        files=BOTH,
        old=(
            "and the supervised increment of the fused block stays within 0.018 of zero and is "
            "negative wherever it is distinguishable from it."
        ),
        new=(
            "and the supervised increment of the fused block stays within 0.018 of zero with "
            "every confidence interval covering zero, while the text block used on its own is "
            "significantly worse than the financial block wherever the difference is "
            "distinguishable."
        ),
    ),
    dict(
        id="A6",
        files=("appendix",),
        old=(
            "They are measurement checks, not new findings, and nothing in them is used to "
            "support or to overturn the answer to RQ1."
        ),
        new=(
            "They are measurement checks rather than new findings: they show how far the main "
            "numbers travel, and they neither establish nor overturn the answer to RQ1."
        ),
    ),
    dict(
        id="A8",
        files=("appendix",),
        old=(
            "A character n-gram TF-IDF model was also run on the same text and reaches 0.63 to "
            "0.81 against the dictionary features at 0.48 to 0.57; it is a text-representation "
            "comparison rather than a robustness check of the pipeline, so it is recorded in the "
            "project notes and not tabulated here."
        ),
        new=(
            "A character n-gram TF-IDF representation was also tried as an alternative text "
            "measure. It was not run through the same evaluation harness as the dictionary "
            "features, so its scores are not comparable with the ones reported here, and it is "
            "not used anywhere in the paper."
        ),
    ),
    dict(
        id="A9a",
        files=BOTH,
        old=(
            "The legacy definition follows Beneish (1999) literally and treats M > -1.78 as a "
            "risk flag;"
        ),
        new=(
            "The legacy definition applies the eight published Beneish (1999) coefficients with "
            "one implementation difference: the statement set used here carries no "
            "depreciation-expense field, so the depreciation index (DEPI) is neutralised at 1.0 "
            "and drops out of the score. The legacy rule treats M > -1.78 as a risk flag;"
        ),
    ),
    dict(
        id="A9b",
        files=BOTH,
        old="the conventional M > -1.78 threshold and a sample-calibrated top-decile threshold.",
        new=(
            "the legacy M > -1.78 threshold and a sample-calibrated top-decile threshold. The "
            "score is a modified rather than a literal Beneish score: the depreciation index is "
            "neutralised at 1.0 (see Section 5.1)."
        ),
    ),
    dict(
        id="A9c",
        files=BOTH,
        old="literal -1.78",
        new="legacy -1.78",
        all_occurrences=True,
    ),
    dict(
        id="A9d",
        files=("full", "compact", "appendix"),
        old="using the conventional Beneish cut-off",
        new="using the legacy Beneish cut-off",
        optional=True,
    ),
    dict(
        id="A9e",
        files=BOTH,
        old="The conventional Beneish cut-off is not plotted here.",
        new="The legacy Beneish cut-off is not plotted here.",
    ),
    dict(
        id="A9f",
        files=("full", "appendix"),
        old="only the conventional Beneish threshold",
        new="only the legacy Beneish threshold",
    ),
    dict(
        id="A9g",
        files=("appendix",),
        old="under both the conventional and the recalibrated cut-off",
        new="under both the legacy and the recalibrated cut-off",
    ),
    dict(
        id="A10",
        files=BOTH,
        old="the textual group for 33.8%. The three most important global features",
        new=(
            "the textual group for 33.8%. Six features against three put the average share per "
            "feature at 11.0% and 11.3%, so the two families carry almost the same average "
            "weight. The three most important global features"
        ),
    ),
    dict(
        id="A11a",
        files=BOTH,
        old="(they largely agree because the fused model is dominated by financial features)",
        new="(they largely agree because the fused ranking is anchored by the financial block)",
    ),
    dict(
        id="A11b",
        files=BOTH,
        old="a largely orthogonal signal",
        new="an almost uncorrelated signal",
    ),
    dict(
        id="A12",
        files=BOTH,
        old=(
            "The explained output is oriented so that higher values consistently indicate "
            "greater abnormality. Global results report"
        ),
        new=(
            "The explained output is oriented so that higher values consistently indicate "
            "greater abnormality. SHAP values are reported in the model's own output units "
            "(Isolation Forest path-length deviations): the sign is interpretable, and the "
            "values are not additive with the 0-1 anomaly scores reported in the tables. "
            "Global results report"
        ),
    ),
    dict(
        id="A14",
        files=BOTH,
        old="of which none of eight confidence intervals exclude zero",
        new="of which none excludes zero",
    ),
    # ---- Phase 2: evidence closure (strict timing, lexicon control, DEPI) ----
    dict(
        id="P1c",
        files=("compact",),
        old_prefix="The Beneish M-Score is only a proxy for earnings manipulation",
        new=(
            "The Beneish M-Score is only a proxy for earnings manipulation, and the "
            "preceding subsections have shown it is a poor one in this sample. We therefore "
            "validate the scores against two real CSMAR outcomes: the audit opinion on the "
            "fiscal-year report (FIN_Audit) and exchange violation announcements "
            "(STK_Violation_Main). The narrow opinion label equals one for any opinion other "
            "than unqualified; the wide label also counts unqualified opinions with an "
            "explanatory paragraph. The violation label equals one when an announcement falls "
            "in t+1. Sample counts are reported for both all violations and the "
            "disclosure-related subset, whereas the ranking tests in Table 5.2 use the "
            "narrower subset (delayed disclosure, misstatement, material omission, fictitious "
            "profit or assets) and extend the window to 2025. A calendar-year t+1 label is not "
            "automatically forward-looking: fiscal-year reports are normally published in "
            "April of t+1, so an announcement dated January to March of t+1 precedes the "
            "report it is meant to predict. The appendix therefore also reports a strict "
            "definition that keeps a t+1 announcement only when it post-dates the "
            "fiscal-year report's disclosure date; the gate removes 422 of the 1,965 "
            "any-violation labels (21.5%) and 297 of the 1,337 disclosure labels (22.2%), "
            "leaving 1,543 and 1,040 events. It leaves the conclusions unchanged and "
            "slightly sharpens them: the finance-only score ranks disclosure violations at "
            "AUC 0.600 [0.584, 0.619] against 0.596 under the calendar-year definition, the "
            "fused score reaches 0.590, and neither the text block nor the supervised "
            "comparison improves on the financial block."
        ),
    ),
    dict(
        id="P1f",
        files=("full",),
        old_prefix="The Beneish M-Score is only a proxy for earnings manipulation",
        new=(
            "The Beneish M-Score is only a proxy for earnings manipulation, and the "
            "preceding subsections have shown it is a poor one in this sample. We therefore "
            "validate the scores against two real CSMAR outcomes: the audit opinion on the "
            "fiscal-year report (FIN_Audit) and exchange violation announcements "
            "(STK_Violation_Main). The narrow opinion label equals one for any opinion other "
            "than unqualified; the wide label also counts unqualified opinions with an "
            "explanatory paragraph. The violation label equals one when an announcement falls "
            "in t+1. Sample counts are reported for both all violations and the "
            "disclosure-related subset, whereas the ranking tests in Table 5.5 use the "
            "narrower subset (delayed disclosure, misstatement, material omission, fictitious "
            "profit or assets) and extend the window to 2025. A calendar-year t+1 label is not "
            "automatically forward-looking: fiscal-year reports are normally published in "
            "April of t+1, so an announcement dated January to March of t+1 precedes the "
            "report it is meant to predict. Section 5.8 therefore also reports a strict "
            "definition that keeps a t+1 announcement only when it post-dates the "
            "fiscal-year report's disclosure date; the gate removes 422 of the 1,965 "
            "any-violation labels (21.5%) and 297 of the 1,337 disclosure labels (22.2%), "
            "leaving 1,543 and 1,040 events. It leaves the conclusions unchanged and "
            "slightly sharpens them: the finance-only score ranks disclosure violations at "
            "AUC 0.600 [0.584, 0.619] against 0.596 under the calendar-year definition, the "
            "fused score reaches 0.590, and neither the text block nor the supervised "
            "comparison improves on the financial block."
        ),
    ),
    dict(
        id="P2c",
        files=("compact",),
        old_prefix="Table 5.3 asks the complementary supervised question",
        new=(
            "Table 5.3 asks the complementary supervised question: given the labels, does the "
            "text block add rank information beyond the financial block? Text alone is weaker "
            "than finance alone (0.680 versus 0.865 for modified opinions), so the issue is "
            "complementarity. Under firm-grouped cross-validation the logistic model reaches "
            "0.865 on financial features and 0.866 fused, an increment of +0.002 "
            "[-0.013, +0.014]; gradient boosting gives +0.012 [-0.005, +0.027], and on the "
            "strict disclosure-violation label the increments are -0.002 [-0.011, +0.005] and "
            "-0.001 [-0.011, +0.009]. Across the 8 label-by-model combinations the increment "
            "is positive in 6 and its interval excludes zero in 0 - small and never "
            "statistically distinguishable from zero."
        ),
    ),
    dict(
        id="P2f",
        files=("full",),
        old_prefix="Table 5.6 asks the complementary supervised question",
        new=(
            "Table 5.6 asks the complementary supervised question: given the labels, does the "
            "text block add rank information beyond the financial block? Text alone is weaker "
            "than finance alone (0.680 versus 0.865 for modified opinions), so the issue is "
            "complementarity. Under firm-grouped cross-validation the logistic model reaches "
            "0.865 on financial features and 0.866 fused, an increment of +0.002 "
            "[-0.013, +0.014]; gradient boosting gives +0.012 [-0.005, +0.027], and on the "
            "strict disclosure-violation label the increments are -0.002 [-0.011, +0.005] and "
            "-0.001 [-0.011, +0.009]. Across the 8 label-by-model combinations the increment "
            "is positive in 6 and its interval excludes zero in 0 - small and never "
            "statistically distinguishable from zero."
        ),
    ),
    dict(
        id="P3",
        files=("appendix",),
        old_prefix="Two of the extensions returned nothing",
        new=(
            "Two of the extensions returned nothing, and both are worth stating. Adding 42 "
            "positive and 51 negative industry-specific terms to the sentiment lexicon leaves "
            "the text measure where it was (rank correlation against the M-Score -0.027 "
            "before, -0.028 after; AUC 0.537 against 0.539). Restricting the sample to the "
            "four industries that supply most disclosure events (14,937 firm-years, 341 "
            "events) gives a finance-only AUC of 0.776 and an M-Score AUC of 0.271, "
            "indistinguishable from the full non-financial frame. Two further checks tighten "
            "the forward-looking claim instead of widening it. Requiring a t+1 violation "
            "announcement to post-date the fiscal-year report removes 422 of the 1,965 "
            "any-violation labels (21.5%) and 297 of the 1,337 disclosure labels (22.2%); on "
            "the surviving labels the finance-only score ranks disclosure violations at AUC " 
            "0.600 [0.584, 0.619] against 0.596 under the calendar-year definition, so the "
            "timing objection does not weaken the result. Holding the financial block, the "
            "sample and the model fixed and swapping only the text measurement gives a fused "
            "rank correlation of -0.021 under the first dictionary and -0.018 under the "
            "second (text-only -0.048 and -0.026; readability is identical under both, so the "
            "same MD&A text is scored), so the movement documented in B.2 is not a lexicon "
            "effect."
        ),
    ),
    dict(
        id="P4a",
        files=("appendix",),
        old_prefix="Table B3 summarises the two specifications.",
        new=(
            "Table B3 summarises the two specifications. The lexicon was replaced by the full "
            "Chinese financial sentiment list of Yao et al. (2021), uncertainty terms were "
            "expanded, substring counting was replaced by jieba token matching, and the "
            "single threshold was supplemented by a sample-calibrated top-decile definition: "
            "the sentiment measure matches 111.3 terms per 1,000 MD&A tokens against 13.4 in "
            "the first specification (8.3 times denser). The substantive answer does not "
            "move: the text-only rank correlation goes from -0.030 to -0.026, the fused "
            "correlation from 0.103 to -0.018, and the autoencoder from 0.012 (p = 0.272) to "
            "-0.007 (p = 0.528); under the recalibrated benchmark the text-only top-10% "
            "enrichment falls from 1.07 to 0.91. One caveat applies to that comparison: the "
            "first specification was estimated on the earlier financial intermediate, in "
            "which the annual statement rows were merged positionally, so a row could carry a "
            "neighbouring year's statement items. That defect was repaired before the main "
            "results were produced. Holding the repaired financial block, the sample and the "
            "model fixed and swapping only the text measurement gives a fused rank "
            "correlation of -0.021 with the first dictionary and -0.018 with the second, and "
            "a text-only correlation of -0.048 and -0.026; readability is identical under "
            "both, so the same MD&A text is being scored. The movement in Table B3 therefore "
            "reflects the financial-data repair rather than the lexicon. With that caveat, "
            "the second specification removes the two most obvious measurement objections "
            "while leaving RQ1 answered negatively. Both specifications are retained: the "
            "frozen v0.1 lexicons, the cached MD&A text, and the archived result tables are "
            "stored in the repository, and scripts/compare_runs.py reproduces the comparison "
            "reported here."
        ),
    ),
    dict(
        id="P4b",
        files=("full",),
        old_prefix="Table 5.4 summarises the two specifications.",
        new=(
            "Table 5.4 summarises the two specifications. The lexicon was replaced by the full "
            "Chinese financial sentiment list of Yao et al. (2021), uncertainty terms were "
            "expanded, substring counting was replaced by jieba token matching, and the "
            "single threshold was supplemented by a sample-calibrated top-decile definition: "
            "the sentiment measure matches 111.3 terms per 1,000 MD&A tokens against 13.4 in "
            "the first specification (8.3 times denser). The substantive answer does not "
            "move: the text-only rank correlation goes from -0.030 to -0.026, the fused "
            "correlation from 0.103 to -0.018, and the autoencoder from 0.012 (p = 0.272) to "
            "-0.007 (p = 0.528); under the recalibrated benchmark the text-only top-10% "
            "enrichment falls from 1.07 to 0.91. One caveat applies to that comparison: the "
            "first specification was estimated on the earlier financial intermediate, in "
            "which the annual statement rows were merged positionally, so a row could carry a "
            "neighbouring year's statement items. That defect was repaired before the main "
            "results were produced. Holding the repaired financial block, the sample and the "
            "model fixed and swapping only the text measurement gives a fused rank "
            "correlation of -0.021 with the first dictionary and -0.018 with the second, and "
            "a text-only correlation of -0.048 and -0.026; readability is identical under "
            "both, so the same MD&A text is being scored. The movement in Table 5.4 therefore "
            "reflects the financial-data repair rather than the lexicon. With that caveat, "
            "the second specification removes the two most obvious measurement objections "
            "while leaving RQ1 answered negatively. Both specifications are retained: the "
            "frozen v0.1 lexicons, the cached MD&A text, and the archived result tables are "
            "stored in the repository, and scripts/compare_runs.py reproduces the comparison "
            "reported here."
        ),
    ),
    dict(
        id="P5",
        files=("appendix",),
        old_prefix="The first specification used a small bootstrap sentiment dictionary",
        new=(
            "The first specification used a small bootstrap sentiment dictionary, substring "
            "matching, and only the legacy Beneish threshold. The second specification "
            "replaced the bootstrap list with the Yao et al. (2021) financial sentiment "
            "lexicon, used Jieba token matching, expanded the uncertainty dictionary, and "
            "added a sample-calibrated top-decile Beneish benchmark. The comparison is "
            "retained to show whether the negative result against the Beneish proxy was "
            "driven by the initial text-measurement or benchmark choices. Both specifications "
            "score a modified Beneish score rather than a literal one: the statement set "
            "carries no depreciation-expense field, so the depreciation index (DEPI) is "
            "neutralised at 1.0 and drops out of the sum (Section 5.1). The second "
            "specification produces substantially more sentiment matches per 1,000 tokens, "
            "but the rank correlations remain very similar. This strengthens the conclusion "
            "that the measured MD&A features do not improve the unsupervised "
            "Beneish-oriented ranking in this sample; it does not establish that all forms of "
            "textual information lack value."
        ),
    ),
]

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="report matches, write nothing")
    parser.add_argument("--apply", action="store_true", help="rewrite the three sources")
    parser.add_argument("--merge", action="store_true", help="assemble the merged copy")
    parser.add_argument("--pdf", action="store_true", help="export the merged PDF")
    args = parser.parse_args(argv)
    if not any([args.dry_run, args.apply, args.merge, args.pdf]):
        parser.error("choose at least one of --dry-run, --apply, --merge, --pdf")
    problems = 0
    if args.dry_run or args.apply:
        number_problems = check_v03_numbers()
        if number_problems:
            print("[numbers] the text does not match the Phase 2 tables:")
            for item in number_problems:
                print(f"  - {item}")
            return 2
        print("[numbers] all quoted Phase 2 numbers match their tables")
        problems = apply_fixes(FIXES, DOCUMENTS, apply=args.apply)
    if args.merge:
        merged = merge_documents(COMPACT, APPENDIX, MERGED, separate_line="page-break")
        print(f"[merge] {merged}")
    if args.pdf:
        pages = export_pdf(MERGED, MERGED_PDF)
        print(f"[pdf] {MERGED_PDF} ({pages} pages)")
    if problems:
        print(f"[result] {problems} unmatched or ambiguous anchors")
        return 2
    print("[result] all anchors matched exactly once")
    return 0


if __name__ == "__main__":
    sys.exit(main())
