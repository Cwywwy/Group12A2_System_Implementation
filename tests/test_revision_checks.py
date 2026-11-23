# -*- coding: utf-8 -*-
"""
test_revision_checks.py
Author: Group12A2 DSW Team
Purpose: Tests for the number audit that keeps the manuscript prose in step
         with the Phase 2 tables.
Module: tests
"""
import pandas as pd
import pytest

from src.reporting.revision_checks import check_v03_numbers


def _write_tables(directory, *, strict_n=1543, shift=0.0):
    pd.DataFrame(
        [
            {
                "label": "violation_any_t1_strict",
                "n_loose": 1965,
                "n_strict": strict_n,
                "n_dropped": 1965 - strict_n,
            },
            {
                "label": "violation_disclosure_t1_strict",
                "n_loose": 1337,
                "n_strict": 1040,
                "n_dropped": 297,
            },
        ]
    ).to_csv(directory / "event_strict_diagnostics.csv", index=False)
    pd.DataFrame(
        [
            {
                "label": "violation_disclosure_t1_strict",
                "model": "finance-only IF",
                "auc": 0.6005 + shift,
                "auc_lo": 0.5837,
                "auc_hi": 0.6193,
            },
            {
                "label": "violation_disclosure_t1_strict",
                "model": "fused IF",
                "auc": 0.5904,
                "auc_lo": 0.5736,
                "auc_hi": 0.6107,
            },
            {
                "label": "violation_disclosure_t1_loose",
                "model": "finance-only IF",
                "auc": 0.5955,
                "auc_lo": 0.5797,
                "auc_hi": 0.6114,
            },
        ]
    ).to_csv(directory / "event_ranking_metrics_strict.csv", index=False)
    rows = []
    positives = [0.0016, 0.0115, 0.0077, 0.0065, 0.0038, 0.0071]
    for index, delta in enumerate(positives):
        rows.append(
            {
                "label": "violation_any_t1_strict",
                "model": "logit" if index % 2 == 0 else "hgb",
                "feature_set": "delta_fused_vs_finance",
                "oof_auc": delta,
                "oof_auc_lo": -0.01,
                "oof_auc_hi": 0.01,
            }
        )
    for model, delta in (("logit", -0.0025), ("hgb", -0.0006)):
        rows.append(
            {
                "label": "violation_disclosure_t1_strict",
                "model": model,
                "feature_set": "delta_fused_vs_finance",
                "oof_auc": delta,
                "oof_auc_lo": -0.011,
                "oof_auc_hi": 0.009,
            }
        )
    pd.DataFrame(rows).to_csv(directory / "event_supervised_metrics_strict.csv", index=False)
    pd.DataFrame(
        [
            {"spec": "current_lexicon", "model": "if_fused", "spearman_rho": -0.0176},
            {"spec": "current_lexicon", "model": "if_text", "spearman_rho": -0.0259},
            {"spec": "v0.1_lexicon", "model": "if_fused", "spearman_rho": -0.0211},
            {"spec": "v0.1_lexicon", "model": "if_text", "spearman_rho": -0.0478},
        ]
    ).to_csv(directory / "lexicon_control_v01.csv", index=False)


def test_check_v03_numbers_passes_on_matching_tables(tmp_path):
    _write_tables(tmp_path)
    assert check_v03_numbers(tmp_path) == []


def test_check_v03_numbers_flags_a_changed_label_count(tmp_path):
    _write_tables(tmp_path, strict_n=1500)
    problems = check_v03_numbers(tmp_path)
    assert any("strict n" in problem for problem in problems)


def test_check_v03_numbers_flags_a_changed_auc(tmp_path):
    _write_tables(tmp_path, shift=0.01)
    problems = check_v03_numbers(tmp_path)
    assert any("auc" in problem for problem in problems)


def test_check_v03_numbers_reports_a_missing_table(tmp_path):
    with pytest.raises(FileNotFoundError):
        check_v03_numbers(tmp_path)
