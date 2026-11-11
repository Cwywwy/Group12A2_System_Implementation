"""Verify that the delivered manuscripts match a fresh rebuild from the current tables.

Checks
1. Rebuild EN/CN docx from ``outputs/manuscript/source/*.docx`` + current ``outputs/tables``.
2. Compare paragraph text and table grids with the delivered files (must be identical).
3. Cross-check a handful of headline numbers against the CSVs directly.
4. Report PDF page counts and modification times.

Revision history
2026-11-12  created: rebuild-vs-delivered verification for the final manuscripts.
"""

from __future__ import annotations

import subprocess
import sys
from datetime import datetime
from pathlib import Path

from docx import Document

ROOT = Path(__file__).resolve().parents[1]
MANUSCRIPT = ROOT / "outputs" / "manuscript"
TMP = ROOT / "outputs" / ".tmp"


def dump(path: Path) -> tuple[list[str], list[list[list[str]]]]:
    doc = Document(str(path))
    paras = [p.text.strip() for p in doc.paragraphs]
    tables = [[[c.text.strip() for c in row.cells] for row in t.rows] for t in doc.tables]
    return paras, tables


def rebuild() -> None:
    TMP.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "build_section5.py"),
        "--docx",
        "--docx-out",
        str(TMP / "verify_en.docx"),
        "--docx-cn",
        "--docx-cn-out",
        str(TMP / "verify_cn.docx"),
    ]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    print(proc.stdout.strip())
    if proc.returncode != 0:
        print(proc.stderr[-2000:])
        raise SystemExit(f"rebuild failed (exit {proc.returncode})")


def compare(label: str, delivered: Path, rebuilt: Path) -> bool:
    d_paras, d_tables = dump(delivered)
    r_paras, r_tables = dump(rebuilt)
    ok = True
    print(f"\n[{label}] delivered={len(d_paras)} paras / {len(d_tables)} tables   "
          f"rebuilt={len(r_paras)} paras / {len(r_tables)} tables")
    if len(d_paras) != len(r_paras):
        ok = False
        print("  PARAGRAPH COUNT DIFFERS")
    for i, (a, b) in enumerate(zip(d_paras, r_paras)):
        if a != b:
            ok = False
            print(f"  para {i} differs:\n    delivered: {a[:120]}\n    rebuilt  : {b[:120]}")
    if len(d_tables) != len(r_tables):
        ok = False
        print("  TABLE COUNT DIFFERS")
    for t, (a, b) in enumerate(zip(d_tables, r_tables)):
        if a != b:
            ok = False
            for r, (ra, rb) in enumerate(zip(a, b)):
                if ra != rb:
                    print(f"  table {t} row {r} differs:\n    delivered: {ra}\n    rebuilt  : {rb}")
                    break
    print(f"  => {'IDENTICAL' if ok else 'DIFFERENCES FOUND'}")
    return ok


def csv_cell(path: Path, **filters: str) -> dict[str, str]:
    import csv

    with path.open(encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh):
            if all(str(row.get(k)) == str(v) for k, v in filters.items()):
                return row
    return {}


def spot_checks(delivered: Path) -> bool:
    import csv

    text = "\n".join(p.text for p in Document(str(delivered)).paragraphs)
    table_text = "\n".join(
        c.text for t in Document(str(delivered)).tables for row in t.rows for c in row.cells
    )
    body = text + "\n" + table_text
    ok = True

    ranking = ROOT / "outputs" / "tables" / "event_ranking_metrics.csv"
    row = csv_cell(ranking, label="mod_opinion", model="finance-only IF")
    if row:
        auc = f"{float(row['auc']):.3f}"
        hit = auc in table_text
        print(f"  AUC opinion finance-only {auc}: {'found' if hit else 'MISSING'} in tables")
        ok &= hit

    row = csv_cell(ranking, label="mod_opinion", model="Beneish M-Score")
    if row:
        auc = f"{float(row['auc']):.3f}"
        hit = auc in table_text
        print(f"  AUC opinion Beneish {auc}: {'found' if hit else 'MISSING'} in tables")
        ok &= hit

    topk = ROOT / "outputs" / "tables" / "topk_metrics.csv"
    row = csv_cell(topk, benchmark="calibrated", model="if_finance", k="0.1")
    if row:
        enr = f"{float(row['enrichment']):.3f}"
        hit = enr in table_text
        print(f"  calibrated enrichment finance top-10% {enr}: {'found' if hit else 'MISSING'}")
        ok &= hit

    for needle in ("5.6 From the First", "5.7 External Validation", "Table 5.5", "Table 5.6"):
        hit = needle in body
        print(f"  section marker '{needle}': {'found' if hit else 'MISSING'}")
        ok &= hit

    return ok


def pdf_pages(path: Path) -> int | None:
    try:
        from pypdf import PdfReader

        return len(PdfReader(str(path)).pages)
    except Exception as exc:  # pragma: no cover
        print(f"  (pypdf failed: {exc})")
        return None


def main() -> int:
    rebuild()  # writes outputs/.tmp/verify_en.docx and verify_cn.docx

    ok = True
    ok &= compare("EN", MANUSCRIPT / "Group12A2_Final_EN.docx", TMP / "verify_en.docx")
    ok &= compare("CN", MANUSCRIPT / "Group12A2_Final_CN.docx", TMP / "verify_cn.docx")

    print("\n[headline numbers against current tables]")
    ok &= spot_checks(MANUSCRIPT / "Group12A2_Final_EN.docx")

    print("\n[deliverables]")
    for name in (
        "Group12A2_Final_EN.docx",
        "Group12A2_Final_EN.pdf",
        "Group12A2_Final_CN.docx",
        "Group12A2_Final_CN.pdf",
    ):
        path = MANUSCRIPT / name
        if not path.exists():
            print(f"  MISSING {name}")
            ok = False
            continue
        mtime = datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
        extra = ""
        if path.suffix == ".pdf":
            pages = pdf_pages(path)
            extra = f", {pages} pages" if pages else ""
        print(f"  {name:<34} {path.stat().st_size/1024:6.0f} KB, {mtime}{extra}")

    print("\nRESULT:", "manuscripts match a fresh rebuild" if ok else "MISMATCH — rebuild needed")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
