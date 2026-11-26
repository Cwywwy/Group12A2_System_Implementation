"""Tests for scripts/build_results_excel.py (results visualisation workbook).

Revision history
2026-11-22  created: sheet names, chart counts, headline cell values.
2026-11-22  added English-language workbook tests (--lang en).
2026-11-26  retarget the fixtures at the five-year panel: six sheets (the v0.1
            comparison sheet was dropped), live p-values, and the settled
            forward-label window.
"""

import importlib.util
from pathlib import Path

import pytest
from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "build_results_excel.py"

spec = importlib.util.spec_from_file_location("build_results_excel", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


@pytest.fixture(scope="module")
def workbook(tmp_path_factory):
    out = tmp_path_factory.mktemp("excel") / "results.xlsx"
    module.build(out)
    return load_workbook(out)


@pytest.fixture(scope="module")
def workbook_en(tmp_path_factory):
    out = tmp_path_factory.mktemp("excel_en") / "results_en.xlsx"
    module.build(out, lang="en")
    return load_workbook(out)


def row(ws, index, start=2, stop=11):
    return [ws.cell(row=index, column=col).value for col in range(start, stop)]


# ---- Chinese workbook ------------------------------------------------------
def test_sheet_names(workbook):
    assert workbook.sheetnames == [
        "总览 Overview", "RQ1 主结果", "RQ2 可解释", "RQ3 稳健性",
        "§5.6 外部检验", "说明 Notes",
    ]


def test_chart_counts(workbook):
    counts = {ws.title: len(ws._charts) for ws in workbook.worksheets}
    assert counts == {
        "总览 Overview": 0, "RQ1 主结果": 1, "RQ2 可解释": 2,
        "RQ3 稳健性": 0, "§5.6 外部检验": 2, "说明 Notes": 0,
    }


def test_overview_key_cells(workbook):
    ws = workbook["总览 Overview"]
    assert ws["B14"].value == "审查第一名（融合分数）"
    assert "600870" in ws["C14"].value
    assert ws["B16"].value == "一句话结论（诚实用语 · Honest phrasing）"


def test_rq1_rho_and_p_values(workbook):
    ws = workbook["RQ1 主结果"]
    rho = {ws[f"B{r}"].value: (ws[f"C{r}"].value, ws[f"D{r}"].value)
           for r in range(6, 10)}
    assert rho["Finance-only IF（仅财务）"] == (-0.033, "< 0.001")
    assert rho["Text-only IF（仅文本）"] == (-0.021, "0.008")
    assert rho["Fused IF（融合）"] == (-0.019, "0.014")
    assert rho["Fused AE（自编码器）"] == (-0.026, "0.001")


def test_rq1_enrichment(workbook):
    ws = workbook["RQ1 主结果"]
    assert ws["C12"].value == "富集率·legacy(M>−1.78) top-10%"
    assert ws["D12"].value == "富集率·样本校准 top-10%"
    assert row(ws, 13, 3, 7) == [2.033, 2.541, 2.317, 2.438]
    assert ws["D15"].value == 2.23


def test_external_event_table_uses_settled_window(workbook):
    ws = workbook["§5.6 外部检验"]
    header = row(ws, 5)
    assert header[:3] == ["事件标签", "事件数", "事件率"]
    assert header[3:8] == ["2021", "2022", "2023", "2024", "2025"]
    violation = row(ws, 8)
    assert violation[0] == "t+1 违规（任意类型）"
    assert violation[1] == 1965
    assert violation[2] == pytest.approx(0.2127, abs=5e-4)
    # the forward window is settled only through 2023
    assert violation[6:8] == ["—", "—"]
    opinion = row(ws, 6)
    assert opinion[1] == 322
    assert opinion[6] is not None and opinion[7] is not None


def test_external_supervised_row_alignment(workbook):
    ws = workbook["§5.6 外部检验"]
    assert row(ws, 20) == [
        "仅财务 Finance", 0.865, "—", 0.859, "—", 0.672, "—", 0.671, "—",
    ]
    assert row(ws, 22) == [
        "融合 Fused", 0.864, 0, 0.863, 0.004, 0.673, 0.001, 0.679, 0.008,
    ]


def test_delta_labels_distinct(workbook):
    ws = workbook["§5.6 外部检验"]
    labels = [ws[f"B{r}"].value for r in range(26, 34)]
    assert labels[:4] == ["窄非标·Logit", "窄非标·HGB", "宽非标·Logit", "宽非标·HGB"]
    assert labels[4] == "任意违规·Logit"
    assert labels[6] == "披露违规·Logit"


def test_rq3_year_table_spans_five_years(workbook):
    ws = workbook["RQ3 稳健性"]
    assert row(ws, 15)[:6] == ["模型", "2021", "2022", "2023", "2024", "2025"]
    finance = row(ws, 16)
    assert finance[0] == "Finance-only IF（仅财务）"
    assert finance[1:6] == pytest.approx([-0.011, -0.006, -0.037, -0.040, -0.049])


# ---- English workbook ------------------------------------------------------
def test_en_sheet_names(workbook_en):
    assert workbook_en.sheetnames == [
        "Overview", "RQ1 Main results", "RQ2 Explainability", "RQ3 Robustness",
        "5.6 External validation", "Notes",
    ]


def test_en_chart_counts(workbook_en):
    counts = {ws.title: len(ws._charts) for ws in workbook_en.worksheets}
    assert counts == {
        "Overview": 0, "RQ1 Main results": 1, "RQ2 Explainability": 2,
        "RQ3 Robustness": 0, "5.6 External validation": 2, "Notes": 0,
    }


def test_en_overview_key_cells(workbook_en):
    ws = workbook_en["Overview"]
    assert "Results at a Glance" in ws["B2"].value
    assert ws["B14"].value == "Top case under review (fused score)"
    assert "600870" in ws["C14"].value
    assert ws["B16"].value == "One-line conclusion (honest phrasing)"


def test_en_rq1_headers_and_values(workbook_en):
    ws = workbook_en["RQ1 Main results"]
    rho = {ws[f"B{r}"].value: ws[f"C{r}"].value for r in range(6, 10)}
    assert rho["Finance-only IF"] == -0.033
    assert rho["Text-only IF"] == -0.021
    assert rho["Fused IF"] == -0.019
    assert ws["C12"].value == "Enrichment · legacy (M>−1.78) top-10%"
    assert ws["D12"].value == "Enrichment · calibrated top-10%"
    assert ws["C13"].value == 2.033
    assert ws["D13"].value == 2.541


def test_en_external_rows(workbook_en):
    ws = workbook_en["5.6 External validation"]
    assert row(ws, 20) == [
        "Finance", 0.865, "—", 0.859, "—", 0.672, "—", 0.671, "—",
    ]
    labels = [ws[f"B{r}"].value for r in range(26, 34)]
    assert labels[:4] == [
        "Opinion (narrow) · Logit", "Opinion (narrow) · HGB",
        "Opinion (wide) · Logit", "Opinion (wide) · HGB",
    ]
