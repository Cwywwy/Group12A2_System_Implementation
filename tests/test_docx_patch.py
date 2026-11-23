# -*- coding: utf-8 -*-
"""
test_docx_patch.py
Author: Group12A2 DSW Team
Purpose: Tests for the docx primitives that rewrite and merge the manuscript.
Module: tests
"""
import docx
import pytest

from src.reporting.docx_patch import (
    merge_documents,
    paragraph_texts,
    replace_paragraph,
    set_para_text,
)


def _document_with(*paragraphs: str):
    document = docx.Document()
    for text in paragraphs:
        document.add_paragraph(text)
    return document


def test_set_para_text_keeps_first_run_formatting():
    document = docx.Document()
    paragraph = document.add_paragraph()
    first = paragraph.add_run("old ")
    first.bold = True
    paragraph.add_run("tail")
    set_para_text(paragraph, "new text")
    assert [run.text for run in paragraph.runs] == ["new text", ""]
    assert paragraph.runs[0].bold is True


def test_set_para_text_adds_a_run_to_an_empty_paragraph():
    document = docx.Document()
    paragraph = document.add_paragraph("")
    set_para_text(paragraph, "filled")
    assert paragraph.text == "filled"


def test_replace_paragraph_is_idempotent():
    document = _document_with("prefix sentence with a tail.", "untouched paragraph")
    assert replace_paragraph(document, "prefix sentence", "rewritten paragraph") == 1
    assert replace_paragraph(document, "prefix sentence", "rewritten paragraph") == 0
    assert replace_paragraph(document, "rewritten", "rewritten paragraph") == 0
    assert [p.text for p in document.paragraphs] == [
        "rewritten paragraph",
        "untouched paragraph",
    ]


def test_merge_documents_appends_the_appendix_after_a_page_break(tmp_path):
    primary = tmp_path / "body.docx"
    appendix = tmp_path / "appendix.docx"
    merged = tmp_path / "merged.docx"
    _document_with("body one", "body two").save(primary)
    _document_with("appendix one").save(appendix)

    result = merge_documents(primary, appendix, merged, separate_line="page-break")

    assert result == merged
    texts = [text for text in paragraph_texts(merged) if text.strip()]
    assert texts == ["body one", "body two", "appendix one"]


def test_merge_documents_copies_into_the_target_not_the_source(tmp_path):
    primary = tmp_path / "body.docx"
    appendix = tmp_path / "appendix.docx"
    merged = tmp_path / "merged.docx"
    _document_with("body one").save(primary)
    _document_with("appendix one").save(appendix)

    merge_documents(primary, appendix, merged)

    assert [text for text in paragraph_texts(primary) if text.strip()] == ["body one"]
    assert [text for text in paragraph_texts(appendix) if text.strip()] == ["appendix one"]


def test_merge_documents_missing_source_raises(tmp_path):
    primary = tmp_path / "body.docx"
    _document_with("body one").save(primary)
    with pytest.raises(FileNotFoundError):
        merge_documents(primary, tmp_path / "missing.docx", tmp_path / "merged.docx")
