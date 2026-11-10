# -*- coding: utf-8 -*-
"""
test_textual.py
Author: Group12A2 DSW Team
Purpose: Unit tests for MD&A slicing and the three Chinese text features.
Module: tests

Revision History
-----------------
2026-11-05  initial version.
"""
import pytest

from src.config import PROJECT_ROOT
from src.features.textual import (
    compute_text_features,
    count_dictionary_tokens,
    extract_mda_features,
    extract_pdf_text,
    locate_mda,
    tokenise,
)

REAL_PDF = PROJECT_ROOT / "data" / "raw" / "cninfo" / "2021" / "000001_2021_annual_report.pdf"


def test_locate_mda_slices_between_sections():
    text = "第一节 公司简介\n正文。\n第三节 管理层讨论与分析\n经营情况良好。\n第四节 公司治理\n治理内容。"
    mda = locate_mda(text)
    assert mda is not None
    assert "经营情况良好" in mda
    assert "治理内容" not in mda


def test_locate_mda_prefers_body_over_toc():
    body = "第三节 管理层讨论与分析\n" + "公司经营稳健。" * 200 + "\n第四节 公司治理\n治理内容。"
    toc = "目录\n第三节 管理层讨论与分析 ·········· 12\n第四节 公司治理 ·········· 30\n"
    text = toc + "第一节 公司简介\n简介内容。\n" + body
    mda = locate_mda(text)
    assert mda is not None
    assert len(mda) > 500
    assert "公司经营稳健" in mda
    assert "治理内容" not in mda


def test_locate_mda_standalone_body_heading_beats_section_prefixed_toc():
    # 000408 pattern: the TOC entry starts with 第三节, the body heading sits on
    # its own line; the old scoring picked the 56-char TOC slice.
    body = "管理层讨论与分析\n" + "经营情况稳健。" * 300 + "\n第四节 公司治理\n治理内容。"
    toc = "目录\n第三节 管理层讨论与分析 ....... 12\n第四节 公司治理 ....... 30\n"
    text = toc + "第一节 公司简介\n简介内容。\n" + body
    mda = locate_mda(text)
    assert mda is not None
    assert len(mda) > 500
    assert "经营情况稳健" in mda
    assert "治理内容" not in mda


def test_locate_mda_ignores_cross_reference_when_heading_exists():
    body = "第三节 管理层讨论与分析\n公司经营稳健。\n第四节 公司治理\n治理内容。"
    cross_ref = "参见管理层讨论与分析部分的详细说明。"
    mda = locate_mda(body + "\n附注\n" + cross_ref)
    assert mda is not None
    assert "公司经营稳健" in mda
    assert "详细说明" not in mda


def test_locate_mda_alternative_heading():
    text = "第一节 公司简介\n正文。\n第三节 经营情况讨论与分析\n经营情况良好。\n第四节 公司治理\n治理内容。"
    mda = locate_mda(text)
    assert mda is not None
    assert "经营情况良好" in mda
    assert "治理内容" not in mda


def test_locate_mda_returns_none_when_heading_missing():
    assert locate_mda("第一节 公司简介\n第二节 主要财务指标") is None


def test_tokenise_keeps_chinese_only():
    tokens = tokenise("公司 revenue 2021 业绩")
    assert tokens == ["公司", "业绩"]


def test_count_dictionary_tokens_exact_match():
    assert count_dictionary_tokens(["增长", "增长", "亏损"], {"增长", "亏损"}) == 3
    # token membership avoids the v0.1 substring false hit (不 inside 不错)
    assert count_dictionary_tokens(["不错", "不确定"], {"不"}) == 0


def test_text_features_known_counts():
    text = "公司业绩增长，增长。亏损。不明朗，不明朗，取决于。"
    pos, neg, unc = {"增长"}, {"亏损"}, {"不明朗", "取决于"}
    features = compute_text_features(text, pos, neg, unc)
    tokens = tokenise(text)
    total = len(tokens)
    pos_hits = count_dictionary_tokens(tokens, pos)
    neg_hits = count_dictionary_tokens(tokens, neg)
    unc_hits = count_dictionary_tokens(tokens, unc)
    assert features["n_tokens"] == total
    assert features["sentiment_balance"] == pytest.approx((pos_hits - neg_hits) / total)
    assert features["uncertainty_ratio"] == pytest.approx(unc_hits / total)
    assert 0.0 < features["readability"] <= 1.0
    # sanity: the planted words are actually detected as present
    assert pos_hits >= 1 and neg_hits >= 1 and unc_hits >= 2


def test_text_features_empty_text():
    features = compute_text_features("", {"增长"}, {"亏损"}, {"不明朗"})
    assert features["n_tokens"] == 0
    assert features["sentiment_balance"] == 0.0


def test_extract_mda_features_marks_unreadable_pdf_instead_of_raising(monkeypatch, tmp_path):
    def raise_pdf_error(_path):
        raise ValueError("bad xref")

    monkeypatch.setattr("src.features.textual.extract_pdf_text", raise_pdf_error)
    result = extract_mda_features(tmp_path / "broken.pdf")
    assert result["status"] == "pdf_error"
    assert result["features"] is None
    assert result["error_type"] == "ValueError"


def test_real_pdf_extracts_mda_when_text_layer_exists():
    if not REAL_PDF.exists():
        pytest.skip("real PDF not downloaded yet")
    text = extract_pdf_text(REAL_PDF)
    if len(text) < 1000:
        pytest.skip("PDF appears to be a scan without a usable text layer")
    mda = locate_mda(text)
    assert mda is not None and len(mda) > 1000
