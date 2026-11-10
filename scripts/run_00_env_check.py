# -*- coding: utf-8 -*-
"""
run_00_env_check.py
Author: Group12A2 DSW Team
Purpose: Readiness probe - report which pipeline inputs exist and what is missing.
Module: scripts

Usage:
    .venv/Scripts/python scripts/run_00_env_check.py

Revision History
-----------------
2026-11-06  initial version.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config import CNINFO_RAW, DATA_INTERIM, DATA_RAW, SAMPLE_YEARS
from src.sample_frame import CHECKLIST_CSV

CSMAR_FILES = ("FS_Combas.xlsx", "FS_Comins.xlsx", "FS_Comscfd.xlsx")
DICTIONARIES = ("financial_positive.txt", "financial_negative.txt", "uncertainty.txt")


def _count_pdfs(year: int) -> int:
    folder = CNINFO_RAW / str(year)
    if not folder.exists():
        return 0
    return len(list(folder.glob("*_annual_report.pdf")))


def main() -> int:
    checks: list[tuple[str, bool, str]] = []
    checks.append(("虚拟环境 .venv", (Path(".venv/Scripts/python.exe")).exists(), str(Path(".venv"))))
    checks.append(("样本框/下载打卡表", CHECKLIST_CSV.exists(), str(CHECKLIST_CSV)))
    for name in CSMAR_FILES:
        path = DATA_RAW / "csmar" / name
        checks.append((f"CSMAR {name}", path.exists(), str(path)))
    for year in SAMPLE_YEARS:
        n = _count_pdfs(year)
        checks.append((f"年报 PDF {year}", n > 0, f"{n} 个文件"))
    for year in SAMPLE_YEARS:
        path = DATA_INTERIM / f"text_features_{year}.csv"
        checks.append((f"文本特征 {year}", path.exists(), str(path)))
    for name in DICTIONARIES:
        path = DATA_RAW.parent / "external" / "dictionaries" / name
        checks.append((f"词典 {name}", path.exists(), str(path)))

    print("[run_00] 管线就绪检查")
    missing = 0
    for label, ok, detail in checks:
        print(f"  [{'OK' if ok else '--'}] {label}: {detail}")
        missing += 0 if ok else 1
    print(f"[run_00] 就绪 {len(checks) - missing}/{len(checks)}；缺失 {missing} 项")
    if missing:
        print("[run_00] 缺失项说明：CSMAR 三表请组员按 docs/csmar_download_guide.md 下载；")
        print("[run_00] 年报 PDF 用 run_02 补下；文本特征用 run_05 提取。")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
