# -*- coding: utf-8 -*-
"""
csmar_parser.py
Author: Group12A2 DSW Team
Purpose: Parse the three CSMAR financial statement tables into the intermediate
         finance table used by src/features/financial.py and beneish.py.
Module: src/data_ingestion

CSMAR exports vary in layout between versions, so the parser is tolerant:
- header detection supports the modern layout (row of item codes such as
  Stkcd/Accper/A001101000), the older Chinese-label layout, and an optional
  English-name companion row below the code row;
- the same row is used to pair item codes with readable names so both
  code-based and name-based alias matching work;
- consolidated statements are filtered via the Typrep/Statement Type column
  (values A/B or 1/2);
- several date formats are accepted;
- unknown columns are ignored and missing optional columns become NaN and are
  reported by missing_field_report.

Revision History
-----------------
2026-11-05  initial version.
2026-11-06  real-file validation against FS_Combas.xlsx: modern CSMAR exports
            use an English code row (no Chinese labels), plus a unit row that
            must be dropped; add CODE_ALIASES, English name aliases, Typrep
            detection and companion-name-row pairing; drop rows whose fiscal
            year fails to parse (removes name/unit rows generically).
2026-11-23  keep annual (12-31) rows only and merge the three statements on
            symbol and fiscal year instead of row position (fixes year-lagged
            balance sheets and cross-firm-year feature merges).
"""
from pathlib import Path

import numpy as np
import pandas as pd

from src.features.financial import FINANCE_COLS

# Chinese keywords: keep for older Chinese-header exports.
HEADER_KEYWORDS = (
    "资产总计", "负债合计", "营业收入", "营业成本", "净利润",
    "经营活动产生的现金流量净额", "货币资金", "应收账款净额", "销售费用",
)

# Modern CSMAR exports identify the header row by these identifier cells.
IDENTIFIER_CELLS = ("Stkcd", "Symbol", "证券代码", "股票代码")

# Exact CSMAR item codes (balance sheet verified against FS_Combas[DES]).
CODE_ALIASES: dict[str, list[str]] = {
    "cash": ["A001101000"],
    "receivables": ["A001111000"],
    "current_assets": ["A001100000"],
    "fixed_assets": ["A001212000"],
    "total_assets": ["A001000000"],
    "current_liabilities": ["A002100000"],
    "long_term_debt": ["A002201000"],
    "total_liabilities": ["A002000000"],
    # Income statement codes: the operating (not "total operating") item is
    # the documented definition, so B001101000/B001201000 take precedence over
    # the total-revenue/total-cost fallbacks that appear earlier in the export.
    "revenue": ["B001101000", "B001100000"],
    "cogs": ["B001201000", "B001200000"],
    "sga_sales": ["B001209000", "B001303000", "B001302000"],
    "sga_admin": ["B001210000", "B001304000", "B001305000"],
    "net_income": ["B002000000"],
    "ocf": ["C001000000"],
    # This direct-method cash-flow export has no depreciation line (its C00
    # codes cover operating/investing/financing cash flows only), so the field
    # stays NaN and Beneish DEPI is held at its neutral value 1.0.
    "depreciation": [],
}

# Column aliases -> intermediate fields. Order matters: first match wins.
FIELD_ALIASES: dict[str, list[str]] = {
    "symbol": ["证券代码", "Stkcd", "股票代码", "Symbol"],
    "fiscal_year": ["报告期", "Accper", "截止日期", "会计期间", "EndDate"],
    "revenue": ["营业收入"],
    "cogs": ["营业成本"],
    "total_assets": ["资产总计", "资产合计"],
    "total_liabilities": ["负债合计"],
    "current_assets": ["流动资产合计"],
    "current_liabilities": ["流动负债合计"],
    "receivables": ["应收账款净额", "应收账款"],
    "fixed_assets": ["固定资产净额", "固定资产"],
    "long_term_debt": ["长期借款"],
    "cash": ["货币资金"],
    "depreciation": ["固定资产折旧"],
    "sga_sales": ["销售费用"],
    "sga_admin": ["管理费用"],
    "net_income": ["净利润"],
    "ocf": ["经营活动产生的现金流量净额"],
}

