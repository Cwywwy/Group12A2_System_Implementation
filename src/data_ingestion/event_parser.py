# -*- coding: utf-8 -*-
"""
event_parser.py
Author: Group12A2 DSW Team
Purpose: Parse the CSMAR audit-opinion (FIN_Audit) and violation
         (STK_Violation_Main) exports into firm-year event labels, so the
         screening scores can be evaluated against real regulatory outcomes
         instead of the Beneish M-Score proxy.
Module: src/data_ingestion

Layout notes
------------
Modern CSMAR Excel exports carry three header-ish rows above the data:
row 1 = English item codes (read as the DataFrame header), row 2 = Chinese
labels, row 3 = units ("没有单位" / "元"). The parser therefore drops the
first two data rows and keeps only rows with a parsable six-digit code.

Event definitions
-----------------
- mod_opinion (narrow): the auditor did NOT issue a clean opinion, i.e. the
  opinion is qualified, qualified with an emphasis-of-matter paragraph,
  a disclaimer, or adverse. These are the cases regulators care about.
- mod_opinion_wide: the narrow definition plus "带有解释性说明的无保留意见"
  (unqualified with an explanatory paragraph), which is the softer CSMAR
  category often used in robustness checks.
- violation_any_t1 / violation_disclosure_t1: the firm had a CSMAR violation
  announcement in fiscal year t+1 (the year in which the annual report of
  year t is published), either any violation or a disclosure-related one
  (misstatement, delayed disclosure, material omission, fictitious profit or
  assets). t+1 alignment keeps the label strictly forward-looking relative
  to the report content that the screening model sees.

Revision History
----------------
2026-11-11  initial version: audit-opinion and violation parsers, narrow and
            wide opinion definitions, t+1 violation flags.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.config import PROJECT_ROOT

CSMAR_EVENT_DIR = PROJECT_ROOT / "data" / "raw" / "csmar_events"
AUDIT_FILE = CSMAR_EVENT_DIR / "FIN_Audit.xlsx"
VIOLATION_FILE = CSMAR_EVENT_DIR / "STK_Violation_Main.xlsx"

# Rows 2 and 3 of the export are the Chinese label row and the unit row.
LABEL_ROW_MARKERS = ("证券代码", "没有单位", "None")
SKIP_ROWS = 2

# Opinion category keywords (CSMAR Chinese labels). Order matters: the
# specific cases are matched before the generic "保留" branch.
OPINION_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("adverse", ("否定意见",)),
    ("disclaimer", ("无法表示意见", "无法出具意见")),
    ("qualified_emphasis", ("保留意见加事项段", "保留意见加带事项段")),
    ("emphasis", ("解释性说明", "强调事项", "带强调事项段")),
    # "标准无保留意见" contains the substring "保留意见", so the clean
    # opinion must be matched before the qualified catch-all below.
    ("standard", ("标准无保留意见", "标准意见", "无保留意见")),
    ("qualified", ("保留意见", "保留")),
]

MODERATE_CLASSES = {"qualified", "qualified_emphasis", "disclaimer", "adverse"}
LENIENT_CLASSES = MODERATE_CLASSES | {"emphasis"}

# Violation categories that matter for disclosure risk.
DISCLOSURE_KEYWORDS = (
    "推迟披露", "虚假记载", "误导性陈述", "重大遗漏", "虚构利润",
    "虚列资产", "披露不实", "擅自改变", "财务造假", "会计处理不当",
)
DISCLOSURE_CODES = {"P2501", "P2502", "P2503", "P2504", "P2505", "P2506"}
CODE_SEPARATORS = (";", "；", "、", ",")

BIG4_KEYWORDS = (
    "普华永道", "德勤", "毕马威", "安永",
    "PwC", "Pricewaterhouse", "Deloitte", "KPMG", "Ernst",
)


def _read_export(path: Path | str) -> pd.DataFrame:
    """Read a CSMAR Excel export and drop the label/unit rows."""
    frame = pd.read_excel(path, dtype=str, sheet_name=0)
    frame = frame.iloc[SKIP_ROWS:].copy()
    frame.columns = [str(col).strip() for col in frame.columns]
    return frame


def _clean_code(series: pd.Series) -> pd.Series:
    """Normalise A-share codes to six digits with leading zeros."""
    cleaned = series.astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
    cleaned = cleaned.str.replace(r"\s+", "", regex=True)
    return cleaned.str.zfill(6)


def _drop_non_data(frame: pd.DataFrame, code_col: str) -> pd.DataFrame:
    """Drop label rows and rows with an unusable security code."""
    out = frame.copy()
    out[code_col] = out[code_col].astype(str).str.strip()
    keep = out[code_col].str.fullmatch(r"\d{1,6}(\.0)?")
    out = out.loc[keep.fillna(False)]
    out[code_col] = _clean_code(out[code_col])
    return out


def classify_opinion(text: object) -> str:
    """Map a CSMAR opinion label to a normalised opinion class."""
    if not isinstance(text, str):
        return "unknown"
    value = text.strip()
    if not value or value in LABEL_ROW_MARKERS:
        return "unknown"
    for label, keywords in OPINION_RULES:
        if any(keyword in value for keyword in keywords):
            return label
    return "unknown"


def _is_big4(auditor: object) -> int:
    if not isinstance(auditor, str):
        return 0
    return int(any(keyword.lower() in auditor.lower() for keyword in BIG4_KEYWORDS))


def _to_float(series: pd.Series) -> pd.Series:
    return pd.to_numeric(
        series.astype(str).str.replace(",", "", regex=False).str.strip(),
        errors="coerce",
    )


def _ensure_columns(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Add any missing (optional) columns as NaN so the schema is stable."""
    out = frame.copy()
    for column in columns:
        if column not in out.columns:
            out[column] = pd.NA
    return out


