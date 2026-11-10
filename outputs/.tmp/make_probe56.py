"""Throwaway: build a probe docx that shows the new 5.6 block on page 1."""

import importlib.util
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.text.paragraph import Paragraph

root = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("bs5", root / "scripts" / "build_section5.py")
bs5 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bs5)

num = bs5.collect_numbers()
text = bs5.prose(num)
doc = Document(str(root / "outputs" / "manuscript" / "source" / "Group12A2_Final_EN.docx"))
paras = doc.paragraphs
anchor = paras[2]._p
heading = bs5._make_paragraph_like(paras[2], text["s56_heading"], 13, False, bold=True)
cap = bs5._make_paragraph_like(paras[2], text["t54_caption"], 9, True)
cap_p = Paragraph(cap, paras[2]._parent)
cap_p.alignment = WD_ALIGN_PARAGRAPH.LEFT
items = [
    heading,
    bs5._make_paragraph_like(paras[2], text["s56a"], 0, False),
    cap,
    bs5._make_table(bs5._table_54(num), paras[2]),
    bs5._make_paragraph_like(paras[2], text["s56b"], 0, False),
]
for element in items:
    anchor.addnext(element)
    anchor = element
out = root / "outputs" / ".tmp" / "probe56.docx"
doc.save(str(out))
print("probe written", out, out.stat().st_size)
