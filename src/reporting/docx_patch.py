# -*- coding: utf-8 -*-
"""
docx_patch.py
Author: Group12A2 DSW Team
Purpose: Reusable python-docx primitives for rewriting and merging the
         manuscript files without touching unrelated content.
Module: src.reporting

Revision History
----------------
2026-11-24  initial version: paragraph rewrites and appendix merge extracted
            from the v0.3 patcher.
"""
from __future__ import annotations

import copy
from pathlib import Path

import docx
from docx.oxml.ns import qn

__all__ = [
    "merge_documents",
    "paragraph_texts",
    "replace_paragraph",
    "set_para_text",
]


def set_para_text(paragraph, value: str) -> None:
    """Write ``value`` into a paragraph while keeping the first run's formatting."""
    runs = paragraph.runs
    if not runs:
        paragraph.add_run(value)
        return
    runs[0].text = value
    for run in runs[1:]:
        run.text = ""


def paragraph_texts(path: str | Path) -> list[str]:
    """Return the text of every paragraph in ``path``."""
    return [paragraph.text for paragraph in docx.Document(str(path)).paragraphs]


def replace_paragraph(document, old_prefix: str, new: str) -> int:
    """Rewrite paragraphs whose text starts with ``old_prefix``.

    A paragraph that already carries ``new`` counts as done, which keeps the
    rewrite idempotent when the patcher runs twice. Returns the number of
    paragraphs that were rewritten.
    """
    changed = 0
    for paragraph in document.paragraphs:
        text = paragraph.text
        if not text.strip():
            continue
        if text == new:
            continue
        if not text.startswith(old_prefix):
            continue
        set_para_text(paragraph, new)
        changed += 1
    return changed


def _page_break_element():
    """Build a page-break paragraph in a throwaway document."""
    carrier_document = docx.Document()
    carrier = carrier_document.add_paragraph()._p
    run = carrier.makeelement(qn("w:r"), {})
    br = carrier.makeelement(qn("w:br"), {qn("w:type"): "page"})
    run.append(br)
    carrier.append(run)
    return carrier


def merge_documents(
    primary: str | Path,
    appendix: str | Path,
    output: str | Path,
    separate_line: str = "",
) -> Path:
    """Append ``appendix`` (minus its section properties) to ``primary``.

    The result is written to ``output`` and verified paragraph by paragraph
    against the two sources, so a silent merge failure cannot reach a
    deliverable. ``separate_line`` is inserted between the two parts as a page
    break so the appendix always starts on a fresh page.
    """
    primary = Path(primary)
    appendix = Path(appendix)
    for source in (primary, appendix):
        if not source.exists():
            raise FileNotFoundError(source)
    base = docx.Document(str(primary))
    tail = docx.Document(str(appendix))
    body = base.element.body
    sect_pr = body.find(qn("w:sectPr"))
    insert_at = len(body) - 1 if sect_pr is not None else len(body)
    if separate_line:
        body.insert(insert_at, copy.deepcopy(_page_break_element()))
        insert_at = len(body) - 1 if sect_pr is not None else len(body)
    for child in list(tail.element.body):
        if child.tag == qn("w:sectPr"):
            continue
        body.insert(insert_at, copy.deepcopy(child))
        insert_at += 1

    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    base.save(str(output))

    merged = [text for text in paragraph_texts(output) if text.strip()]
    expected = [
        text for text in paragraph_texts(primary) + paragraph_texts(appendix) if text.strip()
    ]
    if merged != expected:
        difference = next(
            (index for index, (a, b) in enumerate(zip(expected, merged)) if a != b),
            min(len(expected), len(merged)),
        )
        raise ValueError(
            "merged text differs from the two sources "
            f"({len(merged)} vs {len(expected)} paragraphs, first difference at {difference})"
        )
    return output
