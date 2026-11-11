#!/usr/bin/env python
"""Clean the workspace after the layout reorganisation.

Two kinds of leftovers are handled here:

1. ``_trash/`` — history moved out during the 2026-11-11 tidy-up; deleting it is
   irreversible, so the script only lists it unless ``--apply`` is given.
2. Locked ``*.univer`` scratch files — previous Univer sessions keep the file
   handles open, so these survive manual deletion until those processes close.

Usage::

    .venv\\Scripts\\python.exe scripts\\run_15_cleanup_workspace.py           # dry run
    .venv\\Scripts\\python.exe scripts\\run_15_cleanup_workspace.py --apply    # really delete

Exit codes: 0 = nothing left to do, 1 = items remain (dry run or locked).

Revision history
2026-11-11  created: report and remove _trash, scratch .univer files, caches.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

TRASH_DIR = PROJECT_ROOT / "_trash"
SCRATCH_DIR = PROJECT_ROOT / "outputs" / ".tmp"
CACHE_DIRS = (
    PROJECT_ROOT / ".pytest_cache",
    PROJECT_ROOT / "scripts" / "__pycache__",
    PROJECT_ROOT / "src" / "__pycache__",
    PROJECT_ROOT / "tests" / "__pycache__",
)
# Locked duplicates of the course bundle: identical copies live in course_materials/.
DUPLICATE_UNIVER = (
    PROJECT_ROOT / "course_paper_materials.univer",
    PROJECT_ROOT / "grading_rubric.univer",
)


def _size_mb(path: Path) -> float:
    if path.is_file():
        return path.stat().st_size / 1024**2
    total = sum(p.stat().st_size for p in path.rglob("*") if p.is_file())
    return total / 1024**2


def _remove(path: Path, apply: bool) -> tuple[bool, str]:
    """Delete one file or directory; return (success, message)."""
    label = f"{path.relative_to(PROJECT_ROOT)} ({_size_mb(path):.1f} MB)"
    if not apply:
        return False, f"would delete {label}"
    try:
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()
    except PermissionError:
        return False, f"LOCKED  {label} — close the program holding it, then re-run"
    except OSError as exc:  # pragma: no cover - unusual filesystem error
        return False, f"FAILED  {label} — {exc}"
    return True, f"deleted {label}"


def duplicates_are_safe() -> bool:
    """True when every root ``.univer`` has an identically sized copy in course_materials/."""
    safe = True
    for path in DUPLICATE_UNIVER:
        if not path.exists():
            continue
        copy = PROJECT_ROOT / "course_materials" / path.name
        if not copy.exists() or copy.stat().st_size != path.stat().st_size:
            print(f"  keep     {path.name} — no matching copy in course_materials/")
            safe = False
    return safe


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="actually delete (default: dry run)")
    args = parser.parse_args()

    print(f"workspace: {PROJECT_ROOT}")
    print(f"mode     : {'APPLY' if args.apply else 'DRY RUN'}\n")

    remaining = 0

    if TRASH_DIR.exists():
        print("[1] _trash/")
        ok, msg = _remove(TRASH_DIR, args.apply)
        print(f"  {msg}")
        remaining += 0 if ok else 1
    else:
        print("[1] _trash/ — already gone")

    print("\n[2] scratch .univer files left by Univer sessions")
    scratch = sorted(SCRATCH_DIR.glob("*.univer")) if SCRATCH_DIR.exists() else []
    if not scratch:
        print("  none")
    for path in scratch:
        ok, msg = _remove(path, args.apply)
        print(f"  {msg}")
        remaining += 0 if ok else 1

    print("\n[3] root duplicates of the course bundle")
    if duplicates_are_safe():
        for path in DUPLICATE_UNIVER:
            if path.exists():
                ok, msg = _remove(path, args.apply)
                print(f"  {msg}")
                remaining += 0 if ok else 1
    else:
        print("  skipped — duplicate check failed")
        remaining += 1

    print("\n[4] caches")
    for path in CACHE_DIRS:
        if path.exists():
            ok, msg = _remove(path, args.apply)
            print(f"  {msg}")
            remaining += 0 if ok else 1
    if not any(p.exists() for p in CACHE_DIRS):
        print("  none")

    print("\n[5] empty scratch directory")
    if SCRATCH_DIR.exists() and not any(SCRATCH_DIR.iterdir()):
        if args.apply:
            SCRATCH_DIR.rmdir()
            print("  removed outputs/.tmp/")
        else:
            print("  would remove outputs/.tmp/ (empty)")

    if remaining:
        print(f"\n{remaining} item(s) still pending" + ("" if args.apply else " (dry run)"))
        return 1
    print("\nworkspace clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
