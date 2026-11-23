# -*- coding: utf-8 -*-
"""
manuscript_revision.py
Author: Group12A2 DSW Team
Purpose: Apply a declarative list of manuscript fixes to a set of docx sources
         and report anything that did not land.
Module: src.reporting

A fix is a dict with:
``id``          stable identifier, used in the log and in the missing list
``files``       which document tags the fix applies to ("full", "compact", ...)
``old``/``new`` literal anchor rewrite, optionally ``all_occurrences=True``
``old_prefix``/``new`` whole-paragraph rewrite for sentences whose tail varies
``optional``    a missed anchor is a warning rather than a failure

Revision History
----------------
2026-11-24  initial version: fix engine and number audit split out of the v0.3
            patcher.
"""
from __future__ import annotations

from pathlib import Path

import docx

from src.reporting.docx_patch import replace_paragraph, set_para_text

__all__ = ["apply_fixes"]


def _apply_paragraph_fixes(document, tag: str, fixes, applied: set[str], apply: bool) -> None:
    for paragraph in document.paragraphs:
        text = paragraph.text
        if not text.strip():
            continue
        for fix in fixes:
            if fix["id"] in applied:
                continue
            if text == fix["new"]:
                applied.add(fix["id"])
                continue
            if not text.startswith(fix["old_prefix"]):
                continue
            if apply:
                set_para_text(paragraph, fix["new"])
            applied.add(fix["id"])
            print(f"[{'edit' if apply else 'dry '}] {tag}: {fix['id']} (paragraph)")


def _apply_anchor_fixes(
    document, tag: str, fixes, applied: set[str], apply: bool, problems: int
) -> int:
    for paragraph in document.paragraphs:
        text = paragraph.text
        if not text.strip():
            continue
        changed = text
        hits: list[str] = []
        for fix in fixes:
            already = fix["new"] in changed
            if fix["old"] not in changed:
                if already:
                    applied.add(fix["id"])
                continue
            occurrences = changed.count(fix["old"])
            if occurrences > 1 and not fix.get("all_occurrences"):
                print(f"[skip] {tag} {fix['id']}: anchor occurs {occurrences}x in one paragraph")
                problems += 1
                continue
            changed = changed.replace(fix["old"], fix["new"])
            hits.append(fix["id"])
        if hits:
            if apply:
                set_para_text(paragraph, changed)
            applied.update(hits)
            print(f"[{'edit' if apply else 'dry '}] {tag}: {', '.join(sorted(hits))}")
    return problems


def apply_fixes(fixes: list[dict], documents: dict[str, Path], apply: bool = False) -> int:
    """Apply ``fixes`` to every document tag; return the number of problems."""
    problems = 0
    for tag, path in documents.items():
        if not path.exists():
            print(f"[miss] {tag}: {path} not found")
            problems += 1
            continue
        document = docx.Document(str(path))
        expected = [fix for fix in fixes if tag in fix["files"]]
        paragraph_fixes = [fix for fix in expected if "old_prefix" in fix]
        anchor_fixes = [fix for fix in expected if "old_prefix" not in fix]
        applied: set[str] = set()

        _apply_paragraph_fixes(document, tag, paragraph_fixes, applied, apply)
        problems = _apply_anchor_fixes(document, tag, anchor_fixes, applied, apply, problems)

        missing = [
            fix["id"] for fix in expected if fix["id"] not in applied and not fix.get("optional")
        ]
        if missing:
            print(f"[miss] {tag}: no match for {', '.join(missing)}")
            problems += len(missing)
        if apply:
            document.save(str(path))
            print(f"[save] {path}")
    return problems
