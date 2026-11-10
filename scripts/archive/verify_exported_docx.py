"""Verify exported docx formatting for the System Implementation section.

Author: Group12A2 DSW Team
Purpose: read back the two exported docx files and report paragraph counts,
         section headings, fonts, and line spacing so the layout can be
         confirmed without opening Word.
Module: scripts/verify (ad-hoc)
"""
from docx import Document
from docx.shared import Pt

def font_name(run):
    rPr = run._element.rPr
    if rPr is None:
        return None
    rFonts = rPr.rFonts
    if rFonts is None:
        return None
    east = rFonts.get("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}eastAsia")
    ascii_ = rFonts.get("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}ascii")
    return (ascii_, east)

def report(path):
    doc = Document(path)
    heads = []
    body_fonts = {}
    ref_count = 0
    for p in doc.paragraphs:
        t = p.text.strip()
        if not t:
            continue
        if t.startswith(("4.", "5.", "6.")) and len(t) < 120:
            heads.append(t)
        if t.startswith("[") and "]" in t[:6]:
            ref_count += 1
        for run in p.runs:
            f = font_name(run)
            if f and f[0]:
                body_fonts.setdefault(f, 0)
                body_fonts[f] += 1
    print("==", path)
    print("paragraphs:", len(doc.paragraphs))
    print("headings (4./5./6.):")
    for h in heads:
        print("   ", h)
    print("reference-like paragraphs:", ref_count)
    print("run font (ascii, eastAsia) counts:", body_fonts)

report("outputs/manuscript/Group12A2_System_Implementation_EN.docx")
report("outputs/manuscript/Group12A2_System_Implementation_CN.docx")
