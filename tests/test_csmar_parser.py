# -*- coding: utf-8 -*-
"""
test_csmar_parser.py
Author: Group12A2 DSW Team
Purpose: Tests for the tolerant CSMAR three-table parser.
Module: tests

Fixtures mimic CSMAR exports: header not on row 1, mixed parent/consolidated
rows, date strings in several formats, thousands separators in numbers.

Revision History
-----------------
2026-11-05  initial version.
"""
import pandas as pd

from src.data_ingestion.csmar_parser import (
    build_finance_intermediate,
    read_csmar_table,
)


def _write_balance(tmp_path):
    rows = [
        ["公司研究系列财务报表", "", ""],
        ["证券代码", "报告期", "报表类型", "资产总计", "负债合计", "流动资产合计",
         "流动负债合计", "应收账款净额", "固定资产净额", "长期借款", "货币资金"],
        ["000001", "2020-12-31", "合并报表", "1,000", "500", "400", "300", "50", "200", "30", "80"],
        ["000001", "2020-12-31", "母公司报表", "700", "350", "280", "210", "35", "140", "20", "60"],
        ["000002", "20201231", "合并报表", "2,000", "900", "800", "600", "90", "400", "60", "150"],
    ]
    path = tmp_path / "FS_Combas.xlsx"
    pd.DataFrame(rows).to_excel(path, index=False, header=False)
    return path


def _write_income(tmp_path):
    rows = [
        ["证券代码", "报告期", "报表类型", "营业收入", "营业成本", "销售费用", "管理费用", "净利润"],
        ["000001", "2020/12/31", "合并", "3,000", "2,100", "120", "180", "300"],
        ["000001", "2020-12-31", "母公司", "2,000", "1,400", "80", "120", "200"],
        ["000002", "2020-12-31", "合并", "5,000", "3,600", "200", "300", "500"],
    ]
    path = tmp_path / "FS_Comins.xlsx"
    pd.DataFrame(rows).to_excel(path, index=False, header=False)
    return path


def _write_cashflow(tmp_path):
    rows = [
        ["证券代码", "报告期", "报表类型", "经营活动产生的现金流量净额", "固定资产折旧"],
        ["000001", "2020-12-31", "A", "400", "60"],
        ["000001", "2020-12-31", "B", "250", "40"],
        ["000002", "2020-12-31", "A", "800", "100"],
    ]
    path = tmp_path / "FS_Comscfd.xlsx"
    pd.DataFrame(rows).to_excel(path, index=False, header=False)
    return path


def test_balance_header_offset_and_parent_filter(tmp_path):
    table = read_csmar_table(_write_balance(tmp_path))
    assert len(table) == 2
    assert list(table["symbol"]) == ["000001", "000002"]
    assert list(table["fiscal_year"]) == [2020, 2020]
    assert table.iloc[0]["total_assets"] == 1000
    assert table.iloc[1]["receivables"] == 90


def test_income_sga_sums_sales_and_admin(tmp_path):
    table = read_csmar_table(_write_income(tmp_path))
    assert len(table) == 2
    assert table.iloc[0]["sga"] == 300
    assert table.iloc[1]["revenue"] == 5000


def test_cashflow_date_variants_and_markers(tmp_path):
    table = read_csmar_table(_write_cashflow(tmp_path))
    assert len(table) == 2
    assert table.iloc[0]["ocf"] == 400
    assert table.iloc[1]["depreciation"] == 100


def test_build_finance_intermediate_merges_three_tables(tmp_path):
    merged = build_finance_intermediate(
        _write_balance(tmp_path), _write_income(tmp_path), _write_cashflow(tmp_path)
    )
    assert list(merged.columns) == ["symbol", "fiscal_year", "revenue", "cogs", "total_assets",
                                    "total_liabilities", "current_assets", "current_liabilities",
                                    "receivables", "fixed_assets", "long_term_debt", "cash",
                                    "depreciation", "sga", "net_income", "ocf"]
    assert len(merged) == 2
    row1 = merged[merged["symbol"] == "000001"].iloc[0]
    assert row1["total_assets"] == 1000
    assert row1["sga"] == 300
    assert row1["ocf"] == 400


def _write_modern_balance(tmp_path):
    """Modern CSMAR layout: code row, English name row, unit row, then data."""
    code_row = ["Stkcd", "Accper", "Typrep", "A001101000", "A001111000", "A001100000",
                "A001212000", "A001000000", "A002100000", "A002201000", "A002000000",
                "A999999000"]
    name_row = ["Stock Code", "Ending Date of Statistics", "Statement Type",
                "Cash and Cash Equivalents", "Net Accounts Receivable",
                "Total Current Assets", "Net Fixed Assets", "Total Assets",
                "Total Current Liabilities", "Long-term Loans", "Total Liabilities",
                "Unused Item"]
    unit_row = ["No Unit ", "No Unit ", "No Unit ", "CNY", "CNY", "CNY", "CNY", "CNY",
                "CNY", "CNY", "CNY", "CNY"]
    rows = [
        code_row,
        name_row,
        unit_row,
        ["1", "2020-12-31", "A", "80", "50", "400", "200", "1000", "300", "30", "500", "9"],
        ["1", "2020-12-31", "B", "60", "35", "280", "140", "700", "210", "20", "350", "8"],
        ["2", "20201231", "A", "150", "90", "800", "400", "2000", "600", "60", "900", "7"],
    ]
    path = tmp_path / "FS_Combas_modern.xlsx"
    pd.DataFrame(rows).to_excel(path, index=False, header=False)
    return path


def test_modern_code_header_with_name_and_unit_rows(tmp_path):
    table = read_csmar_table(_write_modern_balance(tmp_path))
    assert len(table) == 2
    assert list(table["symbol"]) == ["000001", "000002"]
    assert list(table["fiscal_year"]) == [2020, 2020]
    assert table.iloc[0]["cash"] == 80
    assert table.iloc[0]["receivables"] == 50
    assert table.iloc[0]["current_assets"] == 400
    assert table.iloc[0]["fixed_assets"] == 200
    assert table.iloc[0]["total_assets"] == 1000
    assert table.iloc[0]["current_liabilities"] == 300
    assert table.iloc[0]["long_term_debt"] == 30
    assert table.iloc[0]["total_liabilities"] == 500
    assert table.iloc[1]["total_assets"] == 2000


def test_modern_code_header_usecols_subset(tmp_path):
    path = _write_modern_balance(tmp_path)
    probe = pd.read_excel(path, header=None, nrows=3, dtype=str)
    header_cells = [str(v) for v in probe.iloc[0].tolist()]
    usecols = [header_cells.index(name) for name in
               ("Stkcd", "Accper", "Typrep", "A001101000", "A001111000", "A001100000",
                "A001212000", "A001000000", "A002100000", "A002201000", "A002000000")]
    table = read_csmar_table(path, usecols=usecols)
    assert len(table) == 2
    assert table.iloc[0]["total_assets"] == 1000
    assert table.iloc[1]["cash"] == 150