# English names from the modern CSMAR export (paired from the companion row).
NAME_ALIASES_EN: dict[str, list[str]] = {
    "revenue": ["Operating Revenue"],
    "cogs": ["Operating Cost", "Operating Costs"],
    "total_assets": ["Total Assets"],
    "total_liabilities": ["Total Liabilities"],
    "current_assets": ["Total Current Assets"],
    "current_liabilities": ["Total Current Liabilities"],
    "receivables": ["Net Accounts Receivable", "Accounts Receivable"],
    "fixed_assets": ["Net Fixed Assets", "Fixed Assets"],
    "long_term_debt": ["Long-term Loans", "Long-term Borrowings"],
    "cash": ["Cash and Cash Equivalents"],
    "depreciation": [
        "Fixed Assets Depreciation",
        "Depreciation of Fixed Assets",
        "Fixed-assets Depreciation",
    ],
    "sga_sales": ["Selling Expenses", "Sales Expenses"],
    "sga_admin": ["Administrative Expenses"],
    "net_income": ["Net Profit"],
    "ocf": [
        "Net Cash Flows from Operating Activities",
        "Net Cash Flow from Operating Activities",
    ],
}

CONSOLIDATED_MARKERS = {"合并报表", "合并", "A", "1", "1.0"}
REPORT_TYPE_KEYWORDS = ("Typrep", "报表类型", "StatementType", "Statement Type", "类型编码", "报表类型编码")

SAMPLE_FISCAL_YEARS = (2020, 2021, 2022, 2023)


def _normalise_header(value) -> str:
    return "" if value is None else str(value).strip()


def _looks_like_name_row(values: list[list], start: int) -> int | None:
    """First row after `start` that reads like an English name row."""
    for i in range(start, min(start + 3, len(values))):
        cells = [_normalise_header(v) for v in values[i]]
        if any("no unit" in c.lower() for c in cells):
            continue
        readable = [c for c in cells if len(c) >= 3 and c[:1].isalpha()]
        if len(readable) >= 3:
            return i
    return None


def _find_header_row(values: list[list]) -> int | None:
    """Return the header row index for either CSMAR export layout."""
    for i, row in enumerate(values):
        cells = [_normalise_header(cell) for cell in row]
        if any(cell in IDENTIFIER_CELLS for cell in cells):
            return i
    for i, row in enumerate(values):
        joined = "|".join(_normalise_header(cell) for cell in row)
        if any(keyword in joined for keyword in HEADER_KEYWORDS):
            return i
    return None


def _parse_period_end(value) -> str | None:
    """Normalise a reported period to YYYY-MM-DD (used to keep annual rows only)."""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return None
    if isinstance(value, (int, np.integer)) and 19000101 <= int(value) <= 21001231:
        text = str(int(value))
        return f"{text[:4]}-{text[4:6]}-{text[6:8]}"
    text = str(value).strip()
    if len(text) >= 8 and text[:8].isdigit() and 19000101 <= int(text[:8]) <= 21001231:
        return f"{text[:4]}-{text[4:6]}-{text[6:8]}"
    stamp = pd.to_datetime(text, errors="coerce")
    if pd.isna(stamp):
        return None
    return stamp.strftime("%Y-%m-%d")


def _parse_period(value) -> int | None:
    """Accept 2021-12-31, 20211231, 2021/12/31, datetime/date objects -> fiscal year."""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return None
    if isinstance(value, (int, np.integer)) and 20190101 <= int(value) <= 20241231:
        return int(value) // 10000
    text = str(value).strip()
    if len(text) >= 8 and text[:8].isdigit() and 20190101 <= int(text[:8]) <= 20241231:
        return int(text[:4])
    for part in text.replace("/", "-").split(" ")[0].split("-"):
        if len(part) == 4 and part.isdigit() and 2019 <= int(part) <= 2023:
            return int(part)
    return None


