# -*- coding: utf-8 -*-
"""
test_references_apa.py
Author: Group12A2 DSW Team
Purpose: Guard the single-source APA reference list: count, ordering, in-text
         consistency, and the absence of leftover numeric markers.
Module: tests

Revision History
-----------------
2026-11-26  initial version; APA conversion for manuscript v0.4.
"""
from __future__ import annotations

import re

from src.reporting.references_apa import (
    CITATION_BY_NUMBER,
    REFERENCES_APA,
    format_citation,
    reference_order_check,
)

YEAR = re.compile(r"\((?:19|20)\d{2}[a-z]?\)")


def test_reference_count_is_stable() -> None:
    assert len(REFERENCES_APA) == 24


def test_references_are_unique() -> None:
    assert len(set(REFERENCES_APA)) == len(REFERENCES_APA)


def test_references_are_alphabetical_by_first_author() -> None:
    surnames = reference_order_check()
    assert surnames == sorted(surnames, key=str.lower)


def test_every_entry_has_a_parenthesised_year() -> None:
    missing = [entry for entry in REFERENCES_APA if not YEAR.search(entry)]
    assert missing == []


def test_entry_ends_with_period_or_doi() -> None:
    # APA 7 omits the period after a DOI, and a language tag may close the entry.
    def ok(entry: str) -> bool:
        trimmed = entry.replace("[in Chinese]", "").rstrip()
        return trimmed.endswith(".") or trimmed.split()[-1].startswith("https://doi.org/")

    bad = [entry for entry in REFERENCES_APA if not ok(entry)]
    assert bad == []


def test_entry_starts_with_surname_and_initial() -> None:
    bad = [entry for entry in REFERENCES_APA if not re.match(r"^[A-Z][\w'-]+, [A-Z]\.", entry)]
    assert bad == []


def test_no_legacy_numeric_markers_in_references() -> None:
    bad = [entry for entry in REFERENCES_APA if re.match(r"^\[\d+\]", entry)]
    assert bad == []


def test_citation_map_covers_every_number() -> None:
    assert sorted(CITATION_BY_NUMBER) == list(range(1, 25))


def test_citation_surnames_exist_in_reference_list() -> None:
    joined = " ".join(REFERENCES_APA).lower()
    missing: list[str] = []
    for form in CITATION_BY_NUMBER.values():
        authors = re.split(r",\s*(?:19|20)\d{2}$", form)[0]
        for surname in authors.replace(" et al.", "").split(" & "):
            if surname.strip().lower() not in joined:
                missing.append(surname.strip())
    assert missing == []


def test_format_citation_single() -> None:
    assert format_citation([1]) == "(Healy & Palepu, 2001)"


def test_format_citation_multiple_sorts_alphabetically() -> None:
    # APA orders works inside one parenthetical by first author, so [11, 12]
    # prints Beneish before Repousis even though the numbers run the other way.
    assert format_citation([11, 12]) == "(Beneish, 1999; Repousis, 2016)"


def test_format_citation_range_is_sorted() -> None:
    assert format_citation([4, 5, 6]) == "(Courtis, 1998; Lehavy et al., 2011; Li, 2008)"
