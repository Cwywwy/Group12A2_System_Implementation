# -*- coding: utf-8 -*-
"""Temporary benchmark: per-PDF MD&A extraction timing."""
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import CNINFO_RAW  # noqa: E402
from src.features.textual import extract_pdf_text, locate_mda, tokenise  # noqa: E402

N = 6
pdfs = sorted((CNINFO_RAW / "2021").glob("*_annual_report.pdf"))[:N]

t_all = time.time()
for pdf in pdfs:
    t0 = time.time()
    text = extract_pdf_text(pdf)
    mda = locate_mda(text)
    toks = tokenise(mda or "")
    print(f"{pdf.name}: {(time.time()-t0):.2f}s, mda_chars={len(mda or '')}, tokens={len(toks)}")
print(f"TOTAL {N} pdfs in {time.time()-t_all:.2f}s = {(time.time()-t_all)/N:.2f}s/pdf")
