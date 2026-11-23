"""Unit tests for the docx building blocks used by the Phase 4 tables.

The helpers edit manuscript sources in place, so the tests pin down the two
properties that protect the sources: appending twice never duplicates a
sentence, and generated tables are inserted directly after their anchor.

Author: Jinyu Wang
Purpose: cover src/reporting/docx_blocks.py.
Module: tests
"""

from __future__ import annotations

import pytest
from docx import Document
from docx.shared import Pt

from src.reporting.docx_blocks import (
    append_sentence,
    build_table,
    insert_block_after,
    replace_text,
)


@pytest.fixture()
def document():
    return Document()


def _paragraph(document, text: str):
    paragraph = document.add_paragraph()
    run = paragraph.add_run(text)
    run.font.size = Pt(10)
    run.font.name = "Times New Roman"
    return paragraph


def test_append_sentence_adds_text_once(document):
    paragraph = _paragraph(document, "The sample has 9,239 firm-years.")

    assert append_sentence(paragraph, "It covers 3,488 firms.") is True
    assert paragraph.text == "The sample has 9,239 firm-years. It covers 3,488 firms."

    assert append_sentence(paragraph, "It covers 3,488 firms.") is False
    assert paragraph.text.count("It covers 3,488 firms.") == 1


def test_append_sentence_ignores_empty_text(document):
    paragraph = _paragraph(document, "Sample.")

    assert append_sentence(paragraph, "   ") is False
    assert paragraph.text == "Sample."


def test_append_sentence_copies_run_format(document):
    paragraph = _paragraph(document, "Sample.")

    assert append_sentence(paragraph, "Extra sentence.") is True
    assert paragraph.runs[-1].font.size == Pt(10)
    assert paragraph.runs[-1].font.name == "Times New Roman"


def test_replace_text_swaps_fragment(document):
    paragraph = _paragraph(document, "The overlap is 0.797 in both directions.")

    assert replace_text(paragraph, "0.797", "0.796") is True
    assert paragraph.text == "The overlap is 0.796 in both directions."

    assert replace_text(paragraph, "0.797", "0.796") is False


def test_build_table_writes_header_and_rows(document):
    table = build_table(document, ["Step", "Retained"], [["0", "10,172"], ["1", "9,414"]])

    assert table.style.name == "Table Grid"
    assert len(table.rows) == 3
    assert len(table.columns) == 2
    assert table.rows[0].cells[0].text == "Step"
    assert table.rows[0].cells[0].paragraphs[0].runs[0].bold is True
    assert table.rows[1].cells[1].text == "10,172"
    assert table.rows[2].cells[1].paragraphs[0].runs[0].bold is False


def test_build_table_rejects_ragged_row(document):
    with pytest.raises(ValueError, match="header has 2"):
        build_table(document, ["Step", "Retained"], [["0"]])


def test_insert_block_after_preserves_order(document):
    anchor = _paragraph(document, "Anchor paragraph.")
    trailing = _paragraph(document, "Trailing paragraph.")

    insert_block_after(
        anchor,
        document,
        [
            ("heading", "Appendix B.3 Additional tables"),
            ("text", "Lead sentence."),
            ("caption", "Table B4. Paired increments."),
            ("table", ["Step", "Retained"], [["0", "10,172"]]),
        ],
    )

    texts = [paragraph.text for paragraph in document.paragraphs]
    assert texts == [
        "Anchor paragraph.",
        "Appendix B.3 Additional tables",
        "Lead sentence.",
        "Table B4. Paired increments.",
        "Trailing paragraph.",
    ]
    assert len(document.tables) == 1
    assert document.tables[0].rows[1].cells[0].text == "0"
    assert trailing.text == "Trailing paragraph."
