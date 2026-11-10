# -*- coding: utf-8 -*-
"""
run_05c_lexicon_density.py
Author: Group12A2 DSW Team
Purpose: Quantify how much denser the v0.2 financial sentiment lexicon is than
         the v0.1 bootstrap lexicon on the same MD&A documents, so the write-up
         can show that the null textual result is not an artefact of a thin
         dictionary.
Module: scripts

Usage: python scripts/run_05c_lexicon_density.py [--year 2021] [--docs 200]

Method
------
The cached MD&A texts from scripts/run_05b_recompute_text_features.py are read
from data/interim/mda_text_<year>.jsonl. Every `step`-th document is tokenised
with the same jieba user dictionary used by the pipeline, and the hits of the
v0.1 (bootstrap) and the v0.2 (Yao et al. 2021) lexicons are counted on the
identical token stream. The output is hits per 1,000 tokens for positive,
negative, combined sentiment and uncertainty terms.

Revision History
----------------
2026-11-11  initial version.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import DATA_INTERIM  # noqa: E402
from src.features.textual import tokenise  # noqa: E402

DICT_DIR = PROJECT_ROOT / "data" / "external" / "dictionaries"
OLD_DIR = DICT_DIR / "v0.1_bootstrap_backup"
OUT_CSV = PROJECT_ROOT / "outputs" / "tables" / "lexicon_density.csv"


def _load(path: Path) -> set[str]:
    words = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            words.add(line)
    return words


def _density(hits: int, tokens: int) -> float:
    return hits / tokens * 1000.0 if tokens else 0.0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, default=2021)
    parser.add_argument("--docs", type=int, default=200)
    args = parser.parse_args()

    source = DATA_INTERIM / f"mda_text_{args.year}.jsonl"
    if not source.exists():
        print(f"[run_05c] missing cached MD&A text: {source}")
        sys.exit(2)

    lexicons = {
        "v01_pos": _load(OLD_DIR / "financial_positive.txt"),
        "v01_neg": _load(OLD_DIR / "financial_negative.txt"),
        "v01_unc": _load(OLD_DIR / "uncertainty.txt"),
        "v02_pos": _load(DICT_DIR / "financial_positive.txt"),
        "v02_neg": _load(DICT_DIR / "financial_negative.txt"),
        "v02_unc": _load(DICT_DIR / "uncertainty.txt"),
    }

    lines: list[str] = []
    with source.open(encoding="utf-8") as handle:
        for line in handle:
            lines.append(line)
    if not lines:
        print(f"[run_05c] no documents in {source}")
        sys.exit(2)

    step = max(1, len(lines) // args.docs)
    sample = lines[::step][: args.docs]

    totals = {key: 0 for key in lexicons}
    n_tokens = 0
    for raw in sample:
        text = json.loads(raw).get("mda_text") or ""
        tokens = tokenise(text)
        n_tokens += len(tokens)
        for key, words in lexicons.items():
            totals[key] += sum(1 for token in tokens if token in words)

    rows = [
        {
            "metric": "positive_terms",
            "v01_per_1000": round(_density(totals["v01_pos"], n_tokens), 2),
            "v02_per_1000": round(_density(totals["v02_pos"], n_tokens), 2),
        },
        {
            "metric": "negative_terms",
            "v01_per_1000": round(_density(totals["v01_neg"], n_tokens), 2),
            "v02_per_1000": round(_density(totals["v02_neg"], n_tokens), 2),
        },
        {
            "metric": "sentiment_terms",
            "v01_per_1000": round(
                _density(totals["v01_pos"] + totals["v01_neg"], n_tokens), 2
            ),
            "v02_per_1000": round(
                _density(totals["v02_pos"] + totals["v02_neg"], n_tokens), 2
            ),
        },
        {
            "metric": "uncertainty_terms",
            "v01_per_1000": round(_density(totals["v01_unc"], n_tokens), 2),
            "v02_per_1000": round(_density(totals["v02_unc"], n_tokens), 2),
        },
    ]
    table = pd.DataFrame(rows)
    table["ratio"] = (table["v02_per_1000"] / table["v01_per_1000"]).round(2)

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
    print(f"[run_05c] documents {len(sample)} of {len(lines)} (year {args.year}), "
          f"tokens {n_tokens:,}")
    print(table.to_string(index=False))
    print(f"[run_05c] written: {OUT_CSV}")


if __name__ == "__main__":
    main()
