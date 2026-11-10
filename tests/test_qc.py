# -*- coding: utf-8 -*-
"""
test_qc.py
Author: Group12A2 DSW Team
Purpose: Unit tests for src/features/qc.py.
Module: tests

Revision History
-----------------
2026-11-06  initial version.
2026-11-06  assert that unreadable-PDF rows remain visible as pdf_error QC issues.
"""
import pandas as pd

from src.features.qc import build_qc_report, classify_issue


def _frames() -> dict[int, pd.DataFrame]:
    return {
        2021: pd.DataFrame(
            {
                "symbol": ["000001", "000002", "000003", "000004"],
                "status": ["ok", "ok", "no_mda", "ok"],
                "n_tokens": [8000, 200, None, 5000],
            }
        ),
        2022: pd.DataFrame(
            {"symbol": ["000001", "000005"], "status": ["ok", "error"], "n_tokens": [7000, None]}
        ),
    }


def test_classify_issue_labels():
    assert classify_issue("ok", 5000) is None
    assert classify_issue("no_mda", None) == "no_mda"
    assert classify_issue("ok", 150) == "suspicious_short"
    assert classify_issue("error", None) == "error"
    assert classify_issue("pdf_error", None) == "pdf_error"


def test_pdf_error_is_emitted_to_qc_issues():
    frames = {
        2023: pd.DataFrame(
            {"symbol": ["600001"], "status": ["pdf_error"], "n_tokens": [None]}
        )
    }
    summary, issues = build_qc_report(frames)
    assert summary.loc[0, "issues"] == 1
    assert issues.loc[0, ["symbol", "fiscal_year", "issue"]].to_dict() == {
        "symbol": "600001", "fiscal_year": 2023, "issue": "pdf_error"
    }
    assert pd.isna(issues.loc[0, "n_tokens"])


def test_summary_and_issue_counts():
    summary, issues = build_qc_report(_frames())
    assert summary["fiscal_year"].tolist() == [2021, 2022]
    assert summary.loc[0, "total"] == 4 and summary.loc[0, "ok"] == 3
    assert summary.loc[0, "issues"] == 2
    assert summary.loc[1, "issues"] == 1
    assert len(issues) == 3
    assert set(issues["issue"]) == {"suspicious_short", "no_mda", "error"}


def test_audit_rows_join_as_issues_without_duplication():
    audit = pd.DataFrame(
        {
            "symbol": ["002177", "000001"],
            "fiscal_year": [2022, 2021],
            "status": ["mismatched_year", "ok"],
            "log_title": ["2021年年度报告（更新后）", "2021年年度报告"],
        }
    )
    _, issues = build_qc_report(_frames(), audit)
    joined = issues[issues["symbol"] == "002177"]
    assert len(joined) == 1 and joined.iloc[0]["issue"] == "download_mismatched_year"
    assert (issues["symbol"] == "000001").sum() == 0  # clean rows never become issues
