"""Tests for scripts/build_results_excel.py (results visualisation workbook).

Revision history
2026-11-22  created: sheet names, chart counts, headline cell values.
2026-11-22  added English-language workbook tests (--lang en).
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


def test_sheet_names(workbook):
    assert workbook.sheetnames == [
        "总览 Overview", "RQ1 主结果", "RQ2 可解释", "RQ3 稳健性",
        "§5.7 外部检验", "§5.6 两版对比", "说明 Notes",
    ]


def test_chart_counts(workbook):
    counts = {ws.title: len(ws._charts) for ws in workbook.worksheets}
    assert counts == {
        "总览 Overview": 0, "RQ1 主结果": 1, "RQ2 可解释": 2, "RQ3 稳健性": 0,
        "§5.7 外部检验": 2, "§5.6 两版对比": 1, "说明 Notes": 0,
    }


def test_overview_key_cells(workbook):
    ws = workbook["总览 Overview"]
    assert ws["B14"].value == "审查第一名（融合分数）"
    assert "600870" in ws["C14"].value
    assert ws["B16"].value == "一句话结论（诚实用语 · Honest phrasing）"


def test_rq1_rho_and_enrichment(workbook):
    ws = workbook["RQ1 主结果"]
    rho = {ws[f"B{r}"].value: ws[f"C{r}"].value for r in range(6, 10)}
    assert rho["Finance-only IF（仅财务）"] == -0.021
    assert rho["Text-only IF（仅文本）"] == -0.026
    assert rho["Fused IF（融合）"] == -0.018
    # enrichment table: header row 12, data rows 13-16; col C legacy, col D calibrated top-10%
    assert ws["C12"].value == "富集率·legacy(M>−1.78) top-10%"
    assert ws["D12"].value == "富集率·样本校准 top-10%"
    assert ws["C13"].value == 1.69
    assert ws["D13"].value == 2.446
    assert ws["D15"].value == 2.099


def test_external_supervised_row_alignment(workbook):
    ws = workbook["§5.7 外部检验"]
    # header row 19, finance row 20, text row 21, fused row 22
    assert [ws.cell(row=20, column=c).value for c in range(2, 11)] == [
        "仅财务 Finance", 0.865, "—", 0.861, "—", 0.672, "—", 0.671, "—",
    ]
    assert [ws.cell(row=22, column=c).value for c in range(2, 11)] == [
        "融合 Fused", 0.866, 0.002, 0.873, 0.012, 0.673, 0.001, 0.679, 0.008,
    ]


def test_delta_labels_distinct(workbook):
    ws = workbook["§5.7 外部检验"]
    labels = [ws[f"B{r}"].value for r in range(26, 34)]
    assert labels[:4] == ["窄非标·Logit", "窄非标·HGB", "宽非标·Logit", "宽非标·HGB"]


def test_lexicon_density_rows(workbook):
    ws = workbook["§5.6 两版对比"]
    row17 = [ws.cell(row=17, column=c).value for c in range(2, 6)]
    assert row17 == ["正面词", 10.29, 100.15, 9.73]
    row19 = [ws.cell(row=19, column=c).value for c in range(2, 6)]
    assert row19 == ["情感词合计", 13.41, 111.3, 8.3]


# ---- English workbook ------------------------------------------------------
def test_en_sheet_names(workbook_en):
    assert workbook_en.sheetnames == [
        "Overview", "RQ1 Main results", "RQ2 Explainability", "RQ3 Robustness",
        "5.7 External validation", "5.6 Two specifications", "Notes",
    ]


def test_en_chart_counts(workbook_en):
    counts = {ws.title: len(ws._charts) for ws in workbook_en.worksheets}
    assert counts == {
        "Overview": 0, "RQ1 Main results": 1, "RQ2 Explainability": 2, "RQ3 Robustness": 0,
        "5.7 External validation": 2, "5.6 Two specifications": 1, "Notes": 0,
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
    assert rho["Finance-only IF"] == -0.021
    assert rho["Text-only IF"] == -0.026
    assert rho["Fused IF"] == -0.018
    assert ws["C12"].value == "Enrichment · legacy (M>−1.78) top-10%"
    assert ws["D12"].value == "Enrichment · calibrated top-10%"
    assert ws["C13"].value == 1.69
    assert ws["D13"].value == 2.446


def test_en_external_rows(workbook_en):
    ws = workbook_en["5.7 External validation"]
    assert [ws.cell(row=20, column=c).value for c in range(2, 11)] == [
        "Finance", 0.865, "—", 0.861, "—", 0.672, "—", 0.671, "—",
    ]
    labels = [ws[f"B{r}"].value for r in range(26, 34)]
    assert labels[:4] == [
        "Opinion (narrow) · Logit", "Opinion (narrow) · HGB",
        "Opinion (wide) · Logit", "Opinion (wide) · HGB",
    ]


