"""Map generated section-5 prose onto the paragraphs of the manuscript docx.

File: scripts/map_section5_paragraphs.py
Author: DSW group 12A2
Purpose: record which paragraph of outputs/manuscript/Group12A2_Final_EN_v0.4.docx
         currently carries each block produced by scripts.build_section5.prose().
         The map is written to outputs/work/section5_map.json so that the later
         number refresh can replace text in place instead of rebuilding the span.
Module: reporting
"""

# Revision history
# 2026-11-26  initial version: exact-match map of prose keys to docx paragraphs.

from __future__ import annotations

import json
import sys
from pathlib import Path

from docx import Document

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.build_section5 import collect_numbers, prose  # noqa: E402

DOCX = PROJECT_ROOT / "outputs" / "manuscript" / "Group12A2_Final_EN_v0.4.docx"
OUT = PROJECT_ROOT / "outputs" / "work" / "section5_map.json"


def _norm(text: str) -> str:
    return " ".join(text.split())


def main() -> int:
    numbers = collect_numbers()
    blocks = prose(numbers)
    document = Document(DOCX)
    paragraphs = [_norm(paragraph.text) for paragraph in document.paragraphs]

    mapping: dict[str, int] = {}
    missing: list[str] = []
    for key, value in blocks.items():
        target = _norm(value)
        hits = [index for index, text in enumerate(paragraphs) if text == target]
        if len(hits) == 1:
            mapping[key] = hits[0]
        else:
            missing.append(f"{key} ({len(hits)} hits)")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(mapping, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"mapped {len(mapping)} of {len(blocks)} blocks -> {OUT}")
    if missing:
        print("unmatched: " + "; ".join(missing))
    return 0 if not missing else 1


if __name__ == "__main__":
    raise SystemExit(main())
