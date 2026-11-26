# -*- coding: utf-8 -*-
"""
patch_manuscript_v05.py
Author: Cwywwy
Purpose: Build the English v0.4 manuscript from v0.3: new §3/§4, APA references, 2021-2025 window.
Module: scripts

The patch is anchor-based and idempotent in intent: sections are located by
their heading text, replaced as whole paragraph spans, and every numeric
citation token is rewritten from the legacy number to an author-year form.
No table or figure is touched here; the tables are rebuilt later from the
rerun, and the figures are inserted by the figure script.

Usage
-----
python scripts/patch_manuscript_v05.py [--source PATH] [--target PATH]

Revision History
----------------
2026-11-26  initial version: section replacement, APA references, citation conversion.
"""
from __future__ import annotations

import argparse
import copy
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches

from src.reporting.manuscript_v04_text import (
    SECTION_3,
    SECTION_3_HEADING,
    SECTION_4,
    SECTION_4_HEADING,
    body_word_count,
)
from src.reporting.references_apa import REFERENCES_APA, format_citation

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MANUSCRIPT_DIR = PROJECT_ROOT / "outputs" / "manuscript"
DEFAULT_SOURCE = MANUSCRIPT_DIR / "Group12A2_Final_EN_v0.3.docx"
DEFAULT_TARGET = MANUSCRIPT_DIR / "Group12A2_Final_EN_v0.4.docx"

CITATION = re.compile(r"\[\s*(\d+(?:\s*[,–—-]\s*\d+)*)\s*\]")
RANGE = re.compile(r"^(\d+)\s*[–—-]\s*(\d+)$")
WINDOW_OLD = ("2021–2023", "2021-2023")
WINDOW_NEW = "2021–2025"


def _find(doc, pattern: str, start: int = 0) -> int:
    """Return the index of the first paragraph at or after start matching pattern."""
    regex = re.compile(pattern)
    for index in range(start, len(doc.paragraphs)):
        if regex.search(doc.paragraphs[index].text.strip()):
            return index
    raise LookupError(f"no paragraph matches {pattern!r} from index {start}")


def _clone(template, text: str):
    """Deep-copy a paragraph element and give it one run holding text."""
    element = copy.deepcopy(template)
    runs = element.findall(qn("w:r"))
    for extra in runs[1:]:
        element.remove(extra)
    if not runs:
        run = OxmlElement("w:r")
        element.append(run)
        runs = [run]
    run = runs[0]
    for node in run.findall(qn("w:t")):
        run.remove(node)
    node = OxmlElement("w:t")
    node.set(qn("xml:space"), "preserve")
    node.text = text
    run.append(node)
    return element


def _replace_section(doc, start_pattern: str, end_pattern: str, heading: str, blocks) -> dict[str, int]:
    """Replace one whole section (heading + subsections) with blocks."""
    start = _find(doc, start_pattern)
    end = _find(doc, end_pattern, start + 1)
    old = [paragraph._p for paragraph in doc.paragraphs[start:end]]
    heading_template = copy.deepcopy(doc.paragraphs[start]._p)
    sub_template = copy.deepcopy(doc.paragraphs[start + 1]._p)
    body_template = copy.deepcopy(doc.paragraphs[start + 2]._p)

    new_elements = [_clone(heading_template, heading)]
    for title, paragraphs in blocks:
        new_elements.append(_clone(sub_template, title))
        for text in paragraphs:
            new_elements.append(_clone(body_template, text))

    anchor = doc.paragraphs[start - 1]._p
    for element in old:
        element.getparent().remove(element)
    cursor = anchor
    for element in new_elements:
        cursor.addnext(element)
        cursor = element
    return {"paragraphs": len(new_elements), "words": body_word_count(blocks)}


def _replace_references(doc) -> int:
    """Replace the 24 numbered reference entries with APA 7 entries."""
    start = _find(doc, r"^References$")
    end = _find(doc, r"^Appendix A")
    template = copy.deepcopy(doc.paragraphs[start + 1]._p)
    old = [paragraph._p for paragraph in doc.paragraphs[start + 1:end]]
    anchor = doc.paragraphs[start]._p

    for element in old:
        element.getparent().remove(element)
    cursor = anchor
    for entry in REFERENCES_APA:
        element = _clone(template, entry)
        cursor.addnext(element)
        cursor = element
    return len(REFERENCES_APA)


def _expand(token: str) -> list[int]:
    numbers: list[int] = []
    for part in re.split(r"\s*,\s*", token.strip()):
        match = RANGE.match(part)
        if match:
            numbers.extend(range(int(match.group(1)), int(match.group(2)) + 1))
        elif part:
            numbers.append(int(part))
    return numbers


def _rewrite(paragraph, text: str) -> None:
    """Set a paragraph's text, keeping the formatting of its first run."""
    runs = paragraph.runs
    if not runs:
        paragraph.add_run(text)
        return
    runs[0].text = text
    for extra in runs[1:]:
        extra._r.getparent().remove(extra._r)


def _convert_citations(doc) -> int:
    """Rewrite every numeric bracket token before References as (Author, year)."""
    stop = _find(doc, r"^References$")
    converted = 0
    for paragraph in doc.paragraphs[:stop]:
        if not CITATION.search(paragraph.text):
            continue
        converted += len(CITATION.findall(paragraph.text))
        _rewrite(
            paragraph,
            CITATION.sub(lambda match: format_citation(_expand(match.group(1))), paragraph.text),
        )
    return converted


def _update_window(doc) -> int:
    """Replace the 2021-2023 window string everywhere, title page included."""
    changed = 0
    for paragraph in doc.paragraphs:
        text = paragraph.text
        new_text = text
        for old in WINDOW_OLD:
            new_text = new_text.replace(old, WINDOW_NEW)
        if new_text != text:
            changed += 1
            _rewrite(paragraph, new_text)
    return changed


def _apply_hanging_indent(doc) -> None:
    """Give the APA entries the standard 0.5 inch hanging indent."""
    start = _find(doc, r"^References$")
    end = _find(doc, r"^Appendix A")
    for paragraph in doc.paragraphs[start + 1:end]:
        paragraph.paragraph_format.left_indent = Inches(0.5)
        paragraph.paragraph_format.first_line_indent = Inches(-0.5)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--target", type=Path, default=DEFAULT_TARGET)
    args = parser.parse_args()

    document = Document(args.source)
    before = len(document.paragraphs)

    stats_3 = _replace_section(document, r"^3\.\s", r"^4\.\s", SECTION_3_HEADING, SECTION_3)
    stats_4 = _replace_section(document, r"^4\.\s", r"^5\.\s", SECTION_4_HEADING, SECTION_4)
    entries = _replace_references(document)
    converted = _convert_citations(document)
    windows = _update_window(document)
    _apply_hanging_indent(document)

    document.save(args.target)
    print(f"source        : {args.source}")
    print(f"target        : {args.target}")
    print(f"paragraphs    : {before} -> {len(document.paragraphs)}")
    print(f"section 3     : {stats_3['paragraphs']} paragraphs, {stats_3['words']} words")
    print(f"section 4     : {stats_4['paragraphs']} paragraphs, {stats_4['words']} words")
    print(f"references    : {entries} APA entries")
    print(f"citations     : {converted} tokens converted")
    print(f"window lines  : {windows} paragraphs updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
