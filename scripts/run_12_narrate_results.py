"""run_12_narrate_results.py

File:     scripts/run_12_narrate_results.py
Author:   Group12A2 DSW Team
Purpose:  emit the auto-narrated English Results section for the experiment
          chapter from the pipeline tables.
Module:   scripts (reporting drivers)

Revision History:
  2026-11-06  initial version.
"""
import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import OUTPUTS, TABLES  # noqa: E402
from src.reporting.narrate_results import build_results_narrative  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tables", default=str(TABLES),
                        help="directory with pipeline output tables")
    parser.add_argument("--descriptives",
                        default=str(OUTPUTS / "reports" / "descriptives_summary.md"),
                        help="optional descriptives report path")
    parser.add_argument("--out",
                        default=str(OUTPUTS / "reports" / "results_narrative.md"))
    args = parser.parse_args()

    try:
        text = build_results_narrative(args.tables, args.descriptives)
    except FileNotFoundError as exc:
        print(f"[run_12] prerequisite data not ready: {exc}", flush=True)
        return 2
    Path(args.out).write_text(text, encoding="utf-8")
    print(f"[run_12] wrote {args.out} ({len(text)} chars)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
