# -*- coding: utf-8 -*-
"""
test_event_label_window.py
Author: Group12A2 DSW Team
Purpose: Check that forward violation labels are scored only on fiscal years
         whose t+1 calendar window is fully covered by the CSMAR snapshot.
Module: tests

Revision History
----------------
2026-11-26  initial version: complete_t1_years and _label_frame guard.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import VIOLATION_SNAPSHOT  # noqa: E402


def _load_script():
    path = PROJECT_ROOT / "scripts" / "run_07b_event_models.py"
    spec = importlib.util.spec_from_file_location("run_07b_event_models", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def module():
    return _load_script()


def test_snapshot_is_a_date_tuple():
    assert len(VIOLATION_SNAPSHOT) == 3
    assert all(isinstance(part, int) for part in VIOLATION_SNAPSHOT)


def test_complete_t1_years_drops_the_open_year(module):
    years = [2021, 2022, 2023, 2024, 2025]
    keep = module.complete_t1_years(years)
    assert keep == [2021, 2022, 2023]


def test_complete_t1_years_accepts_a_series(module):
    keep = module.complete_t1_years(pd.Series([2022, 2023]))
    assert keep == [2022, 2023]


def test_label_frame_leaves_opinion_labels_alone(module):
    frame = pd.DataFrame({"fiscal_year": [2021, 2024, 2025], "mod_opinion": [0, 1, 0]})
    kept = module._label_frame(frame, "mod_opinion")
    assert len(kept) == 3


def test_label_frame_restricts_violation_labels(module):
    frame = pd.DataFrame(
        {
            "fiscal_year": [2021, 2022, 2023, 2024, 2025],
            "violation_any_t1": [0, 1, 0, 1, 0],
        }
    )
    kept = module._label_frame(frame, "violation_any_t1")
    assert list(kept["fiscal_year"]) == [2021, 2022, 2023]
    assert len(module._label_frame(frame, "violation_disclosure_t1")) == 3
