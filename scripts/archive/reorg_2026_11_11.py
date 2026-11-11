"""One-off layout reorganisation for the DSW project (2026-11-11)."""

from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

moves: list[tuple[str, str]] = [
    # --- course materials -------------------------------------------------
    ("course_paper_materials.univer", "course_materials/course_paper_materials.univer"),
    ("grading_rubric.univer", "course_materials/grading_rubric.univer"),
    (
        "Grading and Report Requirement for FinTech 2026-Modified.docx",
        "course_materials/Grading and Report Requirement for FinTech 2026-Modified.docx",
    ),
    (
        "Financial_Disclosure_Quality_Assessment_English_Outline(1).docx",
        "course_materials/Financial_Disclosure_Quality_Assessment_English_Outline(1).docx",
    ),
    ("Copyright notice.pdf", "course_materials/Copyright notice.pdf"),
    # --- listed-company list is a data source ----------------------------
    ("STK_LISTEDCOINFOANL.xlsx", "data/raw/csmar/STK_LISTEDCOINFOANL.xlsx"),
    ("STK_LISTEDCOINFOANL[DES][xlsx].txt", "data/raw/csmar/STK_LISTEDCOINFOANL[DES][xlsx].txt"),
    # --- first version (v0.1) ---------------------------------------------
    (
        "data/external/dictionaries/v0.1_bootstrap_backup",
        "data/archive_v0.1/dictionaries",
    ),
    ("data/interim/v0.1_text_features_backup", "data/archive_v0.1/text_features"),
    ("data/processed/v0.1_feature_table.csv", "data/archive_v0.1/feature_table.csv"),
    ("outputs/.tmp/v01_dual_benchmark/tables", "outputs/archive_v0.1/tables"),
    ("outputs/.tmp/v01_prev_run", "outputs/archive_v0.1/prev_run"),
    # --- branches ---------------------------------------------------------
    ("outputs/reports/positive_result_branches.md", "outputs/branches/positive_result_branches.md"),
    (
        "outputs/reports/branch2_inquiry_crawler_spec.md",
        "outputs/branches/branch2_inquiry_crawler_spec.md",
    ),
    ("outputs/reports/event_branch_results.md", "outputs/branches/event_branch_results.md"),
    (
        "outputs/tables/branch_component_correlations.csv",
        "outputs/branches/branch_component_correlations.csv",
    ),
    # --- junk to trash ----------------------------------------------------
    ("outputs/.tmp", "_trash/outputs_tmp"),
    ("outputs/slides_preview", "_trash/slides_preview"),
    ("docs/slides", "_trash/docs_slides"),
    ("docs/CSMAR guide.docx", "_trash/CSMAR guide.docx"),
    (
        "Group12A2 Screening Financial Disclosure Risk through Textual-Financial Feature "
        "Fusion and Explainable Anomaly Detection Evidence from Chinese A-share "
        "Manufacturing Firms, 2021–2023.docx",
        "_trash/old_submission_copy.docx",
    ),
]


def run() -> int:
    done = 0
    locked: list[str] = []
    for src_rel, dst_rel in moves:
        if any(ch in src_rel for ch in "*?"):
            matches = sorted(ROOT.glob(src_rel))
            src = matches[0] if matches else ROOT / src_rel
        else:
            src = ROOT / src_rel
        dst = ROOT / dst_rel
        if not src.exists():
            print(f"[skip] {src_rel} (absent)")
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.exists():
            print(f"[skip] {dst_rel} (target exists)")
            continue
        try:
            shutil.move(str(src), str(dst))
        except PermissionError as exc:
            print(f"[LOCK] {src_rel} -> {dst_rel} : {exc}")
            locked.append(src_rel)
            continue
        print(f"[move] {src_rel} -> {dst_rel}")
        done += 1
    for junk in (".pytest_cache",):
        target = ROOT / junk
        if target.exists():
            shutil.rmtree(target, ignore_errors=True)
            print(f"[rm]   {junk}")
            done += 1
    for cache in ROOT.rglob("__pycache__"):
        if ".venv" in cache.parts or "_trash" in cache.parts:
            continue
        shutil.rmtree(cache, ignore_errors=True)
    print(f"done: {done} operations")
    if locked:
        print("still locked (close the program holding them):")
        for item in locked:
            print(f"  - {item}")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
