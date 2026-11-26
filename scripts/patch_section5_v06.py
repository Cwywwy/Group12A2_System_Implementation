"""Refresh section 5 of the manuscript with the current pipeline numbers.

File: scripts/patch_section5_v06.py
Author: DSW group 12A2
Purpose: replace the section-5 paragraphs of Group12A2_Final_EN_v0.4.docx in
         place, update the three body tables, and insert the paragraphs and the
         figure that the restructured section needs. Text comes from
         src.reporting.manuscript_v04_section5; numbers come from the pipeline
         tables through scripts.build_section5.collect_numbers.
Module: reporting
"""

# Revision history
# 2026-11-26  initial version: slot-based section 5 refresh with one inserted figure.

from __future__ import annotations

import copy
import sys
from pathlib import Path

import pandas as pd
from docx import Document
from docx.shared import Inches

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.build_section5 import collect_numbers  # noqa: E402
from src.config import DATA_PROCESSED, TABLES  # noqa: E402
from src.reporting.manuscript_v04_appendix import (  # noqa: E402
    attrition_rows,
    branch_rows,
    descriptives_rows,
    enrichment_rows,
    outcome_rows,
)
from src.reporting.manuscript_v04_section5 import (  # noqa: E402
    abstract,
    conclusion,
    section5,
    section5_tables,
)

MANUSCRIPT = PROJECT_ROOT / "outputs" / "manuscript"

SOURCE = MANUSCRIPT / "Group12A2_Final_EN_v0.4.docx"
TARGET = MANUSCRIPT / "Group12A2_Final_EN_v0.5.docx"
FIGURE = PROJECT_ROOT / "outputs" / "figures" / "manuscript" / "figure_5_7_year_diagnostics.png"

# Paragraph index in the source file -> key in the block dictionary.
SLOTS = {
    38: "s51",
    40: "s52_intro",
    41: "s52_skew",
    42: "t51_caption",
    43: "s52_after",
    45: "f51_caption",
    46: "f51_note",
    47: "s52_interpret",
    49: "f52_caption",
    50: "f52_note",
    52: "s53",
    54: "s54",
    56: "s55",
    58: "s56_a",
    59: "s56_b",
    60: "t52_caption",
    61: "s56_c",
    63: "f53_caption",
    64: "f53_note",
    65: "t53_caption",
    66: "s56_d",
    67: "s56_e",
    68: "appendix_pointer",
}

# Paragraph index in the source file -> keys to insert after it, in order.
INSERT_AFTER = {
    54: ["s54_year", "@figure54"],
    56: ["s55_b"],
}

# Paragraph index in the source file -> keys to insert before it, in order.
INSERT_BEFORE = {
    68: ["s56_holdout"],
}

FIGURE_54 = {
    "path": FIGURE,
    "width": Inches(5.6),
    "caption": (
        "Figure 5.3. Beneish cut-off drift and ranking quality by fiscal year."
    ),
    "note": (
        "Note: the left panel plots the ninetieth percentile of the M-Score inside each "
        "fiscal year; the right panel plots AUC against modified audit opinions. The "
        "benchmark has to be recalibrated every year, while the finance-only ranking keeps "
        "the same ordering."
    ),
}

FIGURE_41 = {
    "path": PROJECT_ROOT / "outputs" / "figures" / "manuscript" / "figure_4_1_pipeline.png",
    "width": Inches(5.6),
    "caption": (
        "Figure 4.1. The research pipeline from sample frame to the review queue."
    ),
    "note": (
        "Note: the three bands are acquisition, feature construction and modelling, in "
        "execution order. Every stage writes an inspectable CSV artefact, so any stage can "
        "be rerun on its own inputs."
    ),
}


def _set_text(paragraph, text: str) -> None:
    """Replace a paragraph's text while keeping the formatting of its first run."""
    runs = paragraph.runs
    if not runs:
        paragraph.add_run(text)
        return
    runs[0].text = text
    for run in runs[1:]:
        run._element.getparent().remove(run._element)


def _clone_paragraph(template, text: str):
    """Return a new paragraph element shaped like the template but holding ``text``."""
    element = copy.deepcopy(template._p)
    paragraph = template.__class__(element, template._parent)
    _set_text(paragraph, text)
    return paragraph


def _insert_after(anchor, text: str) -> None:
    anchor._p.addnext(_clone_paragraph(anchor, text)._p)


def _insert_before(anchor, text: str) -> None:
    anchor._p.addprevious(_clone_paragraph(anchor, text)._p)


