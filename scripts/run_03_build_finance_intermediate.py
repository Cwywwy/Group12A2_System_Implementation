# -*- coding: utf-8 -*-
"""
run_03_build_finance_intermediate.py
Author: Group12A2 DSW Team
Purpose: Parse the CSMAR three-table exports in data/raw/csmar/ into the
         intermediate finance table consumed by run_06 (feature table).
Module: scripts

Each table is read through src.data_ingestion.csmar_parser with only the
columns the pipeline needs (probe_field_columns + usecols), so even the
multi-hundred-MB exports stay within memory. The script first verifies that
all three tables are available (or can be extracted from their matching zip),
then exits with code 2 without reading any workbook if an input is still absent.

Usage:
    python scripts/run_03_build_finance_intermediate.py [--out PATH]

Revision History
-----------------
2026-11-06  initial version.
2026-11-06  auto-extract CSMAR download zips when the xlsx is missing.
2026-11-06  preflight all three inputs before reading a workbook; return exit 2 if any
            CSMAR statement remains unavailable.
"""
import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config import DATA_RAW  # noqa: E402
from src.data_ingestion.csmar_parser import (  # noqa: E402
    SAMPLE_FISCAL_YEARS,
    missing_field_report,
    probe_field_columns,
    read_csmar_table,
)
from src.features.financial import FINANCE_COLS  # noqa: E402

CSMAR_DIR = DATA_RAW / "csmar"
TABLE_FILES = {
    "balance": CSMAR_DIR / "FS_Combas.xlsx",
    "income": CSMAR_DIR / "FS_Comins.xlsx",
    "cashflow": CSMAR_DIR / "FS_Comscfd.xlsx",
}
OUT_COLUMNS = ["symbol", "fiscal_year"] + list(FINANCE_COLS[2:])


def _ensure_extracted(path: Path) -> bool:
    """Extract the matching CSMAR download zip when the xlsx is missing."""
    if path.exists():
        return True
    zips = [p for p in CSMAR_DIR.glob("*.zip") if path.stem.lower() in p.name.lower()]
    for archive in zips:
        import zipfile

        with zipfile.ZipFile(archive) as zf:
            names = [n for n in zf.namelist() if n.endswith(path.name)]
            if not names:
                continue
            print(f"[run_03] 自动解压 {archive.name} → {path.name}")
            zf.extract(names[0], path.parent)
            return path.exists()
    return False


def _empty_table() -> pd.DataFrame:
    return pd.DataFrame(columns=OUT_COLUMNS)


def main() -> int:
    parser = argparse.ArgumentParser(description="CSMAR 三表 → 金融中间表")
    parser.add_argument(
        "--out",
        default=str(DATA_RAW.parent / "interim" / "finance_intermediate.csv"),
        help="输出 CSV 路径",
    )
    args = parser.parse_args()

    unavailable = [
        (label, path) for label, path in TABLE_FILES.items() if not _ensure_extracted(path)
    ]
    if unavailable:
        for label, path in unavailable:
            print(f"[run_03] {label}: {path.name} 未找到（下载后重跑本脚本）")
        print("[run_03] 前置数据未就绪：不会读取任何工作簿或写出部分金融表。")
        return 2

    parts = []
    for label, path in TABLE_FILES.items():
        indices = probe_field_columns(path)
        table = read_csmar_table(path, usecols=sorted(set(indices.values())))
        print(f"[run_03] {label}: 解析完成，{len(table)} 行（合并口径、年份可解析）")
        parts.append(table)

    merged = parts[0]
    for other in parts[1:]:
        merged = merged.combine_first(other)
    merged = merged[OUT_COLUMNS].copy()
    merged = merged[merged["fiscal_year"].isin(SAMPLE_FISCAL_YEARS)].copy()
    merged = merged.groupby(["symbol", "fiscal_year"], as_index=False).first()
    merged = merged.dropna(subset=["symbol", "fiscal_year"]).sort_values(
        ["symbol", "fiscal_year"]
    ).reset_index(drop=True)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(out_path, index=False)
    print(f"[run_03] 输出 {out_path}：{len(merged)} 行 x {len(merged.columns)} 列")
    report = missing_field_report(merged)
    if not report.empty:
        print("[run_03] 缺失字段报告（0 表示无缺）:")
        print(report.to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
