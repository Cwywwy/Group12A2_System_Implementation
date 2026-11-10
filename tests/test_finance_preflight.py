# -*- coding: utf-8 -*-
"""
test_finance_preflight.py
Author: Group12A2 DSW Team
Purpose: Ensure absent CSMAR statements stop the finance stage before a large
         available workbook is parsed.
Module: tests

Revision History
----------------
2026-11-06  initial version.
"""
import sys

import scripts.run_03_build_finance_intermediate as run_03


def test_missing_statement_returns_two_without_reading_workbook(monkeypatch, tmp_path, capsys):
    paths = {
        "balance": tmp_path / "FS_Combas.xlsx",
        "income": tmp_path / "FS_Comins.xlsx",
        "cashflow": tmp_path / "FS_Comscfd.xlsx",
    }
    monkeypatch.setattr(run_03, "TABLE_FILES", paths)
    monkeypatch.setattr(run_03, "_ensure_extracted", lambda path: path.name == "FS_Combas.xlsx")
    monkeypatch.setattr(
        run_03,
        "probe_field_columns",
        lambda _path: (_ for _ in ()).throw(AssertionError("must not parse partial input")),
    )
    monkeypatch.setattr(sys, "argv", ["run_03_build_finance_intermediate.py"])

    assert run_03.main() == 2
    output = capsys.readouterr().out
    assert "FS_Comins.xlsx" in output
    assert "FS_Comscfd.xlsx" in output
    assert "不会读取任何工作簿" in output