def parse_audit_opinions(path: Path | str = AUDIT_FILE) -> pd.DataFrame:
    """Parse FIN_Audit.xlsx into one row per firm-fiscal-year opinion."""
    frame = _read_export(path)
    frame = _drop_non_data(frame, "Stkcd")
    frame = frame.rename(
        columns={
            "Stkcd": "symbol",
            "Accper": "accper",
            "Annodt": "announce_date",
            "Audittyp": "audit_type",
            "Auditor": "auditor",
            "Dcost": "audit_fee_domestic",
        }
    )
    frame["fiscal_year"] = pd.to_datetime(frame["accper"], errors="coerce").dt.year
    frame = frame.dropna(subset=["fiscal_year"])
    frame["fiscal_year"] = frame["fiscal_year"].astype(int)
    frame = _ensure_columns(
        frame, ["audit_type", "auditor", "audit_fee_domestic", "announce_date"]
    )
    frame["opinion_class"] = frame["audit_type"].map(classify_opinion)
    frame["mod_opinion"] = frame["opinion_class"].isin(MODERATE_CLASSES).astype(int)
    frame["mod_opinion_wide"] = frame["opinion_class"].isin(LENIENT_CLASSES).astype(int)
    frame["big4"] = frame["auditor"].map(_is_big4)
    frame["audit_fee"] = _to_float(frame["audit_fee_domestic"])
    columns = [
        "symbol",
        "fiscal_year",
        "accper",
        "announce_date",
        "audit_type",
        "opinion_class",
        "mod_opinion",
        "mod_opinion_wide",
        "auditor",
        "big4",
        "audit_fee",
    ]
    out = frame[columns].copy()
    out = out.sort_values(["symbol", "fiscal_year"]).drop_duplicates(
        ["symbol", "fiscal_year"], keep="first"
    )
    return out.reset_index(drop=True)


def _split_codes(value: object) -> list[str]:
    if not isinstance(value, str):
        return []
    text = value
    for sep in CODE_SEPARATORS:
        text = text.replace(sep, ";")
    return [part.strip() for part in text.split(";") if part.strip()]


def _is_disclosure_violation(violation_type: object, type_ids: object) -> int:
    text = violation_type if isinstance(violation_type, str) else ""
    if any(keyword in text for keyword in DISCLOSURE_KEYWORDS):
        return 1
    codes = set(_split_codes(type_ids))
    return int(bool(codes & DISCLOSURE_CODES))


def parse_violations(path: Path | str = VIOLATION_FILE) -> pd.DataFrame:
    """Parse STK_Violation_Main.xlsx into one row per announcement."""
    frame = _read_export(path)
    frame = _drop_non_data(frame, "Symbol")
    frame = frame.rename(
        columns={
            "Symbol": "symbol",
            "ViolationID": "violation_id",
            "DeclareDate": "declare_date",
            "DisposalDate": "disposal_date",
            "ViolationType": "violation_type",
            "ViolationTypeID": "violation_type_ids",
            "ViolationYear": "violation_years",
            "PunishmentType": "punishment_type",
            "Promulgator": "promulgator",
        }
    )
    frame = _ensure_columns(
        frame,
        [
            "violation_id",
            "declare_date",
            "disposal_date",
            "violation_type",
            "violation_type_ids",
            "violation_years",
            "punishment_type",
            "promulgator",
        ],
    )
    frame["declare_date"] = pd.to_datetime(frame["declare_date"], errors="coerce")
    frame = frame.dropna(subset=["declare_date"])
    frame["declare_year"] = frame["declare_date"].dt.year.astype(int)
    frame["is_disclosure"] = [
        _is_disclosure_violation(vtype, vids)
        for vtype, vids in zip(frame["violation_type"], frame["violation_type_ids"])
    ]
    columns = [
        "symbol",
        "violation_id",
        "declare_date",
        "declare_year",
        "disposal_date",
        "violation_type",
        "violation_type_ids",
        "violation_years",
        "punishment_type",
        "promulgator",
        "is_disclosure",
    ]
    out = frame[columns].copy()
    out = out.drop_duplicates(["symbol", "declare_date", "violation_type"])
    return out.reset_index(drop=True)