def _insert_figure(document, anchor, spec: dict) -> None:
    """Place an image paragraph plus caption and note after ``anchor``."""
    document.add_picture(str(spec["path"]), width=spec["width"])
    picture = document.paragraphs[-1]
    anchor._p.addnext(picture._p)
    caption = _clone_paragraph(anchor, spec["caption"])
    picture._p.addnext(caption._p)
    note = _clone_paragraph(anchor, spec["note"])
    caption._p.addnext(note._p)


def _insert_pipeline_figure(document) -> None:
    """Place Figure 4.1 between the pipeline description and subsection 4.2."""
    for index, paragraph in enumerate(document.paragraphs):
        if paragraph.text.strip().startswith("4.2 "):
            _insert_figure(document, document.paragraphs[index - 1], FIGURE_41)
            return


def _fix_intro_numbers(document) -> None:
    """Retire the three-year AUC pair that the introduction still quotes."""
    old = "(AUC 0.242) while a finance-only ranking reaches 0.802"
    new = "(AUC 0.263) while a finance-only ranking reaches 0.787"
    for paragraph in document.paragraphs:
        if old in paragraph.text:
            _set_text(paragraph, paragraph.text.replace(old, new))


def _fix_appendix_captions(document, numbers: dict) -> None:
    """Retire the sample counts that a window change leaves in the captions."""
    frame_n = int(numbers["frame_years"])
    for paragraph in document.paragraphs:
        text = paragraph.text
        if not text.startswith(("Table A1.", "Table B")):
            continue
        updated = text.replace("(10,172 firm-years)", f"({frame_n:,} firm-years)")
        if updated != text:
            _set_text(paragraph, updated)


def _appendix_grids(numbers: dict) -> dict[int, list[list[str]]]:
    """Rebuild the appendix tables whose counts depend on the sample window."""
    features = pd.read_csv(DATA_PROCESSED / "feature_table.csv", dtype={"symbol": str})
    events = pd.read_csv(DATA_PROCESSED / "event_table.csv", dtype={"symbol": str})
    ranking = pd.read_csv(TABLES / "event_ranking_metrics.csv")
    topk = pd.read_csv(TABLES / "topk_metrics.csv")
    try:
        diagnostics = pd.read_csv(TABLES / "event_strict_diagnostics.csv")
    except FileNotFoundError:
        diagnostics = None
    return {
        3: branch_rows(numbers, ranking),
        4: descriptives_rows(features),
        5: enrichment_rows(topk),
        8: attrition_rows(features),
        9: outcome_rows(events, diagnostics, tuple(numbers["violation_years"])),
    }


def _apply_tables(document, grids: dict[int, list[list[str]]]) -> None:
    for index, rows in grids.items():
        table = document.tables[index]
        while len(table.rows) < len(rows):
            table.add_row()
        while len(table.rows) > len(rows):
            removed = table.rows[-1]
            removed._element.getparent().remove(removed._element)
        for row_index, row in enumerate(rows):
            for column_index, value in enumerate(row):
                if column_index >= len(table.rows[row_index].cells):
                    continue
                cell = table.rows[row_index].cells[column_index]
                if cell.paragraphs and cell.paragraphs[0].runs:
                    cell.paragraphs[0].runs[0].text = value
                else:
                    cell.text = value


def main() -> int:
    numbers = collect_numbers()
    blocks = section5(numbers)
    grids = section5_tables(numbers)
    grids.update(_appendix_grids(numbers))

    document = Document(SOURCE)
    paragraphs = list(document.paragraphs)

    abstract_first, abstract_second = abstract(numbers)
    _set_text(paragraphs[3], abstract_first)
    _set_text(paragraphs[4], abstract_second)

    anchors = {}
    for index, key in SLOTS.items():
        text = blocks[key]
        anchors[index] = paragraphs[index]
        _set_text(anchors[index], text)

    for index, keys in INSERT_AFTER.items():
        anchor = anchors[index]
        for key in reversed(keys):
            if key == "@figure54":
                _insert_figure(document, anchor, FIGURE_54)
            elif key in blocks:
                _insert_after(anchor, blocks[key])

    for index, keys in INSERT_BEFORE.items():
        anchor = anchors[index]
        for key in reversed(keys):
            if key in blocks:
                _insert_before(anchor, blocks[key])

    _apply_tables(document, grids)
    _fix_appendix_captions(document, numbers)
    _fix_intro_numbers(document)
    _insert_pipeline_figure(document)
    _set_text(document.paragraphs[75], conclusion(numbers))
    document.save(TARGET)

    words = sum(len(blocks[key].split()) for key in SLOTS.values())
    print(f"wrote {TARGET}")
    print(f"section 5 body: {words} words over {len(SLOTS)} paragraphs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
