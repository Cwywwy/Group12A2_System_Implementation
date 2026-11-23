# -*- coding: utf-8 -*-
"""
test_event_timing.py
Author: Group12A2 DSW Team
Purpose: Unit tests for the disclosure-date gated t+1 violation labels.
Module: tests

Revision History
----------------
2026-11-24  initial version: strict_forward_labels boundary cases.
"""
import pandas as pd
import pytest

from src.data_ingestion.event_parser import strict_forward_labels


def _audit(rows):
    return pd.DataFrame(rows, columns=["symbol", "fiscal_year", "announce_date"])


def _violations(rows):
    return pd.DataFrame(rows, columns=["symbol", "declare_date", "declare_year", "is_disclosure"])


def _sample(rows):
    return pd.DataFrame(rows, columns=["symbol", "fiscal_year"])


def test_announcement_after_report_is_strict():
    sample = _sample([("000001", 2021)])
    audit = _audit([("000001", 2021, "2022-04-28")])
    violations = _violations([("000001", "2022-06-15", 2022, 1)])

    out = strict_forward_labels(sample, audit, violations, window_days=365)

    row = out.iloc[0]
    assert row["violation_any_t1_strict"] == 1
    assert row["violation_disclosure_t1_strict"] == 1
    assert row["violation_any_t1_loose"] == 1
    assert row["n_announcements"] == 1
    assert row["has_report_date"] == 1


def test_announcement_before_report_is_dropped_by_strict_gate():
    sample = _sample([("000002", 2022)])
    audit = _audit([("000002", 2022, "2023-04-20")])
    violations = _violations([("000002", "2023-02-10", 2023, 1)])

    out = strict_forward_labels(sample, audit, violations, window_days=365)

    row = out.iloc[0]
    assert row["violation_any_t1_strict"] == 0
    assert row["violation_disclosure_t1_strict"] == 0
    assert row["violation_any_t1_loose"] == 1
    assert row["n_announcements_strict"] == 0


def test_same_day_announcement_is_not_prospective():
    sample = _sample([("000003", 2021)])
    audit = _audit([("000003", 2021, "2022-04-28")])
    violations = _violations([("000003", "2022-04-28", 2022, 0)])

    out = strict_forward_labels(sample, audit, violations, window_days=365)

    row = out.iloc[0]
    assert row["violation_any_t1_strict"] == 0
    assert row["violation_any_t1_loose"] == 1


def test_window_bound_applies_and_can_be_removed():
    sample = _sample([("000004", 2021)])
    audit = _audit([("000004", 2021, "2022-01-05")])
    violations = _violations([("000004", "2022-12-30", 2022, 1)])

    bounded = strict_forward_labels(sample, audit, violations, window_days=200)
    generous = strict_forward_labels(sample, audit, violations, window_days=365)

    assert bounded.iloc[0]["violation_any_t1_strict"] == 0
    assert generous.iloc[0]["violation_any_t1_strict"] == 1


def test_announcement_outside_t_plus_one_year_is_not_a_t1_label():
    sample = _sample([("000011", 2021)])
    audit = _audit([("000011", 2023, "2024-04-28")])
    violations = _violations([("000011", "2024-06-30", 2024, 1)])

    out = strict_forward_labels(sample, audit, violations, window_days=365)

    assert out.iloc[0]["violation_any_t1_strict"] == 0
    assert out.iloc[0]["violation_any_t1_loose"] == 0


def test_missing_report_date_keeps_no_strict_label():
    sample = _sample([("000005", 2021)])
    audit = _audit([("000005", 2020, "2021-04-28")])
    violations = _violations([("000005", "2022-05-05", 2022, 1)])

    out = strict_forward_labels(sample, audit, violations, window_days=365)

    row = out.iloc[0]
    assert row["has_report_date"] == 0
    assert row["violation_any_t1_strict"] == 0
    assert row["violation_any_t1_loose"] == 1


def test_no_announcement_means_zero_labels():
    sample = _sample([("000006", 2023)])
    audit = _audit([("000006", 2023, "2024-04-25")])
    violations = _violations([("000006", "2020-05-01", 2020, 1)])

    out = strict_forward_labels(sample, audit, violations, window_days=365)

    row = out.iloc[0]
    assert row["violation_any_t1_strict"] == 0
    assert row["violation_any_t1_loose"] == 0


def test_disclosure_flag_splits_the_two_labels():
    sample = _sample([("000007", 2021)])
    audit = _audit([("000007", 2021, "2022-04-28")])
    violations = _violations(
        [
            ("000007", "2022-05-10", 2022, 0),
            ("000007", "2022-09-10", 2022, 1),
        ]
    )

    out = strict_forward_labels(sample, audit, violations, window_days=365)

    row = out.iloc[0]
    assert row["violation_any_t1_strict"] == 1
    assert row["violation_disclosure_t1_strict"] == 1
    assert row["n_announcements"] == 2


def test_output_is_one_row_per_firm_year():
    sample = _sample([("000008", 2021), ("000008", 2022)])
    audit = _audit([("000008", 2021, "2022-04-28"), ("000008", 2022, "2023-04-28")])
    violations = _violations(
        [
            ("000008", "2022-06-01", 2022, 0),
            ("000008", "2022-07-01", 2022, 1),
            ("000008", "2023-06-01", 2023, 1),
        ]
    )

    out = strict_forward_labels(sample, audit, violations, window_days=365)

    assert len(out) == 2
    assert out[["symbol", "fiscal_year"]].duplicated().sum() == 0
    assert out.loc[out["fiscal_year"] == 2021, "violation_any_t1_strict"].iloc[0] == 1
    assert out.loc[out["fiscal_year"] == 2022, "violation_any_t1_strict"].iloc[0] == 1


def test_row_without_announcement_column_is_tolerated():
    sample = _sample([("000009", 2021)])
    audit = _audit([("000009", 2021, "2022-04-28")])

    out = strict_forward_labels(sample, audit, _violations([]), window_days=365)

    assert out.iloc[0]["violation_any_t1_loose"] == 0
    assert out.iloc[0]["n_announcements"] == 0


@pytest.mark.parametrize("window", [365, None])
def test_labels_are_integers(window):
    sample = _sample([("000010", 2021)])
    audit = _audit([("000010", 2021, "2022-04-28")])
    violations = _violations([("000010", "2022-08-01", 2022, 1)])

    out = strict_forward_labels(sample, audit, violations, window_days=window)

    for column in (
        "violation_any_t1_strict",
        "violation_disclosure_t1_strict",
        "violation_any_t1_loose",
        "violation_disclosure_t1_loose",
        "has_report_date",
    ):
        assert out[column].dtype.kind == "i"
