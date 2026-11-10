# -*- coding: utf-8 -*-
"""
qc.py
Author: Group12A2 DSW Team
Purpose: Quality-control aggregation over the yearly text-feature frames and the
         download audit (missing / suspicious / mismatched firm-years).
Module: src/features

build_qc_report is pure (DataFrame in, DataFrames out) so it can be unit-tested;
scripts/run_08_qc_report.py is the thin CLI wrapper that reads the real files.

Revision History
-----------------
2026-11-06  initial version.
"""
import pandas as pd

from src.features.feature_table import MIN_MDA_TOKENS


def classify_issue(status: str, n_tokens: float | None) -> str | None:
    """Return the QC issue label for one row, or None when the row is clean."""
    status = str(status)
    if status != "ok":
        return "no_mda" if status == "no_mda" else status
    if n_tokens is None or pd.isna(n_tokens):
        return "missing"
    if float(n_tokens) < MIN_MDA_TOKENS:
        return "suspicious_short"
    return None


def build_qc_report(text_frames: dict[int, pd.DataFrame], audit: pd.DataFrame | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Aggregate per-year totals and per-row issues; optionally join audit rows.

    text_frames: {fiscal_year: DataFrame with columns symbol, status, n_tokens}
    audit: optional download audit with columns symbol, fiscal_year, status, log_title.
    Returns (summary, issues): summary = one row per year (total/ok/suspicious/missing);
    issues = every non-clean row plus audit rows not present in the text frames.
    """
    summary_rows = []
    issue_rows = []
    known_keys: set[tuple[str, int]] = set()
    for year in sorted(text_frames):
        frame = text_frames[year].copy()
        total = int(len(frame))
        ok = int((frame["status"] == "ok").sum()) if "status" in frame else 0
        issues = []
        for _, row in frame.iterrows():
            symbol = str(row.get("symbol", "")).zfill(6)
            issue = classify_issue(row.get("status", "ok"), row.get("n_tokens"))
            if issue:
                issues.append(
                    {"symbol": symbol, "fiscal_year": year, "issue": issue,
                     "n_tokens": row.get("n_tokens")}
                )
                known_keys.add((symbol, year))
        summary_rows.append(
            {"fiscal_year": year, "total": total, "ok": ok,
             "issues": len(issues), "issue_share": round(len(issues) / total, 4) if total else 0.0}
        )
        issue_rows.extend(issues)

    if audit is not None and {"symbol", "fiscal_year", "status"}.issubset(audit.columns):
        for _, row in audit.iterrows():
            if str(row.get("status")) in ("ok", "cached", "downloaded", "missing_download"):
                continue
            symbol, year = str(row.get("symbol", "")).zfill(6), int(row.get("fiscal_year"))
            if (symbol, year) in known_keys:
                continue
            issue_rows.append(
                {"symbol": symbol, "fiscal_year": year, "issue": f"download_{row.get('status')}",
                 "n_tokens": None}
            )

    summary = pd.DataFrame(summary_rows)
    issues = pd.DataFrame(issue_rows).sort_values(["fiscal_year", "symbol"]).reset_index(drop=True)
    return summary, issues