def _filter_consolidated(df: pd.DataFrame) -> pd.DataFrame:
    """Keep only consolidated rows when a report-type column exists."""
    type_cols = [c for c in df.columns if any(k in str(c) for k in REPORT_TYPE_KEYWORDS)]
    if not type_cols:
        return df
    mask = df[type_cols].apply(
        lambda row: any(_normalise_header(v) in CONSOLIDATED_MARKERS for v in row), axis=1
    )
    return df[mask]


def _to_number(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series.astype(str).str.replace(",", "", regex=False), errors="coerce")


def _resolve_column(data: pd.DataFrame, field: str, name_map: dict[str, str]) -> str | None:
    """Find the best column for `field` by code, then Chinese, then English name."""
    candidates: list[str] = list(CODE_ALIASES.get(field, [])) + FIELD_ALIASES[field] + NAME_ALIASES_EN.get(field, [])
    for alias in candidates:
        if alias in data.columns:
            return alias
        for column, name in name_map.items():
            if column in data.columns and name == alias:
                return column
    return None


def probe_field_columns(path: Path, header_probe_rows: int = 3) -> dict[str, int]:
    """Map each intermediate field to its raw column index without a full read.

    Useful for very large exports: the caller can then pass
    `usecols=sorted(set(indices.values()))` to read_csmar_table and only
    materialise the columns the pipeline needs.
    """
    probe = pd.read_excel(path, header=None, nrows=header_probe_rows, dtype=str)
    header_row = _find_header_row(probe.values.tolist())
    if header_row is None:
        raise ValueError(f"未在文件中定位到表头行（未发现已知字段）：{path}")
    name_row = _looks_like_name_row(probe.values.tolist(), header_row + 1)
    header_cells = [_normalise_header(v) for v in probe.iloc[header_row].tolist()]
    name_cells = (
        [_normalise_header(v) for v in probe.iloc[name_row].tolist()]
        if name_row is not None
        else [""] * len(header_cells)
    )

    indices: dict[str, int] = {}
    for field in list(FIELD_ALIASES) + ["report_type"]:
        if field == "report_type":
            for i, (header, name) in enumerate(zip(header_cells, name_cells)):
                if any(k in header or k in name for k in REPORT_TYPE_KEYWORDS):
                    indices["report_type"] = i
                    break
            continue
        # Alias priority, not column order: the first alias that exists in the
        # file wins, so specific items (营业成本) beat "total" items that happen
        # to appear in an earlier column.
        aliases = (
            list(CODE_ALIASES.get(field, []))
            + list(FIELD_ALIASES[field])
            + list(NAME_ALIASES_EN.get(field, []))
        )
        for alias in aliases:
            hit = None
            for i, (header, name) in enumerate(zip(header_cells, name_cells)):
                if header == alias or name == alias:
                    hit = i
                    break
            if hit is not None:
                indices[field] = hit
                break
    return indices


