"""Publish the freshly printed PDFs into ``outputs/manuscript/``.

File:     scripts/run_14_publish_pdfs.py
Author:   Group12A2 DSW Team
Purpose:  Copy the PDFs printed by Univer (``outputs/.tmp/final_*.pdf``) over the
          delivered files in ``outputs/manuscript/``.  Windows locks an open PDF,
          so Acrobat/WPS must be closed first; the script reports which target is
          still locked instead of failing silently.
Module:   reporting / delivery

Revision History:
  2026-11-11  initial version; copies the §5.7 PDFs and reports locked targets.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TMP = ROOT / "outputs" / ".tmp"
MANUSCRIPT = ROOT / "outputs" / "manuscript"

PAIRS = (
    (TMP / "final_en_v7.pdf", MANUSCRIPT / "Group12A2_Final_EN.pdf"),
    (TMP / "final_cn_v5.pdf", MANUSCRIPT / "Group12A2_Final_CN.pdf"),
)


def publish() -> int:
    """Copy every staged PDF, returning the number of targets still locked."""
    locked = 0
    for source, target in PAIRS:
        if not source.exists():
            print(f"[skip] missing staged file: {source.relative_to(ROOT)}")
            locked += 1
            continue
        try:
            shutil.copyfile(source, target)
        except PermissionError:
            print(
                "[locked] "
                f"{target.relative_to(ROOT)} is open in another program "
                "(Acrobat/WPS). Close it and run this script again."
            )
            locked += 1
        else:
            print(f"[ok] {target.relative_to(ROOT)} <- {source.relative_to(ROOT)}")
    return locked


def main() -> int:
    locked = publish()
    if locked:
        print(f"{locked} file(s) not published")
        return 2
    print("all PDFs published")
    return 0


if __name__ == "__main__":
    sys.exit(main())
