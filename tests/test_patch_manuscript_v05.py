# -*- coding: utf-8 -*-
"""
test_patch_manuscript_v05.py
Author: Cwywwy
Purpose: Unit tests for the section, reference and citation surgery in the v0.4 patch script.
Module: tests

Revision History
----------------
2026-11-26  initial version: section replacement, citation conversion, window rewrite.
"""
import sys
from pathlib import Path

import pytest
from docx import Document

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.patch_manuscript_v05 import (  # noqa: E402
    _convert_citations,
    _expand,
    _replace_section,
    _update_window,
)

BLOCKS_3 = (
    ("3.1 Scope, Sample, and Data Sources", ("The new scope paragraph.",)),
    ("3.2 Textual and Financial Features", ("First feature paragraph.", "Second feature paragraph.")),
)
BLOCKS_4 = (("4.1 Pipeline and Reproducibility", ("The new pipeline paragraph.",)),)


def _document() -> Document:
    document = Document()
    for text in (
        "Title with a 2021–2023 window.",
        "3. Research Design and Methodology",
        "3.1 Old scope heading",
        "Old scope body citing [1] and [4–6].",
        "3.2 Old feature heading",
        "Old feature body.",
        "4. System Implementation and Model Development",
        "4.1 Old pipeline heading",
        "Old pipeline body citing [11,12].",
        "5. Experiment and Results",
        "5.1 sample body with 2021–2023.",
        "References",
        "[1] OLD ENTRY",
        "Appendix A. Branch Experiments",
        "Appendix body.",
    ):
        document.add_paragraph(text)
    return document


def _texts(document) -> list[str]:
    return [paragraph.text for paragraph in document.paragraphs]


def test_replace_section_rewrites_only_its_own_span() -> None:
    document = _document()
    stats = _replace_section(document, r"^3\.\s", r"^4\.\s", "3. Research Design and Methodology", BLOCKS_3)
    texts = _texts(document)

    assert stats["paragraphs"] == 6
    assert texts[1] == "3. Research Design and Methodology"
    assert texts[2] == "3.1 Scope, Sample, and Data Sources"
    assert texts[3] == "The new scope paragraph."
    assert texts[4] == "3.2 Textual and Financial Features"
    assert texts[5] == "First feature paragraph."
    assert texts[6] == "Second feature paragraph."
    assert "Old scope body citing [1] and [4–6]." not in texts
    assert texts[7].startswith("4. System Implementation")


def test_replace_section_keeps_trailing_sections_intact() -> None:
    document = _document()
    _replace_section(document, r"^3\.\s", r"^4\.\s", "3. Research Design and Methodology", BLOCKS_3)
    _replace_section(document, r"^4\.\s", r"^5\.\s", "4. System Implementation and Reproducibility", BLOCKS_4)
    texts = _texts(document)

    assert "4. System Implementation and Reproducibility" in texts
    assert "4.1 Pipeline and Reproducibility" in texts
    assert "The new pipeline paragraph." in texts
    assert "Old pipeline body citing [11,12]." not in texts
    assert texts[-1] == "Appendix body."


def test_expand_handles_ranges_and_commas() -> None:
    assert _expand("1") == [1]
    assert _expand("4–6") == [4, 5, 6]
    assert _expand("11, 12") == [11, 12]
    assert _expand("2,14") == [2, 14]


def test_convert_citations_replaces_every_bracket_before_references() -> None:
    document = _document()
    converted = _convert_citations(document)
    texts = _texts(document)

    assert converted == 3
    assert "(Healy & Palepu, 2001)" in texts[3]
    assert "(Courtis, 1998; Lehavy et al., 2011; Li, 2008)" in texts[3]
    assert "(Beneish, 1999; Repousis, 2016)" in texts[8]
    assert "[1] OLD ENTRY" in texts


def test_update_window_rewrites_title_and_body() -> None:
    document = _document()
    changed = _update_window(document)
    texts = _texts(document)

    assert changed == 2
    assert texts[0] == "Title with a 2021–2025 window."
    assert texts[10] == "5.1 sample body with 2021–2025."
