# -*- coding: utf-8 -*-
"""
test_event_parser.py
Author: Group12A2 DSW Team
Purpose: Tests for the CSMAR audit-opinion and violation parsers, including the
         regression case where "标准无保留意见" contains the substring
         "保留意见" and must not be classified as a modified opinion.
Module: tests
"""
import pandas as pd
import pytest

from src.data_ingestion.event_parser import (
    build_event_table,
    classify_opinion,
    event_summary,
    parse_audit_opinions,
    parse_violations,
)


@pytest.mark.parametrize(
    "text,expected",
    [
        ("标准无保留意见", "standard"),
        ("带有解释性说明的无保留意见", "emphasis"),
        ("带强调事项段的无保留意见", "emphasis"),
        ("保留意见", "qualified"),
        ("保留意见加事项段", "qualified_emphasis"),
        ("无法表示意见", "disclaimer"),
        ("否定意见", "adverse"),
        ("", "unknown"),
        (None, "unknown"),
    ],
)
def test_classify_opinion(text, expected):
    assert classify_opinion(text) == expected


def test_standard_opinion_is_not_modified():
    """Regression: "无保留意见" must not be caught by the "保留意见" branch."""
    assert classify_opinion("标准无保留意见") == "standard"


def _audit_frame():
    return pd.DataFrame(
        {
            "symbol": ["000001", "000002", "000003", "000004"],
            "fiscal_year": [2021, 2022, 2023, 2021],
            "accper": ["2021-12-31"] * 4,
            "announce_date": ["2022-04-01"] * 4,
            "audit_type": [
                "标准无保留意见",
                "保留意见",
                "无法表示意见",
                "带有解释性说明的无保留意见",
            ],
            "opinion_class": ["standard", "qualified", "disclaimer", "emphasis"],
            "mod_opinion": [0, 1, 1, 0],
            "mod_opinion_wide": [0, 1, 1, 1],
            "auditor": ["天健", "普华永道中天", "立信", "德勤华永"],
            "big4": [0, 1, 0, 1],
            "audit_fee": [100.0, 200.0, 150.0, 300.0],
        }
    )


def _violation_frame():
    return pd.DataFrame(
        {
            "symbol": ["000002", "000002", "000003"],
            "violation_id": ["V1", "V2", "V3"],
            "declare_date": pd.to_datetime(["2022-05-01", "2022-05-01", "2023-07-01"]),
            "declare_year": [2022, 2022, 2023],
            "violation_type": ["推迟披露", "违规买卖股票", "重大遗漏"],
            "violation_type_ids": ["P2504", "P2512", "P2505"],
            "is_disclosure": [1, 0, 1],
        }
    )


def test_build_event_table_aligns_violations_to_t_plus_1():
    sample = pd.DataFrame(
        {
            "symbol": ["000001", "000002", "000003"],
            "fiscal_year": [2021, 2021, 2022],
        }
    )
    table = build_event_table(sample, audit=_audit_frame(), violations=_violation_frame())
    # 000002 has one disclosure and one non-disclosure announcement in 2022,
    # which is t+1 for fiscal year 2021.
    row = table[(table["symbol"] == "000002") & (table["fiscal_year"] == 2021)].iloc[0]
    assert row["violation_any_t1"] == 1
    assert row["violation_disclosure_t1"] == 1
    # 000003 has the 2023 announcement, which is t+1 for fiscal year 2022.
    row = table[(table["symbol"] == "000003") & (table["fiscal_year"] == 2022)].iloc[0]
    assert row["violation_any_t1"] == 1
    assert row["violation_disclosure_t1"] == 1
    # 000001 has no announcement.
    row = table[table["symbol"] == "000001"].iloc[0]
    assert row["violation_any_t1"] == 0


def test_build_event_table_flags_missing_audit_records():
    sample = pd.DataFrame({"symbol": ["000999"], "fiscal_year": [2021]})
    table = build_event_table(
        sample, audit=_audit_frame(), violations=_violation_frame()
    )
    row = table.iloc[0]
    assert row["has_audit_record"] == 0
    assert row["opinion_class"] == "missing"
    assert row["mod_opinion"] == 0


def test_event_summary_reports_rates():
    sample = pd.DataFrame(
        {
            "symbol": ["000001", "000002", "000003", "000004"],
            "fiscal_year": [2021, 2022, 2023, 2021],
        }
    )
    table = build_event_table(sample, audit=_audit_frame(), violations=_violation_frame())
    summary = event_summary(table)
    assert summary["n_firm_years"] == 4
    assert summary["n_firms"] == 4
    assert summary["mod_opinion_count"] == 2
    assert summary["mod_opinion_rate"] == pytest.approx(0.5)
    assert summary["mod_opinion_wide_count"] == 3
    assert "by_year" in summary


def _write_export(path, header, rows):
    """Write a CSMAR-style export: code row, Chinese label row, unit row, data."""
    label_row = ["证券代码", "证券简称", "会计截止日期", "审计意见类型"][: len(header)]
    unit_row = ["没有单位"] * len(header)
    frame = pd.DataFrame([label_row, unit_row] + rows, columns=header)
    frame.to_excel(path, index=False, sheet_name="sheet1")
    return path


def test_parse_audit_opinions_skips_label_rows(tmp_path):
    path = _write_export(
        tmp_path / "FIN_Audit.xlsx",
        ["Stkcd", "Accper", "Audittyp", "Auditor"],
        [["000001", "2021-12-31", "标准无保留意见", "天健"],
         ["2", "2021-12-31", "保留意见", "立信"]],
    )
    frame = parse_audit_opinions(path)
    assert len(frame) == 2
    assert set(frame["symbol"]) == {"000001", "000002"}
    assert frame.loc[frame["symbol"] == "000001", "mod_opinion"].iloc[0] == 0
    assert frame.loc[frame["symbol"] == "000002", "mod_opinion"].iloc[0] == 1
    assert frame["fiscal_year"].tolist() == [2021, 2021]


def test_parse_violations_flags_disclosure_types(tmp_path):
    path = _write_export(
        tmp_path / "STK_Violation_Main.xlsx",
        ["ViolationID", "Symbol", "DeclareDate", "ViolationType", "ViolationTypeID"],
        [["V1", "000001", "2022-05-01", "推迟披露", "P2504"],
         ["V2", "2", "2022-06-01", "违规买卖股票", "P2512"]],
    )
    frame = parse_violations(path)
    assert len(frame) == 2
    assert set(frame["symbol"]) == {"000001", "000002"}
    assert frame["is_disclosure"].sum() == 1
    assert frame["declare_year"].tolist() == [2022, 2022]
