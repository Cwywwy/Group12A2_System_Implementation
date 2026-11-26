#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
test_audit_bundle.py
Author: Group12A2 DSW Team
Purpose: Guard the licence-safe review bundle: rows, keys, label completeness,
         and the fact that every headline statistic can be recomputed from it
         alone, without the licensed raw data.
Module: tests
Revision history:
    2026-11-26 initial version: check audit_bundle.csv reproduces the metrics
"""

from __future__ import annotations

import csv
from pathlib import Path

import pytest
from scipy.stats import spearmanr
from sklearn.metrics import roc_auc_score

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TABLES = PROJECT_ROOT / "outputs" / "tables"
BUNDLE = TABLES / "audit_bundle.csv"

SCORE_COLUMNS = ("if_finance", "if_text", "if_fused", "ae_fused")
LABEL_COLUMNS = (
    "mod_opinion",
    "mod_opinion_wide",
    "violation_any_t1",
    "violation_disclosure_t1",
)
SETTLED_YEARS = (2021, 2022, 2023)

# event_ranking_metrics.csv names the arms the way the manuscript does.
MODEL_LABELS = {
    "if_finance": "finance-only IF",
    "if_text": "text-only IF",
    "if_fused": "fused IF",
    "ae_fused": "fused AE",
    "m_score": "Beneish M-Score",
}


def read(name: Path) -> list[dict[str, str]]:
    # utf-8-sig because the metric tables are written with a BOM, which would
    # otherwise survive as part of the first column name.
    with name.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


@pytest.fixture(scope="module")
def bundle() -> list[dict[str, str]]:
    if not BUNDLE.exists():
        pytest.skip("audit_bundle.csv not exported yet")
    return read(BUNDLE)


def metric(model: str) -> dict[str, str]:
    for row in read(TABLES / "model_metrics.csv"):
        if row["model"] == model:
            return row
    raise AssertionError(f"{model} missing from model_metrics.csv")


def ranking(label: str, column: str) -> dict[str, str]:
    wanted = MODEL_LABELS[column]
    for row in read(TABLES / "event_ranking_metrics.csv"):
        if row["label"] == label and row["model"] == wanted:
            return row
    raise AssertionError(f"{label}/{wanted} missing from event_ranking_metrics.csv")


def test_bundle_shape_and_keys(bundle):
    assert len(bundle) == 16_408
    assert {row["fiscal_year"] for row in bundle} == {"2021", "2022", "2023", "2024", "2025"}
    assert all(len(row["symbol"]) == 6 for row in bundle)
    assert len({(row["symbol"], row["fiscal_year"]) for row in bundle}) == len(bundle)


def test_bundle_carries_no_missing_labels(bundle):
    for column in LABEL_COLUMNS:
        blanks = [row for row in bundle if row[column] in ("", "nan")]
        assert not blanks, f"{column} has {len(blanks)} blanks"


def test_bundle_reproduces_the_spearman_rho(bundle):
    reference = "m_score"
    for column in SCORE_COLUMNS:
        pairs = [
            (float(row[column]), float(row[reference]))
            for row in bundle
            if row[column] not in ("", "nan") and row[reference] not in ("", "nan")
        ]
        xs, ys = zip(*pairs)
        rho = spearmanr(xs, ys).statistic
        assert rho == pytest.approx(float(metric(column)["spearman_rho"]), abs=1e-6)


def test_bundle_reproduces_the_opinion_auc(bundle):
    for column in (*SCORE_COLUMNS, "m_score"):
        rows = [row for row in bundle if row[column] not in ("", "nan")]
        scores = [float(row[column]) for row in rows]
        labels = [int(float(row["mod_opinion"])) for row in rows]
        auc = roc_auc_score(labels, scores)
        expected = ranking("mod_opinion", column)["auc"]
        assert auc == pytest.approx(float(expected), abs=1e-6)


def test_bundle_reproduces_the_settled_violation_auc(bundle):
    rows = [row for row in bundle if int(row["fiscal_year"]) in SETTLED_YEARS]
    assert len(rows) == 9_239
    scores = [float(row["if_finance"]) for row in rows]
    labels = [int(float(row["violation_disclosure_t1"])) for row in rows]
    auc = roc_auc_score(labels, scores)
    expected = ranking("violation_disclosure_t1", "if_finance")["auc"]
    assert auc == pytest.approx(float(expected), abs=1e-6)
