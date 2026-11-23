# -*- coding: utf-8 -*-
"""
patch_manuscript_v03.py
Author: Group12A2 DSW Team
Purpose: Apply the v0.3 consistency fixes to the English manuscript sources,
         assemble the single submission file (body plus appendix) and export
         the PDF. Every replacement is anchored on a verbatim sentence, and a
         replacement that does not match exactly once aborts the run.
Module: scripts

Usage:
    python scripts/patch_manuscript_v03.py --dry-run     # report matches only
    python scripts/patch_manuscript_v03.py --apply       # rewrite the sources
    python scripts/patch_manuscript_v03.py --merge       # build the merged copy
    python scripts/patch_manuscript_v03.py --pdf         # export the PDF

Revision History
----------------
2026-11-24  initial version: v0.3 text closure, merged deliverable, PDF export.
"""
import argparse
import copy
import sys
from pathlib import Path

import docx
from docx.oxml.ns import qn

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BASE = PROJECT_ROOT / "11.23base"
FULL = BASE / "Group12A2_Final_EN_corrected.docx"
COMPACT = BASE / "Group12A2_Final_EN_corrected_compact.docx"
APPENDIX = BASE / "Group12A2_Final_EN_corrected_compact_appendix.docx"
MERGED = PROJECT_ROOT / "outputs" / "manuscript" / "Group12A2_Final_EN_v0.3.docx"
MERGED_PDF = PROJECT_ROOT / "outputs" / "manuscript" / "Group12A2_Final_EN_v0.3.pdf"

BOTH = ("full", "compact")

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
]


def set_para_text(paragraph, value):
    """Write text into a paragraph while keeping the first run's formatting."""
    runs = paragraph.runs
    if not runs:
        paragraph.add_run(value)
        return
    runs[0].text = value
    for run in runs[1:]:
        run.text = ""


def _documents():
    return {"full": FULL, "compact": COMPACT, "appendix": APPENDIX}


def apply_fixes(apply: bool) -> int:
    problems = 0
    for tag, path in _documents().items():
        if not path.exists():
            print(f"[miss] {tag}: {path} not found")
            problems += 1
            continue
        document = docx.Document(path)
        expected = [f for f in FIXES if tag in f["files"]]
        applied = set()
        for paragraph in document.paragraphs:
            text = paragraph.text
            if not text.strip():
                continue
            changed = text
            hit_here = []
            for fix in expected:
                already = fix["new"] in changed
                if fix["old"] not in changed:
                    if already:
                        applied.add(fix["id"])
                    continue
                count = changed.count(fix["old"])
                if count > 1 and not fix.get("all_occurrences"):
                    print(f"[skip] {tag} {fix['id']}: anchor occurs {count}x in one paragraph")
                    problems += 1
                    continue
                changed = changed.replace(fix["old"], fix["new"])
                hit_here.append(fix["id"])
            if hit_here:
                if apply:
                    set_para_text(paragraph, changed)
                applied.update(hit_here)
                print(f"[{'edit' if apply else 'dry '}] {tag}: {', '.join(sorted(hit_here))}")
        missing = [f["id"] for f in expected if f["id"] not in applied and not f.get("optional")]
        if missing:
            print(f"[miss] {tag}: no match for {', '.join(missing)}")
            problems += len(missing)
        if apply:
            document.save(path)
            print(f"[save] {path}")
    return problems


def merge_documents() -> None:
    base = docx.Document(COMPACT)
    appendix = docx.Document(APPENDIX)
    body = base.element.body
    sect_pr = body.find(qn("w:sectPr"))
    page_break = docx.Document()
    break_paragraph = page_break.add_paragraph()._p
    run = break_paragraph.makeelement(qn("w:r"), {})
    br = break_paragraph.makeelement(qn("w:br"), {qn("w:type"): "page"})
    run.append(br)
    break_paragraph.append(run)
    body.insert(len(body) - 1 if sect_pr is not None else len(body), copy.deepcopy(break_paragraph))
    for child in list(appendix.element.body):
        if child.tag == qn("w:sectPr"):
            continue
        body.insert(len(body) - 1 if sect_pr is not None else len(body), copy.deepcopy(child))
    MERGED.parent.mkdir(parents=True, exist_ok=True)
    base.save(MERGED)
    merged = docx.Document(MERGED)
    body_paras = [p.text for p in docx.Document(COMPACT).paragraphs]
    appendix_paras = [p.text for p in docx.Document(APPENDIX).paragraphs]
    merged_paras = [p.text for p in merged.paragraphs]
    expected = body_paras + appendix_paras
    got = [t for t in merged_paras if t.strip()]
    want = [t for t in expected if t.strip()]
    if got != want:
        print(f"[warn] merged text differs from the two sources ({len(got)} vs {len(want)} paragraphs)")
        for index, (a, b) in enumerate(zip(want, got)):
            if a != b:
                print(f"  first difference at {index}: {a[:60]!r} / {b[:60]!r}")
                break
        raise SystemExit(1)
    print(f"[merge] {MERGED} ({len(merged_paras)} paragraphs, text identical to sources)")


def export_pdf() -> None:
    try:
        import win32com.client  # type: ignore
    except ImportError:
        print("[pdf] pywin32 is not available; export the PDF from Word manually")
        raise SystemExit(1)
    word = win32com.client.Dispatch("Word.Application")
    word.Visible = False
    try:
        document = word.Documents.Open(str(MERGED))
        document.SaveAs(str(MERGED_PDF), FileFormat=17)
        pages = document.ComputeStatistics(2)
        document.Close(False)
    finally:
        word.Quit()
    print(f"[pdf] {MERGED_PDF} ({pages} pages)")


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
        problems = apply_fixes(apply=args.apply)
    if args.merge:
        merge_documents()
    if args.pdf:
        export_pdf()
    if problems:
        print(f"[result] {problems} unmatched or ambiguous anchors")
        return 2
    print("[result] all anchors matched exactly once")
    return 0


if __name__ == "__main__":
    sys.exit(main())
