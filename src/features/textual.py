# -*- coding: utf-8 -*-
"""
textual.py
Author: Group12A2 DSW Team
Purpose: MD&A extraction from annual report PDFs and the three Chinese text features.
Module: src/features

Revision History
-----------------
2026-11-05  initial version: pypdf extraction, MD&A slicing, jieba tokenisation,
            dictionary loading, readability / sentiment balance / uncertainty ratio.
2026-11-06  robustness: unreadable or malformed PDFs return a pdf_error QC row rather
            than terminating the whole checkpointed batch.
2026-11-05  fix: locate_mda now prefers the LONGEST heading-candidate slice, so the
            body section beats the short table-of-contents entry; cross-reference
            occurrences are ignored when a real heading exists; added alternative
            headings 经营情况讨论与分析 and 管理层分析与讨论.
2026-11-06  fix: locate_mda "strong line" scoring - an occurrence counts as a heading
            only when its line holds just the heading (optional 第X节 prefix) and is
            not a TOC entry (dotted leaders / trailing page number); without any
            strong occurrence fall back to the longest slice.  Fixes false-short
            slices like 000408 (4 tokens) where the body heading sits on its own
            line while the TOC entry starts with 第三节.
2026-11-11  v0.2 dictionary: load the jieba user dictionary so multi-character
            financial terms segment whole, and switch sentiment/uncertainty counting
            from substring hits to token-exact membership (full Yao et al. 2021
            formal lexicon, 5,218 words).
"""
import re
from pathlib import Path

import jieba
from pypdf import PdfReader

from src.config import PROJECT_ROOT

DICT_DIR = PROJECT_ROOT / "data" / "external" / "dictionaries"
FIN_POSITIVE = DICT_DIR / "financial_positive.txt"
FIN_NEGATIVE = DICT_DIR / "financial_negative.txt"
UNCERTAINTY = DICT_DIR / "uncertainty.txt"
JIEBA_USERDICT = DICT_DIR / "jieba_userdict.txt"

MDA_HEADINGS = ("管理层讨论与分析", "经营情况讨论与分析", "管理层分析与讨论")
NEXT_SECTION = re.compile(r"第[四五六七八九十百]+节")
HEADING_LINE = re.compile(r"第[一二三四五六七八九十百]+[章节]")
SENTENCE_SPLIT = re.compile(r"[。！？；]+")
CHINESE_TOKEN = re.compile(r"^[\u4e00-\u9fff]+$")

_userdict_loaded = False


def extract_pdf_text(path: Path) -> str:
    """Extract the text layer of a PDF; scanned pages contribute empty strings."""
    reader = PdfReader(str(path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def locate_mda(text: str) -> str | None:
    """Slice the MD&A section.

    Occurrences are scored as "strong" when the heading occupies its own line:
    the text before the heading on that line is empty or a 第X节/章 prefix, and the
    line is not a table-of-contents entry (dotted leaders / trailing page number).
    The longest strong slice wins; without any strong occurrence the longest slice
    overall is used as a fallback and downstream QC flags tiny slices.
    """
    candidates: list[tuple[bool, str]] = []
    for heading in MDA_HEADINGS:
        pos = 0
        while True:
            start = text.find(heading, pos)
            if start < 0:
                break
            pos = start + 1
            line_start = text.rfind("\n", 0, start) + 1
            line_end = text.find("\n", start)
            if line_end < 0:
                line_end = len(text)
            line = text[line_start:line_end].strip()
            offset = line.find(heading)
            prefix = line[:offset] if offset >= 0 else line
            prefix_ok = bool(
                re.fullmatch(r"(第[一二三四五六七八九十百]+[章节][\s　]*)?", prefix)
            )
            toc_like = "...." in line or bool(re.search(r"\d{1,4}\s*$", line))
            strong = prefix_ok and not toc_like
            tail = text[start + len(heading):]
            match = NEXT_SECTION.search(tail)
            end = start + len(heading) + match.start() if match else len(text)
            candidates.append((strong, text[start:end]))
    if not candidates:
        return None
    strong_pool = [section for strong, section in candidates if strong]
    pool = strong_pool or [section for _, section in candidates]
    return max(pool, key=len)


def _ensure_userdict() -> None:
    """Load the financial lexicon into jieba once per process so multi-character
    terms segment as single tokens."""
    global _userdict_loaded
    if _userdict_loaded:
        return
    if JIEBA_USERDICT.exists():
        jieba.load_userdict(str(JIEBA_USERDICT))
    _userdict_loaded = True


def tokenise(text: str) -> list[str]:
    """jieba word segmentation; keep pure-Chinese tokens only."""
    _ensure_userdict()
    return [token for token in jieba.lcut(text) if CHINESE_TOKEN.match(token)]


def load_dictionary(path: Path) -> set[str]:
    """Load one word-per-line dictionary; blank lines and '#' comments skipped."""
    if not path.exists():
        return set()
    words: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        word = line.strip()
        if word and not word.startswith("#"):
            words.add(word)
    return words


def count_dictionary_tokens(tokens: list[str], words: set[str]) -> int:
    """Count dictionary members among word-segmented tokens (token-exact match).

    Replaces the v0.1 substring count: at the full-lexicon scale (5,218 words) a
    substring scan is both infeasible and over-counts negation prefixes (e.g. 不
    inside 不错) and overlapping terms. Token membership matches the word-frequency
    methodology of the source lexicon (Yao et al., 2021).
    """
    return sum(1 for token in tokens if token in words)


def compute_text_features(
    text: str,
    positive_words: set[str] | None = None,
    negative_words: set[str] | None = None,
    uncertainty_words: set[str] | None = None,
) -> dict:
    """Three text features plus diagnostic counts, per the feature dictionary."""
    positive_words = positive_words if positive_words is not None else load_dictionary(FIN_POSITIVE)
    negative_words = negative_words if negative_words is not None else load_dictionary(FIN_NEGATIVE)
    uncertainty_words = uncertainty_words if uncertainty_words is not None else load_dictionary(UNCERTAINTY)

    tokens = tokenise(text)
    total = len(tokens)
    pos_hits = count_dictionary_tokens(tokens, positive_words)
    neg_hits = count_dictionary_tokens(tokens, negative_words)
    unc_hits = count_dictionary_tokens(tokens, uncertainty_words)

    sentences = [s for s in SENTENCE_SPLIT.split(text) if s.strip()]
    mean_chars = sum(len(s) for s in sentences) / len(sentences) if sentences else 0.0
    readability = 1.0 / mean_chars if mean_chars > 0 else 0.0

    return {
        "readability": readability,
        "sentiment_balance": (pos_hits - neg_hits) / total if total else 0.0,
        "uncertainty_ratio": unc_hits / total if total else 0.0,
        "n_tokens": total,
        "n_sentences": len(sentences),
    }


def extract_mda_features(path: Path, include_text: bool = False) -> dict:
    """Full flow for one PDF; unreadable PDFs become QC rows, not batch failures.

    include_text=True additionally returns the raw MD&A slice under "mda_text"
    so callers can cache the text layer without re-extracting the PDF later.
    """
    try:
        text = extract_pdf_text(path)
    except Exception as exc:  # pypdf errors vary by malformed document structure
        return {
            "path": str(path),
            "status": "pdf_error",
            "features": None,
            "error_type": type(exc).__name__,
        }
    mda = locate_mda(text)
    if mda is None:
        return {"path": str(path), "status": "no_mda", "features": None}
    features = compute_text_features(mda)
    result = {"path": str(path), "status": "ok", "features": features}
    if include_text:
        result["mda_text"] = mda
    return result
