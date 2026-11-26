# -*- coding: utf-8 -*-
"""
cninfo_client.py
Author: Group12A2 DSW Team
Purpose: CNINFO public announcement API client (annual report search + PDF download).
Module: src/data_ingestion

Uses the same HTTP endpoints as CNINFO's own announcement search page, so no
registration or access token is required. The official webapi.cninfo.com.cn open
platform requires a developer account and a token and can be added as an adapter
later without touching this module's callers.

Revision History
-----------------
2026-11-05  initial version: topSearch org id, hisAnnouncement query, PDF download.
2026-11-06  tighten title filter; add BSE legacy-code search helper.
2026-11-06  accept 'YYYY年度报告' title style (no second 年), e.g. 水井坊2021年度报告.
"""
import re
import time
from dataclasses import dataclass
from pathlib import Path

import requests

from src.config import CNINFO_RAW

TOP_SEARCH_URL = "http://www.cninfo.com.cn/new/information/topSearch/query"
ANNOUNCEMENT_URL = "http://www.cninfo.com.cn/new/hisAnnouncement/query"
PDF_BASE_URL = "https://static.cninfo.com.cn/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    ),
    "Referer": "http://www.cninfo.com.cn/new/index",
}

REQUEST_PAUSE_SECONDS = 0.5
MAX_RETRIES = 3
REQUEST_TIMEOUT = 30


@dataclass
class Announcement:
    code: str
    title: str
    time_ms: int
    adjunct_url: str


_ANNUAL_MARKERS = ("年度报告", "年度定期报告", "年报")
_TITLE_NOISE = re.compile(r"[\s_]")
_YEAR_TOKEN = re.compile(r"(20\d{2})")
_NON_ANNUAL_MARKERS = (
    "半年度", "季度", "问询", "回复", "意见", "摘要", "英文",
)


def _has_annual_report_tag(title: str, fiscal_year: int) -> bool:
    """True when the title can be the annual report of fiscal_year.

    Titles are normalised (spaces and underscores removed) because CNINFO mixes
    conventions: '2021年年度报告', '水井坊2021年度报告全文',
    '600328_中盐化工_2023年_年度报告', '金枫酒业2023年年报全文', and even a
    bare '年报全文' whose year is implied by the request window.

    A title that names a *different* year never qualifies, which keeps a stale
    document (e.g. a 2018 report surfacing in a 2021 query) out of the sample.
    A title with no year at all is accepted because the query is already scoped
    to the publication window of fiscal_year; interim and quarterly filings are
    rejected by marker whatever their year.
    """
    t = _TITLE_NOISE.sub("", title)
    if any(marker in t for marker in _NON_ANNUAL_MARKERS):
        return False
    years = {int(year) for year in _YEAR_TOKEN.findall(t)}
    if years and fiscal_year not in years:
        return False
    return any(marker in t for marker in _ANNUAL_MARKERS)


def is_annual_report_title(title: str) -> bool:
    """Keep full annual reports; drop summaries, English versions, and revisions."""
    normalised = _TITLE_NOISE.sub("", title)
    if not any(marker in normalised for marker in _ANNUAL_MARKERS):
        return False
    if any(marker in normalised for marker in _NON_ANNUAL_MARKERS):
        return False
    for marker in (
        "摘要", "英文", "已取消", "取消", "修订", "更正",
        "说明会", "预告", "提示性", "披露的",
    ):
        if marker in normalised:
            return False
    return True