def build_event_table(
    sample: pd.DataFrame,
    audit: pd.DataFrame | None = None,
    violations: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Attach audit-opinion labels and t+1 violation labels to a sample frame.

    Parameters
    ----------
    sample : DataFrame with at least ``symbol`` and ``fiscal_year``.
    audit : optional pre-parsed audit frame (parsed from disk when omitted).
    violations : optional pre-parsed violation frame.
    """
    base = sample[["symbol", "fiscal_year"]].copy()
    base["symbol"] = _clean_code(base["symbol"])
    base["fiscal_year"] = base["fiscal_year"].astype(int)

    if audit is None:
        audit = parse_audit_opinions()
    audit_cols = [
        "symbol",
        "fiscal_year",
        "audit_type",
        "opinion_class",
        "mod_opinion",
        "mod_opinion_wide",
        "auditor",
        "big4",
        "audit_fee",
        "announce_date",
    ]
    merged = base.merge(audit[audit_cols], on=["symbol", "fiscal_year"], how="left")

    if violations is None:
        violations = parse_violations()
    counts = (
        violations.groupby(["symbol", "declare_year"])
        .agg(
            violation_count=("violation_id", "size"),
            violation_disclosure_count=("is_disclosure", "sum"),
        )
        .reset_index()
    )
    # t+1 alignment: an announcement in calendar year t+1 refers to the
    # annual report of fiscal year t that was published in that year.
    forward = counts.copy()
    forward["declare_year"] = forward["declare_year"] - 1
    forward = forward.rename(columns={"declare_year": "fiscal_year"})
    merged = merged.merge(
        forward.rename(
            columns={
                "violation_count": "violation_any_t1",
                "violation_disclosure_count": "violation_disclosure_t1",
            }
        ),
        on=["symbol", "fiscal_year"],
        how="left",
    )
    # Contemporaneous announcements (year t) are kept for robustness only.
    same_year = counts.rename(
        columns={
            "declare_year": "fiscal_year",
            "violation_count": "violation_any_t",
            "violation_disclosure_count": "violation_disclosure_t",
        }
    )
    merged = merged.merge(same_year, on=["symbol", "fiscal_year"], how="left")

    for column in (
        "violation_any_t1",
        "violation_disclosure_t1",
        "violation_any_t",
        "violation_disclosure_t",
    ):
        merged[column] = merged[column].fillna(0).astype(int)
    merged["violation_any_t1"] = (merged["violation_any_t1"] > 0).astype(int)
    merged["violation_disclosure_t1"] = (merged["violation_disclosure_t1"] > 0).astype(int)
    merged["violation_any_t"] = (merged["violation_any_t"] > 0).astype(int)
    merged["violation_disclosure_t"] = (merged["violation_disclosure_t"] > 0).astype(int)

    merged["mod_opinion"] = merged["mod_opinion"].fillna(0).astype(int)
    merged["mod_opinion_wide"] = merged["mod_opinion_wide"].fillna(0).astype(int)
    merged["has_audit_record"] = merged["audit_type"].notna().astype(int)
    merged["opinion_class"] = merged["opinion_class"].fillna("missing")

    return merged.sort_values(["symbol", "fiscal_year"]).reset_index(drop=True)


def event_summary(table: pd.DataFrame) -> dict[str, object]:
    """Small diagnostic dictionary used by the CLI script and the report."""
    labels = (
        "mod_opinion",
        "mod_opinion_wide",
        "violation_any_t1",
        "violation_disclosure_t1",
    )
    summary: dict[str, object] = {
        "n_firm_years": int(len(table)),
        "n_firms": int(table["symbol"].nunique()),
        "audit_coverage": round(float(table["has_audit_record"].mean()), 4),
    }
    for label in labels:
        summary[f"{label}_rate"] = round(float(table[label].mean()), 4)
        summary[f"{label}_count"] = int(table[label].sum())
    summary["by_year"] = {
        int(year): {
            "n": int(len(group)),
            **{
                label: round(float(group[label].mean()), 4)
                for label in labels
            },
        }
        for year, group in table.groupby("fiscal_year")
    }
    return summary
