# -*- coding: utf-8 -*-
"""
test_cninfo_client.py
Author: Group12A2 DSW Team
Purpose: Unit tests for the CNINFO client's pure helpers (no network).
Module: tests

Revision History
-----------------
2026-11-05  initial version: title filter and selection logic.
2026-11-06  cover tightened filter markers and BSE legacy search payload.
"""
from src.data_ingestion import cninfo_client
from src.data_ingestion.cninfo_client import (
    Announcement,
    is_annual_report_title,
    search_annual_reports_bse,
    select_annual_report,
)


def test_title_filter_keeps_plain_annual_reports():
    assert is_annual_report_title("2021年年度报告")
    assert is_annual_report_title("2022 年年度报告")


def test_title_filter_drops_summaries_and_foreign_versions():
    assert not is_annual_report_title("2021年年度报告摘要")
    assert not is_annual_report_title("2021年年度报告（英文版）")
    assert not is_annual_report_title("2021年半年度报告")
    assert not is_annual_report_title("2021年年度报告（已取消）")


def test_select_prefers_exact_title_over_revision():
    items = [
        Announcement(code="000001", title="2021年年度报告", time_ms=100, adjunct_url="a.pdf"),
        Announcement(code="000001", title="2021年年度报告（修订版）", time_ms=200, adjunct_url="b.pdf"),
    ]
    chosen = select_annual_report(items, 2021)
    assert chosen is not None and chosen.adjunct_url == "a.pdf"


def test_select_returns_none_for_empty_list():
    assert select_annual_report([], 2021) is None


def test_select_never_falls_back_to_another_year():
    items = [
        Announcement(code="002237", title="2018年年度报告全文", time_ms=900, adjunct_url="old.pdf"),
    ]
    assert select_annual_report(items, 2021) is None


def test_select_accepts_updated_variant_of_same_year():
    items = [
        Announcement(code="002237", title="2021年年度报告（更新后）", time_ms=300, adjunct_url="upd.pdf"),
        Announcement(code="002237", title="2018年年度报告全文", time_ms=900, adjunct_url="old.pdf"),
    ]
    chosen = select_annual_report(items, 2021)
    assert chosen is not None and chosen.adjunct_url == "upd.pdf"


def test_title_filter_keeps_year_only_annual_reports():
    # CNINFO titles sometimes omit the extra 年: 水井坊2021年度报告.
    assert is_annual_report_title("水井坊2021年度报告")
    assert is_annual_report_title("北方稀土2021年度报告全文")
    assert not is_annual_report_title("水井坊2021年度报告摘要")


def test_select_accepts_year_only_tag():
    items = [
        Announcement(code="600779", title="水井坊2021年度报告", time_ms=100, adjunct_url="swellfun.pdf"),
        Announcement(code="600779", title="水井坊2021年度报告摘要", time_ms=90, adjunct_url="summary.pdf"),
    ]
    chosen = select_annual_report(items, 2021)
    assert chosen is not None and chosen.adjunct_url == "swellfun.pdf"


def test_title_filter_drops_notice_like_documents():
    # Observed in production: correction notices and meeting-preview announcements
    # carry "年年度报告" inside their titles but are not annual reports.
    assert not is_annual_report_title("2021年年度报告(更正公告)")
    assert not is_annual_report_title("2021年年度报告业绩说明会预告公告")
    assert not is_annual_report_title("2021年年度报告披露的提示性公告")


def test_title_filter_keeps_reissued_reports():
    assert is_annual_report_title("2021年年度报告（更新后）")
    assert is_annual_report_title("2021年年度报告（更新前）")


def test_title_filter_accepts_cninfo_title_variants():
    # Observed in production on the 2025 acquisition run: four title conventions
    # the year-anchored pattern used to drop, each of which cost a real PDF.
    assert is_annual_report_title("年报全文")
    assert is_annual_report_title("金枫酒业2023年年报全文")
    assert is_annual_report_title("西菱动力2021年度定期报告全文-更新后")
    assert is_annual_report_title("600328_中盐化工_2023年_年度报告")
    assert not is_annual_report_title("600328_中盐化工_2023年_年度报告_摘要")
    assert not is_annual_report_title("康恩贝2024年年度报告摘要")


