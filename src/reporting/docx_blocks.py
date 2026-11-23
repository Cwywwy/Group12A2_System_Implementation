"""Insert generated tables and sentences into a manuscript .docx.

The manuscript sources are patched in place, so every helper here is written
to be safe on a second run: appends check whether the sentence is already
present, and generated tables are only inserted when their caption is absent.

Author: Jinyu Wang
Purpose: shared docx building blocks for the Phase 4 supplementary tables.
Module: reporting
"""

from __future__ import annotations

from docx.document import Document as _Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt
from docx.table import Table
from docx.text.paragraph import Paragraph

TABLE_STYLE = "Table Grid"
HEADING_SIZE = Pt(11)


def append_sentence(paragraph: Paragraph, text: str) -> bool:
    """Append one sentence to the paragraph, skipping a repeat of the same text."""
    text = text.strip()
    if not text or text in paragraph.text:
        return False
    joiner = "" if not paragraph.text or paragraph.text.endswith(" ") else " "
    run = paragraph.add_run(joiner + text)
    source = next((item for item in paragraph.runs if not item.bold), None)
    if source is not None:
        run.font.size = source.font.size
        run.font.name = source.font.name
        run.font.italic = source.font.italic
    return True


def replace_text(paragraph: Paragraph, old: str, new: str) -> bool:
    """Replace a literal fragment inside one paragraph, keeping the paragraph format."""
    if old not in paragraph.text:
        return False
    from src.reporting.docx_patch import set_para_text

    set_para_text(paragraph, paragraph.text.replace(old, new))
    return True


def _make_paragraph(
    document: _Document,
    text: str,
    *,
    bold: bool = False,
    size: Pt | None = HEADING_SIZE,
    align: WD_ALIGN_PARAGRAPH | None = None,
) -> Paragraph:
    paragraph = document.add_paragraph()
    run = paragraph.add_run(text)
    run.bold = bold
    if size is not None:
        run.font.size = size
    if align is not None:
        paragraph.alignment = align
    return paragraph


def _fill_cell(cell, text: str, bold: bool) -> None:
    cell.text = str(text)
    for run in cell.paragraphs[0].runs:
        run.bold = bold


def build_table(document: _Document, header, rows) -> Table:
    """Create a grid table with a bold header row and plain body cells."""
    table = document.add_table(rows=1 + len(rows), cols=len(header))
    table.style = TABLE_STYLE
    for index, value in enumerate(header):
        _fill_cell(table.rows[0].cells[index], value, True)
    for row_index, row in enumerate(rows, start=1):
        if len(row) != len(header):
            raise ValueError(f"row {row_index} has {len(row)} cells, header has {len(header)}")
        for column_index, value in enumerate(row):
            _fill_cell(table.rows[row_index].cells[column_index], value, False)
    return table


def insert_block_after(anchor: Paragraph, document: _Document, blocks) -> list:
    """Insert a sequence of blocks directly after ``anchor`` and return the elements.

    ``blocks`` is a sequence of tuples:
    ``("heading", text)``, ``("caption", text)``, ``("text", text)`` and
    ``("table", header, rows)``. Order is preserved because each element is
    inserted after the previous one rather than at the end of the body.
    """
    cursor = anchor._p
    created = []
    for block in blocks:
        kind = block[0]
        if kind == "heading":
            element = _make_paragraph(document, block[1], bold=True)._p
        elif kind == "caption":
            element = _make_paragraph(
                document, block[1], bold=True, size=None, align=WD_ALIGN_PARAGRAPH.LEFT
            )._p
        elif kind == "text":
            element = _make_paragraph(document, block[1], bold=False, size=None)._p
        elif kind == "table":
            element = build_table(document, block[1], block[2])._tbl
        else:  # pragma: no cover - defensive
            raise ValueError(f"unknown block kind: {kind}")
        cursor.addnext(element)
        cursor = element
        created.append(element)
    return created