def _post_form(url: str, data: dict) -> dict | list:
    """POST form-encoded data with retry and backoff; return parsed JSON."""
    last_error: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.post(url, data=data, headers=HEADERS, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            return resp.json()
        except (requests.RequestException, ValueError) as exc:
            last_error = exc
            time.sleep(2 * attempt)
    raise RuntimeError(f"request failed after {MAX_RETRIES} attempts: {last_error}") from last_error


def resolve_org_id(code: str) -> str:
    """Map a stock code to CNINFO's internal org id (e.g. 000001 -> gssz0000001)."""
    results = _post_form(TOP_SEARCH_URL, {"keyWord": code, "maxNum": 10}) or []
    for item in results:
        if item.get("code") == code and item.get("orgId"):
            return item["orgId"]
    raise LookupError(f"no org id found for stock code {code}")


def search_annual_reports(code: str, fiscal_year: int) -> list[Announcement]:
    """Query the annual reports of one firm for one fiscal year.

    Routing follows the code family, not the exchange name.  Firms that moved to
    the Beijing Stock Exchange before the 2025 re-coding still sit under 920xxx,
    and CNINFO serves those filings from the Shenzhen column with the ordinary
    annual-report category -- asking the Beijing column returns the full
    announcement list (100+ rows) instead, so the report is usually off page 1.
    Legacy 4xxxxx/8xxxxx codes keep the Beijing column with an unfiltered
    category plus a keyword search, which fits their result set on one page.
    """
    org_id = resolve_org_id(code)
    if code.startswith("9"):
        column, category, searchkey = "szse", "category_ndbg_szsh", ""
    elif code.startswith(("4", "8")):
        column, category, searchkey = "bj", "", "年度报告"
    else:
        column, category, searchkey = "szse", "category_ndbg_szsh", ""
    payload = {
        "pageNum": 1,
        "pageSize": 30,
        "column": column,
        "tabName": "fulltext",
        "plate": "",
        "stock": f"{code},{org_id}",
        "searchkey": searchkey,
        "secid": "",
        "category": category,
        "trade": "",
        "seDate": f"{fiscal_year + 1}-01-01~{fiscal_year + 1}-12-31",
        "sortName": "",
        "sortType": "",
        "isHLtitle": "true",
    }
    data = _post_form(ANNOUNCEMENT_URL, payload) or {}
    items = []
    for ann in data.get("announcements") or []:
        title = ann.get("announcementTitle", "").replace("<em>", "").replace("</em>", "")
        if not is_annual_report_title(title):
            continue
        items.append(
            Announcement(
                code=code,
                title=title,
                time_ms=int(ann.get("announcementTime") or 0),
                adjunct_url=ann.get("adjunctUrl", ""),
            )
        )
    time.sleep(REQUEST_PAUSE_SECONDS)
    return items


def search_annual_reports_bse(code: str, fiscal_year: int) -> list[Announcement]:
    """Query annual reports for a BSE legacy (pre-2025) stock code.

    BSE firms switched from 83xxxx/87xxxx/43xxxx codes to 920xxx on 2025-10-09.
    CNINFO only indexes their older filings under the legacy code, and the
    category_ndbg_bj category returns zero hits for those filings.  The report
    is reachable through the unfiltered column='bj' announcement list, but the
    server caps every page at 30 rows and the report can sit beyond page 1, so
    this helper sends an empty category value and a targeted "年度报告" keyword
    search whose result set fits on a single page.
    """
    org_id = resolve_org_id(code)
    payload = {
        "pageNum": 1,
        "pageSize": 30,
        "column": "bj",
        "tabName": "fulltext",
        "plate": "",
        "stock": f"{code},{org_id}",
        "searchkey": "年度报告",
        "secid": "",
        "category": "",
        "trade": "",
        "seDate": f"{fiscal_year + 1}-01-01~{fiscal_year + 1}-12-31",
        "sortName": "",
        "sortType": "",
        "isHLtitle": "true",
    }
    data = _post_form(ANNOUNCEMENT_URL, payload) or {}
    items = []
    for ann in data.get("announcements") or []:
        title = ann.get("announcementTitle", "")
        title = title.replace("<em>", "").replace("</em>", "")
        if not is_annual_report_title(title):
            continue
        items.append(
            Announcement(
                code=code,
                title=title,
                time_ms=int(ann.get("announcementTime") or 0),
                adjunct_url=ann.get("adjunctUrl", ""),
            )
        )
    time.sleep(REQUEST_PAUSE_SECONDS)
    return items


def select_annual_report(items: list[Announcement], fiscal_year: int) -> Announcement | None:
    """Pick the report for fiscal_year; never fall back to another year's report.

    Titles are matched with _has_annual_report_tag, so variants such as 全文/
    （更新后）/（更新前）and both tag styles ('{year}年年度报告' and
    '{year}年度报告') count as the same year.  Among same-year candidates an
    exact title wins, otherwise the latest publication is used.  If no same-year
    candidate exists the function returns None and the caller records 'missing'
    instead of downloading a wrong-year PDF (wrong-year files corrupt the text
    features and were observed in production: e.g. 002237-2021 grabbed a 2018
    report).
    """
    same_year = [a for a in items if _has_annual_report_tag(a.title, fiscal_year)]
    if not same_year:
        return None
    exact_tags = {f"{fiscal_year}年年度报告", f"{fiscal_year}年度报告"}

    def rank(item: Announcement) -> tuple[bool, bool, int]:
        title = _TITLE_NOISE.sub("", item.title)
        return ("更新后" in title, title in exact_tags, item.time_ms)

    return max(same_year, key=rank)


def download_pdf(adjunct_url: str, dest: Path, chunk_size: int = 1 << 20) -> str:
    """Download one PDF to dest via a .part temp file (atomic rename on success)."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        return "cached"
    part = dest.with_name(dest.name + ".part")
    url = PDF_BASE_URL + adjunct_url.lstrip("/")
    last_error: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with requests.get(url, headers=HEADERS, timeout=300, stream=True) as resp:
                resp.raise_for_status()
                with part.open("wb") as handle:
                    for chunk in resp.iter_content(chunk_size=chunk_size):
                        handle.write(chunk)
            part.replace(dest)
            return "downloaded"
        except requests.RequestException as exc:
            last_error = exc
            time.sleep(2 * attempt)
    raise RuntimeError(f"download failed after {MAX_RETRIES} attempts: {last_error}") from last_error


def download_annual_report(code: str, fiscal_year: int, dest_dir: Path | None = None) -> dict:
    """Full flow for one firm-year; returns a status record for the run log.

    A failing primary query is treated as an empty result rather than an error,
    so that the Beijing Stock Exchange fallback still runs: the two endpoints
    fail independently, and losing one firm-year to a transient timeout is worse
    than one extra request.
    """
    dest_dir = dest_dir or CNINFO_RAW / str(fiscal_year)
    dest = dest_dir / f"{code}_{fiscal_year}_annual_report.pdf"
    record = {"code": code, "year": fiscal_year, "status": "ok", "title": "", "path": str(dest)}
    try:
        try:
            items = search_annual_reports(code, fiscal_year)
        except Exception:  # noqa: BLE001 - the fallback below may still succeed
            items = []
        ann = select_annual_report(items, fiscal_year)
        if ann is None and code.startswith(("4", "8", "9")):
            ann = select_annual_report(search_annual_reports_bse(code, fiscal_year), fiscal_year)
        if ann is None:
            record.update(status="missing", title="no annual report found")
            return record
        status = download_pdf(ann.adjunct_url, dest)
        record.update(status=status, title=ann.title)
    except Exception as exc:  # noqa: BLE001 - record and continue the batch
        record.update(status="error", title=str(exc))
    return record