def test_select_accepts_bare_annual_fulltext():
    items = [
        Announcement(code="600572", title="康恩贝2024年年度报告摘要", time_ms=200, adjunct_url="summary.pdf"),
        Announcement(code="600572", title="年报全文", time_ms=100, adjunct_url="full.pdf"),
    ]
    chosen = select_annual_report(items, 2024)
    assert chosen is not None and chosen.adjunct_url == "full.pdf"


def test_select_accepts_underscore_title_without_summary():
    items = [
        Announcement(code="600199", title="2022年年度报告摘要", time_ms=200, adjunct_url="summary.pdf"),
        Announcement(code="600199", title="600199_金种子酒_2022年_年度报告", time_ms=100, adjunct_url="full.pdf"),
    ]
    chosen = select_annual_report(items, 2022)
    assert chosen is not None and chosen.adjunct_url == "full.pdf"


def test_select_prefers_reissued_over_original_of_same_year():
    items = [
        Announcement(code="300733", title="2021年年度报告", time_ms=100, adjunct_url="original.pdf"),
        Announcement(code="300733", title="2021年度定期报告全文-更新后", time_ms=300, adjunct_url="updated.pdf"),
    ]
    chosen = select_annual_report(items, 2021)
    assert chosen is not None and chosen.adjunct_url == "updated.pdf"


def test_bse_search_payload_uses_empty_category(monkeypatch):
    captured = {}

    def fake_post(url, data):
        captured["url"] = url
        captured["data"] = data
        return {"announcements": []}

    monkeypatch.setattr(cninfo_client, "_post_form", fake_post)
    monkeypatch.setattr(
        cninfo_client,
        "resolve_org_id",
        lambda code: "gfbj0832000",
    )
    items = search_annual_reports_bse("832000", 2021)
    assert items == []
    # The server requires the category key but accepts an empty value;
    # omitting the key entirely yields zero announcements.
    assert captured["data"]["category"] == ""
    assert captured["data"]["stock"] == "832000,gfbj0832000"
    assert captured["data"]["column"] == "bj"
    assert captured["data"]["searchkey"] == "年度报告"


def _capture_payload(monkeypatch, code: str) -> dict:
    captured: dict = {}

    def fake_post(url, data):
        captured.update(data)
        return {"announcements": []}

    monkeypatch.setattr(cninfo_client, "_post_form", fake_post)
    monkeypatch.setattr(cninfo_client, "resolve_org_id", lambda c: "org")
    cninfo_client.search_annual_reports(code, 2024)
    return captured


def test_search_routes_920_codes_to_the_shenzhen_column(monkeypatch):
    # After the 2025 re-coding, 920xxx firms are served from the szse column;
    # the bj column answers with the whole announcement list instead.
    payload = _capture_payload(monkeypatch, "920000")
    assert payload["column"] == "szse"
    assert payload["category"] == "category_ndbg_szsh"
    assert payload["searchkey"] == ""
    assert payload["seDate"] == "2025-01-01~2025-12-31"


def test_search_routes_legacy_bse_codes_to_the_beijing_column(monkeypatch):
    payload = _capture_payload(monkeypatch, "832000")
    assert payload["column"] == "bj"
    assert payload["category"] == ""
    assert payload["searchkey"] == "年度报告"


def test_download_falls_back_to_legacy_bse_search(monkeypatch, tmp_path):
    calls: list[str] = []

    monkeypatch.setattr(cninfo_client, "search_annual_reports", lambda code, year: (_ for _ in ()).throw(AssertionError("primary hit")))
    monkeypatch.setattr(
        cninfo_client,
        "search_annual_reports_bse",
        lambda code, year: [
            Announcement(code=code, title="2024年年度报告", time_ms=1, adjunct_url="x.pdf")
        ],
    )
    monkeypatch.setattr(cninfo_client, "download_pdf", lambda url, dest: calls.append(url) or "downloaded")
    record = cninfo_client.download_annual_report("832000", 2024, dest_dir=tmp_path)
    assert record["status"] == "downloaded"
    assert calls == ["x.pdf"]
