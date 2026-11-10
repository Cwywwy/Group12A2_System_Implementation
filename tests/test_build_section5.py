#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Unit tests for the section-5 builder helpers.

Module role: manuscript assembly regression tests.
Author: Jinyu Wang
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load():
    path = ROOT / "scripts" / "build_section5.py"
    spec = importlib.util.spec_from_file_location("build_section5", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


build_section5 = _load()


def test_fmt_branches():
    fmt = build_section5._fmt
    assert fmt(281_021.9) == "281,022"
    assert fmt(112.18) == "112.18"
    assert fmt(1.5) == "1.500"
    assert fmt(-11.33) == "-11.330"
    assert fmt(0.0093) == "0.0093"
    assert fmt(0.0000001) == "0.00000"
    assert fmt(float("nan")) == "n/a"


def test_p_value_helpers():
    assert build_section5._p_text(0.0001) == "< 0.001"
    assert build_section5._p_text(0.008) == "0.008"
    assert build_section5._p_inline(0.0001) == "p < 0.001"
    assert build_section5._p_inline(0.272) == "p = 0.272"


def test_plain_strips_backticks():
    assert build_section5._plain("`roa` reaches 0.1") == "roa reaches 0.1"


def _fake_numbers() -> dict:
    num = {
        "frame_years": 10_000,
        "descriptives": [("roa", 9_999, 0.09, 0.72, -11.3, 47.9)],
    }
    for model in build_section5.MODEL_LABELS:
        num[f"rho_{model}"] = 0.1
        num[f"p_{model}"] = 0.001
        for k in (5, 10, 15):
            for bench in ("legacy", "calibrated"):
                num[f"ev_{bench}_{model}_{k}"] = 0.5
                num[f"en_{bench}_{model}_{k}"] = 1.2
    return num


def test_table_51_shape_and_header():
    rows = build_section5._table_51(_fake_numbers())
    assert rows[0] == ["Feature", "n", "mean", "std", "min", "max"]
    assert rows[1][0] == "roa"
    assert len(rows) == 2


def test_table_52_covers_all_models():
    rows = build_section5._table_52(_fake_numbers())
    assert len(rows) == 1 + len(build_section5.MODEL_LABELS)
    assert rows[0] == ["Model", "Spearman rho", "p-value"]


def test_table_53_has_dual_benchmark_columns():
    rows = build_section5._table_53(_fake_numbers())
    assert len(rows[0]) == 6
    assert rows[0][-2:] == ["Event rate (recalibrated)", "Enrichment (recalibrated)"]
    assert len(rows) == 1 + 3 * len(build_section5.MODEL_LABELS)


def test_translate_rows_maps_headers_and_models():
    rows = [
        ["Model", "k", "Enrichment (recalibrated)"],
        ["Fused IF", "10%", "1.904"],
    ]
    out = build_section5._translate_rows(rows)
    assert out[0][0] == "模型"
    assert out[0][2] == "富集率（校准）"
    assert out[1][0] == "融合 IF"


def test_prose_has_no_placeholders():
    num = _fake_numbers()
    for key in ("s51", "s52_intro", "p_after_t51", "p_after_t53", "s53", "s54", "s55"):
        num.setdefault("year_share_text", {2021: 0.96, 2022: 0.99, 2023: 0.99})
        num.setdefault("frame_firms", 10)
        num.setdefault("frame_by_year", {2021: 1, 2022: 1, 2023: 1})
        num.setdefault("n", 10)
        num.setdefault("n_firms", 5)
        num.setdefault("by_year", {2021: 1, 2022: 1, 2023: 1})
        num.setdefault("share", 0.8)
        num.setdefault("text_ok", 9)
        num.setdefault("text_suspicious", 1)
        num.setdefault("text_missing", 0)
        num.setdefault("legacy_flag", 5)
        num.setdefault("legacy_share", 0.6)
        num.setdefault("q90", 16.5)
        num.setdefault("cal_flag", 1)
        num.setdefault("overlap_fin_fused", 0.8)
        num.setdefault("overlap_fin_text", 0.1)
        num.setdefault("shap_finance", 0.66)
        num.setdefault("shap_text", 0.34)
        num.setdefault("shap_top3", [("roa", 0.3), ("leverage", 0.2), ("ocf", 0.1)])
        num.setdefault("top1_symbol", "000820")
        num.setdefault("top1_year", 2021)
        num.setdefault("top1_industry", "C42")
        num.setdefault("top1_score", 0.7)
        num.setdefault("top1_mscore", 100.0)
        num.setdefault("top1_drivers", ["roa", "leverage", "ocf"])
    text = build_section5.prose(num)
    cn = build_section5.prose_cn(num)
    for payload in (text, cn):
        for value in payload.values():
            if isinstance(value, str):
                assert "{" not in value, value[:80]
                assert "None" not in value, value[:80]

def _fake_numbers_v02() -> dict:
    num = _fake_numbers()
    num["v01"] = {
        "if_text": {"rho": -0.030, "p": 0.010},
        "if_fused": {"rho": 0.103, "p": 0.001},
        "ae_fused": {"rho": 0.012, "p": 0.272},
        "calibrated_if_text_10": 1.07,
    }
    num["lexicon_density"] = {
        "sentiment_terms": {"v01": 13.4, "v02": 111.3, "ratio": 8.3}
    }
    num.update(
        {
            "year_share_text": {2021: 0.96, 2022: 0.99, 2023: 0.99},
            "frame_firms": 10,
            "frame_by_year": {2021: 1, 2022: 1, 2023: 1},
            "n": 10,
            "n_firms": 5,
            "by_year": {2021: 1, 2022: 1, 2023: 1},
            "share": 0.8,
            "text_ok": 9,
            "text_suspicious": 1,
            "text_missing": 0,
            "legacy_flag": 5,
            "legacy_share": 0.6,
            "q90": 16.5,
            "cal_flag": 1,
            "overlap_fin_fused": 0.8,
            "overlap_fin_text": 0.1,
            "shap_finance": 0.66,
            "shap_text": 0.34,
            "shap_top3": [("roa", 0.3), ("leverage", 0.2), ("ocf", 0.1)],
            "top1_symbol": "000820",
            "top1_year": 2021,
            "top1_industry": "C42",
            "top1_score": 0.7,
            "top1_mscore": 100.0,
            "top1_drivers": ["roa", "leverage", "ocf"],
        }
    )
    return num


def test_table_54_shape_and_dual_specification():
    rows = build_section5._table_54(_fake_numbers_v02())
    assert len(rows) == 10
    assert all(len(row) == 3 for row in rows)
    assert rows[0] == [
        "Design choice",
        "First specification (v0.1)",
        "Second specification (v0.2)",
    ]
    assert "3,585" in rows[1][2]
    assert rows[8][0].startswith("Text-only top-10%")
    assert "1.07" in rows[8][1]


def test_table_54_cn_shape_is_chinese():
    rows = build_section5._table_54_cn(_fake_numbers_v02())
    assert len(rows) == 10
    assert all(len(row) == 3 for row in rows)
    assert rows[0][0] == "设计选择"
    assert rows[1][0] == "情感词典"


def test_prose_includes_section_56():
    text = build_section5.prose(_fake_numbers_v02())
    cn = build_section5.prose_cn(_fake_numbers_v02())
    for payload in (text, cn):
        for key in ("s56_heading", "s56a", "t54_caption", "s56b"):
            assert payload[key], key
        assert "8.3" in payload["s56b"], payload["s56b"][:80]