def read_csmar_table(
    path: Path,
    usecols: list[int] | None = None,
    header_probe_rows: int = 3,
) -> pd.DataFrame:
    """Read one CSMAR table into the FINANCE_COLS intermediate schema.

    When `usecols` is given (column indices of the raw file), only those
    columns are materialised, which keeps very large exports within memory.
    """
    probe = pd.read_excel(path, header=None, nrows=header_probe_rows, dtype=str)
    header_row = _find_header_row(probe.values.tolist())
    if header_row is None:
        raise ValueError(f"未在文件中定位到表头行（未发现已知字段）：{path}")
    name_row = _looks_like_name_row(probe.values.tolist(), header_row + 1)
    name_map: dict[str, str] = {}

    if usecols is None:
        raw = pd.read_excel(path, header=None, dtype=str)
        columns = [_normalise_header(v) for v in raw.iloc[header_row].tolist()]
        if name_row is not None:
            name_map = dict(zip(
                columns,
                [_normalise_header(v) for v in raw.iloc[name_row].tolist()],
            ))
        data = raw.iloc[header_row + 1:].copy()
    else:
        raw = pd.read_excel(path, header=None, dtype=str, usecols=usecols)
        columns = [_normalise_header(v) for v in probe.iloc[header_row, usecols].tolist()]
        if name_row is not None:
            name_map = dict(zip(
                columns,
                [_normalise_header(v) for v in probe.iloc[name_row, usecols].tolist()],
            ))
        data = raw.copy()
    data.columns = columns
    data = _filter_consolidated(data)

    mapped: dict[str, pd.Series | None] = {}
    for field, _aliases in FIELD_ALIASES.items():
        column = _resolve_column(data, field, name_map)
        mapped[field] = data[column] if column else None

    out = pd.DataFrame()
    if mapped["symbol"] is None:
        raise ValueError(f"缺少证券代码列：{path}")
    out["symbol"] = (
        mapped["symbol"].astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(6)
    )
    if mapped["fiscal_year"] is None:
        raise ValueError(f"缺少报告期列：{path}")
    out["fiscal_year"] = mapped["fiscal_year"].apply(_parse_period)
    out["period_end"] = mapped["fiscal_year"].apply(_parse_period_end)
    out = out[out["fiscal_year"].notna()].copy()

    for field in FINANCE_COLS[2:]:
        if field == "sga":
            parts = [mapped[k] for k in ("sga_sales", "sga_admin") if mapped[k] is not None]
            if parts:
                out["sga"] = _to_number(parts[0])
                for extra in parts[1:]:
                    out["sga"] = out["sga"].add(_to_number(extra), fill_value=0)
            else:
                out["sga"] = np.nan
            continue
        out[field] = _to_number(mapped[field]) if mapped[field] is not None else np.nan
    return out


def build_finance_intermediate(
    balance_path: Path,
    income_path: Path,
    cashflow_path: Path,
    fiscal_years: tuple[int, ...] = SAMPLE_FISCAL_YEARS,
) -> pd.DataFrame:
    """Merge the three tables into one FINANCE_COLS table for 2020-2023.

    CSMAR exports are quarterly, so each statement contains opening-balance
    rows (YYYY-01-01) as well as interim periods. Only the annual (12-31)
    consolidated row per firm-year may be kept, and the three statements are
    merged on ("symbol", "fiscal_year") rather than by row position: positional
    merges silently pair a balance sheet with another firm-year's income
    statement whenever the tables differ in coverage.
    """
    parts = []
    for path in (balance_path, income_path, cashflow_path):
        table = read_csmar_table(path)
        table = table[table["period_end"].str[5:] == "12-31"]
        table = table[table["fiscal_year"].isin(fiscal_years)].copy()
        table = table.groupby(["symbol", "fiscal_year"], as_index=False).first()
        parts.append(table.set_index(["symbol", "fiscal_year"]))
    merged = parts[0]
    for other in parts[1:]:
        merged = merged.combine_first(other)
    merged = merged.reset_index()
    merged = merged[["symbol", "fiscal_year"] + list(FINANCE_COLS[2:])]
    merged = merged.dropna(subset=["symbol", "fiscal_year"]).sort_values(
        ["symbol", "fiscal_year"]
    ).reset_index(drop=True)
    return merged


def missing_field_report(intermediate: pd.DataFrame) -> pd.DataFrame:
    """Count of NaN values per field, to surface incomplete CSMAR selections."""
    report = intermediate[list(FINANCE_COLS[2:])].isna().sum().reset_index()
    report.columns = ["field", "n_missing"]
    return report[report["n_missing"] > 0]
