"""run_99_full_pipeline.py

File:     scripts/run_99_full_pipeline.py
Author:   Group12A2 DSW Team
Purpose:  one-click orchestrator running the analysis stages in order; used by
          the team handoff so every stage is executed exactly as documented.
Module:   scripts (orchestration)

Revision History:
  2026-11-06  initial version: sequential stages with stage filter and runbook log.
"""
import argparse
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

PY = sys.executable
RUN = PROJECT_ROOT / "scripts"
OUT = PROJECT_ROOT / "outputs" / "reports"
OUT.mkdir(parents=True, exist_ok=True)

STAGES = [
    ("01_sample", [str(RUN / "run_01_sample.py")]),
    ("03_finance", [str(RUN / "run_03_build_finance_intermediate.py")]),
    ("04_audit", [str(RUN / "run_04_audit_downloads.py")]),
    ("05_extract", [str(RUN / "run_05_extract_mda_features.py")]),
    ("08_qc", [str(RUN / "run_08_qc_report.py")]),
    ("06_features", [str(RUN / "run_06_build_feature_table.py")]),
    ("11_descriptives", [str(RUN / "run_11_descriptives.py")]),
    ("07_experiment", [str(RUN / "run_07_experiment.py")]),
    ("12_narrate", [str(RUN / "run_12_narrate_results.py")]),
]


def _run_stage(name: str, argv: list[str], years: list[int] | None) -> str:
    """Return 'ok', 'skip' (prerequisite missing, stage exited 2), or 'fail'."""
    t0 = time.time()
    print(f"\n=== [{name}] start ===", flush=True)
    if name == "05_extract":
        cmds = [[argv[0], "--year", str(y)] for y in years]
    else:
        cmds = [argv]
    status = "ok"
    for cmd in cmds:
        print(f"[run_99] exec: {PY} {' '.join(cmd)}", flush=True)
        # stdout is streamed directly (no pipe capture) so long stages stay live.
        proc = subprocess.run([PY, *cmd], cwd=PROJECT_ROOT)
        if proc.returncode not in (0, 2):
            print(f"=== [{name}] FAILED (exit {proc.returncode}) ===", flush=True)
            return "fail"
        if proc.returncode == 2:
            print(f"[run_99] {name} skipped itself: prerequisite data not ready.", flush=True)
            status = "skip"
    print(f"=== [{name}] {status} in {time.time() - t0:.0f}s ===", flush=True)
    return status


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--stage", nargs="+", default=None,
        help="run only the named stage(s), e.g. --stage 06_features 11_descriptives",
    )
    parser.add_argument("--years", nargs="+", type=int, default=[2021, 2022, 2023],
                        help="fiscal years for 05_extract (default 2021 2022 2023)")
    parser.add_argument("--skip-05", action="store_true",
                        help="skip the long MD&A extraction stage (hours)")
    args = parser.parse_args()

    selected = args.stage or [name for name, _ in STAGES]
    runbook = OUT / "pipeline_runbook.md"
    lines = ["# Pipeline Runbook", "",
             f"- started: {time.strftime('%Y-%m-%d %H:%M:%S')}",
             f"- python: {PY}", f"- stages selected: {', '.join(selected)}", ""]

    ok = True
    for name, argv in STAGES:
        if name not in selected:
            continue
        if name == "05_extract" and args.skip_05:
            lines.append(f"- {name}: SKIPPED (--skip-05)")
            continue
        status = _run_stage(name, argv, args.years)
        if status == "fail":
            ok = False
        lines.append(f"- {name}: {status} at {time.strftime('%H:%M:%S')}")

    lines.append("")
    lines.append("- finished: " + time.strftime("%Y-%m-%d %H:%M:%S"))
    runbook.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n[run_99] runbook: {runbook}", flush=True)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
