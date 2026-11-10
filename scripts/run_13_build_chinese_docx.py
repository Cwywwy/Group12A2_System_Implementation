"""Convert docs/manuscript_chinese_draft.md into a formatted Chinese .docx.

File:    run_13_build_chinese_docx.py
Author:  Group12A2 DSW Team
Purpose: Produce the Chinese manuscript Word deliverable (Song Ti body, Hei Ti
         headings, 1.5 line spacing) from the reviewed Markdown draft.
Module:  reporting (manuscript assembly)
"""

import re
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor

SOURCE = Path("docs/manuscript_chinese_draft.md")
OUTPUT = Path("outputs/manuscript/Group12A2_Final_CN.docx")

BODY_EA = "宋体"
BODY_ASCII = "Times New Roman"
HEAD_EA = "黑体"
MONO = "Consolas"

INLINE_RE = re.compile(r"(\*\*.+?\*\*|`.+?`)")


def set_run_font(run, ea=BODY_EA, ascii_=BODY_ASCII, size=12, bold=False,
                 italic=False, colour=None):
    run.font.name = ascii_
    run._element.rPr.rFonts.set(qn("w:eastAsia"), ea)
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    if colour is not None:
        run.font.color.rgb = colour


def add_inline_runs(para, text, ea=BODY_EA, size=12, base_bold=False):
    """Split text into bold/code/normal runs and append to para."""
    pos = 0
    for match in INLINE_RE.finditer(text):
        if match.start() > pos:
            r = para.add_run(text[pos:match.start()])
            set_run_font(r, ea=ea, size=size, bold=base_bold)
        token = match.group(0)
        if token.startswith("**") and token.endswith("**"):
            r = para.add_run(token[2:-2])
            set_run_font(r, ea=ea, size=size, bold=True)
        elif token.startswith("`") and token.endswith("`"):
            r = para.add_run(token[1:-1])
            set_run_font(r, ea=BODY_EA, ascii_=MONO, size=size, bold=base_bold)
        pos = match.end()
    if pos < len(text):
        r = para.add_run(text[pos:])
        set_run_font(r, ea=ea, size=size, bold=base_bold)


def add_body(doc, text):
    para = doc.add_paragraph()
    para.paragraph_format.line_spacing = 1.5
    para.paragraph_format.space_after = Pt(6)
    add_inline_runs(para, text, size=12)
    return para


def add_heading(doc, text, size, space_before=12, space_after=8):
    para = doc.add_paragraph()
    para.paragraph_format.line_spacing = 1.5
    para.paragraph_format.space_before = Pt(space_before)
    para.paragraph_format.space_after = Pt(space_after)
    add_inline_runs(para, text, ea=HEAD_EA, size=size, base_bold=True)
    return para


def main():
    doc = Document()
    lines = SOURCE.read_text(encoding="utf-8").splitlines()

    for raw in lines:
        line = raw.rstrip()
        if not line.strip():
            continue
        if line.strip() == "---":
            continue

        if line.startswith("# "):
            para = doc.add_paragraph()
            para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            para.paragraph_format.space_after = Pt(12)
            add_inline_runs(para, line[2:].strip(), ea=HEAD_EA, size=16,
                            base_bold=True)
        elif line.startswith("## "):
            add_heading(doc, line[3:].strip(), size=15, space_before=14,
                        space_after=8)
        elif line.startswith("### "):
            add_heading(doc, line[4:].strip(), size=13, space_before=12,
                        space_after=6)
        elif line.startswith("> "):
            para = doc.add_paragraph()
            para.paragraph_format.line_spacing = 1.5
            para.paragraph_format.left_indent = Pt(18)
            add_inline_runs(para, line[2:].strip(), size=11, base_bold=False)
            for run in para.runs:
                run.font.color.rgb = RGBColor(0x59, 0x59, 0x59)
        elif re.match(r"^- ", line):
            para = doc.add_paragraph(style="List Bullet")
            para.paragraph_format.line_spacing = 1.5
            add_inline_runs(para, line[2:].strip(), size=12)
        elif re.match(r"^\d+\. ", line):
            para = doc.add_paragraph(style="List Number")
            para.paragraph_format.line_spacing = 1.5
            add_inline_runs(para, re.sub(r"^\d+\. ", "", line).strip(), size=12)
        else:
            add_body(doc, line)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUTPUT)
    print(f"[run_13] wrote {OUTPUT.resolve()}")


if __name__ == "__main__":
    main()
