# -*- coding: utf-8 -*-
"""
config.py
Author: Group12A2 DSW Team
Purpose: Global constants for the reproducible research pipeline.
Module: src (core)

Revision History
-----------------
2026-11-05  initial version: seeds, thresholds, paths, feature definitions.
2026-11-11  add BENEISH_TOP_QUANTILE (sample-calibrated top-decile benchmark).
2026-11-11  repoint paths at data/archive_v0.1 and outputs/branches.
"""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# ---- Paths ----
DATA_RAW = PROJECT_ROOT / "data" / "raw"
CSMAR_RAW = DATA_RAW / "csmar"
CNINFO_RAW = DATA_RAW / "cninfo"
DATA_INTERIM = PROJECT_ROOT / "data" / "interim"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
OUTPUTS = PROJECT_ROOT / "outputs"
TABLES = OUTPUTS / "tables"
FIGURES = OUTPUTS / "figures"
REPORTS = OUTPUTS / "reports"

# Raw input already provided by the team.
LISTEDCO_INFO_XLSX = (
    PROJECT_ROOT / "data" / "raw" / "csmar" / "STK_LISTEDCOINFOANL.xlsx"
)

# ---- Sample design (fixed in the proposal, confirmed 2026-11-05) ----
SAMPLE_YEARS = (2021, 2022, 2023)
BASE_YEAR = 2020
FIN_YEARS = (BASE_YEAR,) + SAMPLE_YEARS          # 2020-2023 financial statements
MANUFACTURING_PREFIX = "C"                        # CAPCO IndustryCodeD prefix for manufacturing

# ---- Isolation Forest (fixed in advance, never tuned on outcomes) ----
SEED = 42
IF_N_ESTIMATORS = 500
IF_MAX_SAMPLES = 256                              # whole sample used when smaller
REVIEW_THRESHOLD = 0.10                           # top-10% review priority
REVIEW_THRESHOLD_SENSITIVITY = (0.05, 0.15)

# ---- Preprocessing ----
WINSOR_QUANTILES = (0.01, 0.99)
MIN_SUBINDUSTRY_YEAR_CELL = 20                    # below this, standardise on the full sample

# ---- Beneish M-Score ----
BENEISH_THRESHOLD = -1.78                         # legacy benchmark flag only, never a training input
BENEISH_TOP_QUANTILE = 0.10                       # recalibrated benchmark: top-decile M-Score

# ---- Feature definitions (formulae fixed in docs/feature_dictionary.md) ----
FINANCE_FEATURES = (
    "roa",
    "leverage",
    "revenue_growth",
    "ocf_to_assets",
    "receivables_turnover",
    "accruals_to_assets",
)
TEXT_FEATURES = ("readability", "sentiment_balance", "uncertainty_ratio")
FEATURE_GROUPS = {"finance": FINANCE_FEATURES, "text": TEXT_FEATURES}
ALL_FEATURES = FINANCE_FEATURES + TEXT_FEATURES
