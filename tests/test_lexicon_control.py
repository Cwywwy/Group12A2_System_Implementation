# -*- coding: utf-8 -*-
"""
test_lexicon_control.py
Author: Group12A2 DSW Team
Purpose: Tests for the same-row lexicon control (archive loader, control frame,
         variant scoring and control table).
Module: tests
"""
import numpy as np
import pandas as pd
import pytest

from src.config import ALL_FEATURES, FINANCE_FEATURES, TEXT_FEATURES
from src.evaluation.lexicon_control import (
    K_VALUES,
    control_table,
    corpus_diagnostics,
    load_archive_text_features,
    prepare_control_frame,
    score_variant,
    variant_overlap,
)


def _synthetic(n=120, seed=7):
    rng = np.random.default_rng(seed)
    frame = pd.DataFrame(
        {
            "symbol": [f"{i:06d}" for i in range(n)],
            "fiscal_year": np.tile([2021, 2022, 2023], n // 3 + 1)[:n],
            "industry_code_d": np.tile(["C39", "C26", "C27"], n // 3 + 1)[:n],
            "m_score": rng.normal(size=n),
        }
    )
    for column in FINANCE_FEATURES:
        frame[column] = rng.normal(size=n)
    frame["readability"] = rng.normal(size=n)
    frame["sentiment_balance"] = rng.normal(size=n)
    frame["uncertainty_ratio"] = rng.normal(size=n)
    frame["n_tokens"] = rng.integers(500, 5000, size=n)
    return frame


def _archive_from(frame: pd.DataFrame, seed=11) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    archive = frame[["symbol", "fiscal_year"]].copy()
    archive["readability"] = frame["readability"].to_numpy()
    archive["sentiment_balance"] = frame["sentiment_balance"].to_numpy() + rng.normal(
        scale=0.1, size=len(frame)
    )
    archive["uncertainty_ratio"] = frame["uncertainty_ratio"].to_numpy()
    archive["n_tokens"] = frame["n_tokens"].to_numpy()
    return archive


def _prefixed(archive: pd.DataFrame) -> pd.DataFrame:
    """Rename the archive columns the way the loader does."""
    return archive.rename(columns={c: f"v01_{c}" for c in TEXT_FEATURES + ("n_tokens",)})


def test_load_archive_text_features_reads_the_year_from_the_file_name(tmp_path):
    frame = _synthetic()
    for year in (2021, 2022, 2023):
        block = frame[frame["fiscal_year"] == year]
        archive = _archive_from(block)
        archive = archive.drop(columns="fiscal_year")
        archive.to_csv(tmp_path / f"text_features_{year}.csv", index=False)

    loaded = load_archive_text_features(tmp_path)

    assert set(loaded["fiscal_year"]) == {2021, 2022, 2023}
    assert {"v01_readability", "v01_sentiment_balance", "v01_uncertainty_ratio", "v01_n_tokens"} <= set(
        loaded.columns
    )
    assert len(loaded) == len(frame)


def test_load_archive_text_features_rejects_an_empty_directory(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_archive_text_features(tmp_path)


def test_prepare_control_frame_keeps_only_shared_complete_rows():
    frame = _synthetic()
    archive = _prefixed(_archive_from(frame))
    archive = archive.iloc[:-5]

    work = prepare_control_frame(frame, archive)

    assert len(work) == len(frame) - 5
    assert set(ALL_FEATURES) <= set(work.columns)
    assert "v01_readability" in work.columns


def test_score_variant_returns_three_matrices_and_a_fused_score():
    frame = _synthetic()
    work = prepare_control_frame(frame, _prefixed(_archive_from(frame)))

    current = score_variant(work, tuple(TEXT_FEATURES))

    assert set(current) >= {"if_finance", "if_text", "if_fused", "fused_scores"}
    assert len(current["if_fused"]["scores"]) == len(work)
    for name in ("if_finance", "if_text", "if_fused"):
        assert np.isfinite(current[name]["scores"]).all()
    assert np.isfinite(current["fused_scores"]).all() or np.isnan(
        current["fused_scores"]
    ).sum() == 0


def test_corpus_diagnostics_reports_agreement():
    frame = _synthetic()
    work = prepare_control_frame(frame, _prefixed(_archive_from(frame)))
    work["v01_readability"] = work["readability"]
    work["v01_n_tokens"] = work["n_tokens"]

    diagnostics = corpus_diagnostics(work)

    assert diagnostics.iloc[0]["n_rows"] == len(work)
    assert diagnostics.iloc[0]["corr_readability"] == pytest.approx(1.0)
    assert diagnostics.iloc[0]["share_identical_token_count"] == pytest.approx(1.0)


def test_control_table_and_overlap_cover_both_specifications():
    frame = _synthetic()
    work = prepare_control_frame(frame, _prefixed(_archive_from(frame)))
    current = score_variant(work, tuple(TEXT_FEATURES))
    legacy = score_variant(work, tuple(f"v01_{column}" for column in TEXT_FEATURES))

    control = control_table(current, legacy, work)
    overlap = variant_overlap(current, legacy)

    assert set(control["spec"]) == {"current_lexicon", "v0.1_lexicon"}
    assert set(control["model"]) == {"if_finance", "if_text", "if_fused"}
    for k in K_VALUES:
        assert f"enrichment_calibrated_k{int(round(k * 100))}" in control.columns
    assert set(overlap["pair"]) == {"fused_current_vs_v01", "text_current_vs_v01"}
    assert overlap["top10_overlap"].between(0, 1).all()
