# -*- coding: utf-8 -*-
"""
run_02b_audit_data.py
Author: Group12A2 DSW Team
Purpose: Re-audit the assembled data for annual-vs-interim contamination and
         format compliance: raw CSMAR period coverage, annual-only filtering,
         symbol-year key alignment, value-level cross-checks against the raw
         exports, PDF year alignment, event-label alignment, and schema/range
         checks on every deliverable table.
Module: scripts

Usage
-----
    .venv\\Scripts\\python.exe scripts/run_02b_audit_data.py

Outputs
-------
    outputs/reports/data_audit_2026-11-23.md   (human-readable audit)
    outputs/reports/data_audit_2026-11-23.json (machine-readable detail)

Revision History
----------------
2026-11-23  initial version: annual/interim contamination and format audit.
"""
from __future__ import annotations

import json
import random
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
RAW = PROJECT_ROOT / "data" / "raw"
CSMAR = RAW / "csmar"
PDF_ROOT = RAW / "cninfo"
PROCESSED = PROJECT_ROOT / "data" / "processed"
OUT = PROJECT_ROOT / "outputs" / "reports"
NARROW = PROJECT_ROOT / "outputs" / ".tmp" / "raw_narrow"

STATEMENT_COLS = {
    "FS_Combas.xlsx": {
        "A001000000": "total_assets",
        "A002000000": "total_liabilities",
        "A001111000": "receivables",
        "A001100000": "current_assets",
        "A001212000": "fixed_assets",
    },
    "FS_Comins.xlsx": {
        "B001101000": "revenue",
        "B001201000": "cogs",
        "B002000000": "net_income",
    },
    "FS_Comscfd.xlsx": {
        "C001000000": "ocf",
    },
}

REPORT: dict[str, object] = {"checks": {}, "issues": [], "generated": ""}
ISSUES: list[str] = REPORT["issues"]  # type: ignore[assignment]


def check(name: str, ok: bool, detail: object = None) -> None:
    REPORT["checks"][name] = {"ok": bool(ok), "detail": detail}
    flag = "PASS" if ok else "FAIL"
    print(f"[{flag}] {name}: {detail}")


def load_raw_narrow(file_name: str) -> pd.DataFrame:
    """Read and cache the period columns plus the fields used by the study."""
    NARROW.mkdir(parents=True, exist_ok=True)
    column_sig = "-".join(sorted(STATEMENT_COLS[file_name]))
    cache = NARROW / (file_name.replace(".xlsx", f"_{abs(hash(column_sig)) % 100000}.pkl"))
    if cache.exists():
        return pd.read_pickle(cache)
    cols = ["Stkcd", "Accper", "Typrep", *STATEMENT_COLS[file_name].keys()]
    frame = pd.read_excel(CSMAR / file_name, header=0, skiprows=[1, 2], usecols=cols)
    frame = frame.rename(columns=STATEMENT_COLS[file_name])
    for column in STATEMENT_COLS[file_name].values():
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame["Stkcd"] = (
        frame["Stkcd"].astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(6)
    )
    frame["Accper"] = pd.to_datetime(frame["Accper"], errors="coerce")
    frame.to_pickle(cache)
    return frame


def audit_raw_periods() -> dict[str, pd.DataFrame]:
    annual: dict[str, pd.DataFrame] = {}
    for file_name in STATEMENT_COLS:
        raw = load_raw_narrow(file_name)
        raw = raw.dropna(subset=["Accper", "Stkcd"])
        month_day = raw["Accper"].dt.strftime("%m-%d")
        counts = month_day.value_counts().to_dict()
        report_rows = raw[raw["Typrep"].astype(str).str.strip() == "A"]
        annual_rows = report_rows[month_day.loc[report_rows.index] == "12-31"].copy()
        annual_rows["fiscal_year"] = annual_rows["Accper"].dt.year
        dup = int(
            annual_rows.duplicated(subset=["Stkcd", "fiscal_year"], keep=False).sum()
        )
        annual[file_name] = annual_rows
        check(
            f"raw/{file_name} 期间分布",
            True,
            {
                "行数": int(len(raw)),
                "Anal": int(len(report_rows)),
                "年度(12-31)行": int(len(annual_rows)),
                "非12-31月份": {k: v for k, v in sorted(counts.items()) if k != "12-31"},
                "年度行重复键": dup,
                "年份范围": [int(annual_rows["fiscal_year"].min()), int(annual_rows["fiscal_year"].max())],
            },
        )
        if dup:
            ISSUES.append(
                f"{file_name}: 年度合并口径存在 {dup} 行 (Stkcd, 年份) 重复，可能是更正版报表"
            )
    return annual


def audit_intermediate(annual: dict[str, pd.DataFrame]) -> None:
    inter = pd.read_csv(
        PROJECT_ROOT / "data" / "interim" / "finance_intermediate.csv",
        dtype={"symbol": str},
    )
    inter["symbol"] = inter["symbol"].str.zfill(6)
    check(
        "intermediate/仅含样本年度 2020–2023",
        bool(inter["fiscal_year"].between(2020, 2023).all()),
        inter["fiscal_year"].value_counts().sort_index().to_dict(),
    )
    dup = int(inter.duplicated(["symbol", "fiscal_year"]).sum())
    check("intermediate/无重复公司-年度", dup == 0, {"行数": len(inter), "重复": dup})

    # Value-level cross-check against the raw annual rows, all firm-years.
    keys = ["Stkcd", "fiscal_year"]
    merged = inter.merge(
        annual["FS_Combas.xlsx"][[*keys, "total_assets", "total_liabilities"]],
        left_on=["symbol", "fiscal_year"],
        right_on=keys,
        how="left",
        suffixes=("", "_raw"),
    )
    merged = merged.merge(
        annual["FS_Comins.xlsx"][[*keys, "revenue", "cogs", "net_income"]],
        on=keys,
        how="left",
        suffixes=("", "_raw"),
    )
    merged = merged.merge(
        annual["FS_Comscfd.xlsx"][[*keys, "ocf"]],
        on=keys,
        how="left",
        suffixes=("", "_raw"),
    )
    for field in ("total_assets", "total_liabilities", "revenue", "cogs", "net_income", "ocf"):
        both = merged[[field, f"{field}_raw"]].dropna()
        scale = both.abs().max(axis=1).replace(0, np.nan)
        diff = (both[field] - both[f"{field}_raw"]).abs()
        mismatched = int((diff > 1e-6 * scale).sum())
        check(
            f"intermediate/{field} 与原始年报一致",
            mismatched == 0,
            {"比对行": int(len(both)), "不一致": mismatched},
        )
        if mismatched:
            sample = merged.loc[
                (merged[field] - merged[f"{field}_raw"]).abs()
                > 1e-6 * merged[[field, f"{field}_raw"]].abs().max(axis=1).replace(0, np.nan),
                ["symbol", "fiscal_year", field, f"{field}_raw"],
            ].head(3)
            ISSUES.append(f"{field} 不一致 {mismatched} 行，示例：{sample.to_dict('records')}")

    # Interim-contamination test: an opening-balance row (YYYY-01-01) repeats the
    # prior year-end, so a row taken from Q1 would reproduce the previous year's
    # figures. Count rows that match the opening value rather than the year-end.
    raw_all = load_raw_narrow("FS_Combas.xlsx")
    month_day = raw_all["Accper"].dt.strftime("%m-%d")
    opening = raw_all[month_day == "01-01"][["Stkcd", "Accper", "total_assets"]].copy()
    opening["fiscal_year"] = opening["Accper"].dt.year
    opening = opening.rename(columns={"total_assets": "assets_open"})
    year_end = annual["FS_Combas.xlsx"][["Stkcd", "fiscal_year", "total_assets"]].rename(
        columns={"total_assets": "assets_close"}
    )
    probe = (
        inter.merge(
            opening[["Stkcd", "fiscal_year", "assets_open"]],
            left_on=["symbol", "fiscal_year"],
            right_on=["Stkcd", "fiscal_year"],
            how="left",
        )
        .merge(year_end, on=["Stkcd", "fiscal_year"], how="left")
        .dropna(subset=["assets_open", "assets_close"])
    )
    same_open = np.isclose(probe["total_assets"], probe["assets_open"], rtol=1e-9, atol=1e-6)
    same_close = np.isclose(probe["total_assets"], probe["assets_close"], rtol=1e-9, atol=1e-6)
    contaminated = int((same_open & ~same_close).sum())
    neither = int((~same_open & ~same_close).sum())
    check(
        "intermediate/无季报期初数混入（01-01 行回归测试）",
        contaminated == 0,
        {
            "可比行": int(len(probe)),
            "等于期初数且不等于期末数": contaminated,
            "两者皆不等（可能为追溯调整）": neither,
        },
    )
    if neither:
        ISSUES.append(
            f"{neither} 行总资产既不等同原始年报期末数、也不等同期初数，需核对是否为追溯调整"
        )

    # Lag test: does assets(t) equal raw assets(t-1)? (the old bug signature)
    assets = annual["FS_Combas.xlsx"][["Stkcd", "fiscal_year", "total_assets"]].copy()
    assets["prev_assets"] = assets.groupby("Stkcd")["total_assets"].shift(1)
    assets["prev_year"] = assets.groupby("Stkcd")["fiscal_year"].shift(1)
    lagged = inter.merge(
        assets[["Stkcd", "fiscal_year", "total_assets", "prev_assets", "prev_year"]],
        left_on=["symbol", "fiscal_year"],
        right_on=["Stkcd", "fiscal_year"],
        how="left",
        suffixes=("", "_raw"),
    )
    comparable = lagged.dropna(subset=["total_assets_raw", "prev_assets"])
    comparable = comparable[comparable["prev_year"] == comparable["fiscal_year"] - 1]
    equal_prev = int(
        np.isclose(
            comparable["total_assets_raw"], comparable["prev_assets"], rtol=1e-9, atol=1e-6
        ).sum()
    )
    check(
        "intermediate/无一年滞后特征（旧缺陷回归测试）",
        equal_prev == 0,
        {"可比行": int(len(comparable)), "总资产等于上年值": equal_prev},
    )

    # Feature identities re-derived from the intermediate.
    from src.features.financial import compute_finance_features
    from src.features.beneish import compute_beneish

    rebuilt = compute_beneish(compute_finance_features(inter))
    features = pd.read_csv(
        PROJECT_ROOT / "data" / "processed" / "feature_table.csv", dtype={"symbol": str}
    )
    features["symbol"] = features["symbol"].str.zfill(6)
    joined = features.merge(
        rebuilt, on=["symbol", "fiscal_year"], how="left", suffixes=("", "_calc")
    )
    for field in ("roa", "leverage", "ocf_to_assets", "accruals_to_assets", "m_score"):
        a = joined[field]
        b = joined[f"{field}_calc"]
        diff = (a - b).abs()
        tol = 1e-8 * a.abs().clip(lower=1.0)
        bad = int(((diff > tol) & a.notna() & b.notna()).sum())
        check(
            f"feature_table/{field} 可由中间表重算",
            bad == 0,
            {"可比": int((a.notna() & b.notna()).sum()), "不一致": bad},
        )
        if bad:
            ISSUES.append(f"feature_table.{field} 重算不一致 {bad} 行")


def audit_feature_formats() -> None:
    features = pd.read_csv(PROJECT_ROOT / "data" / "processed" / "feature_table.csv")
    checks = {
        "行数=10,172": len(features) == 10172,
        "公司-年度无重复": not features.duplicated(["symbol", "fiscal_year"]).any(),
        "年份⊂{2021,2022,2023}": set(features["fiscal_year"].unique()) <= {2021, 2022, 2023},
        "end_date 全为 YYYY-12-31": (features["end_date"].astype(str).str[5:] == "12-31").all(),
        "行业代码全以 C 开头": features["industry_code_d"].astype(str).str.startswith("C").all(),
        "symbol 6 位（读入后）": features["symbol"].astype(str).str.zfill(6).str.len().eq(6).all(),
        "readability ∈ (0,1]": bool(
            features["readability"].dropna().between(0, 1, inclusive="right").all()
        ),
        "sentiment_balance ∈ [-1,1]": bool(
            features["sentiment_balance"].dropna().between(-1, 1).all()
        ),
        "uncertainty_ratio ∈ [0,1]": bool(
            features["uncertainty_ratio"].dropna().between(0, 1).all()
        ),
        "n_tokens 非负": bool((features["n_tokens"].dropna() >= 0).all()),
        "text_status 取值合法": set(features["text_status"].dropna()) <= {
            "ok", "no_mda", "pdf_error"
        },
        "text_quality 取值合法": set(features["text_quality"].dropna()) <= {
            "ok", "suspicious", "missing"
        },
        "金融特征无 inf": not np.isinf(
            features[["roa", "leverage", "revenue_growth", "ocf_to_assets",
                      "receivables_turnover", "accruals_to_assets", "m_score"]].to_numpy()
        ).any(),
        "文本特征与 status 对齐": bool(
            (
                features["text_status"].fillna("missing").eq("ok")
                == features["readability"].notna()
            ).all()
        ),
    }
    for name, ok in checks.items():
        check(f"feature_table/{name}", ok)
        if not ok:
            ISSUES.append(f"feature_table 格式：{name} 未通过")

    # Missingness report vs recomputed counts.
    counts = features["text_quality"].value_counts().to_dict()
    check(
        "feature_table/文本缺失计数",
        counts.get("ok") == 9991 and counts.get("suspicious") == 7 and counts.get("missing") == 174,
        counts,
    )


def audit_pdf_year_alignment(sample_size: int = 120) -> None:
    """Check sampled PDFs actually report the fiscal year in the row."""
    from pypdf import PdfReader

    features = pd.read_csv(
        PROJECT_ROOT / "data" / "processed" / "feature_table.csv", dtype={"symbol": str}
    )
    features["symbol"] = features["symbol"].str.zfill(6)
    ok_rows = features[features["text_status"] == "ok"]
    rng = random.Random(20261123)
    sample = ok_rows.sample(n=min(sample_size, len(ok_rows)), random_state=rng.randint(0, 10**6))
    mismatches: list[dict] = []
    missing = 0
    for row in sample.itertuples():
        path = PDF_ROOT / str(int(row.fiscal_year)) / f"{row.symbol}_{int(row.fiscal_year)}_annual_report.pdf"
        if not path.exists():
            missing += 1
            continue
        try:
            reader = PdfReader(str(path))
            text = "".join((reader.pages[i].extract_text() or "") for i in range(min(2, len(reader.pages))))
        except Exception as exc:  # noqa: BLE001 - audit should keep going
            mismatches.append({"symbol": row.symbol, "year": int(row.fiscal_year), "error": str(exc)})
            continue
        found = re.findall(r"(20\d{2})\s*年年度报告", text)
        if not found:
            found = re.findall(r"(20\d{2})\s*年度报告", text)
        if found and str(int(row.fiscal_year)) not in found:
            mismatches.append(
                {"symbol": row.symbol, "year": int(row.fiscal_year), "pdf_year": found[:3]}
            )
        if "摘要" in text[:400] and "年度报告摘要" in text[:400]:
            mismatches.append({"symbol": row.symbol, "year": int(row.fiscal_year), "note": "摘要件"})
    check(
        "PDF/文件年份与报告期一致（抽样）",
        len(mismatches) == 0,
        {"抽样": len(sample), "缺失文件": missing, "不一致": mismatches[:5], "不一致数": len(mismatches)},
    )
    if mismatches:
        ISSUES.append(f"PDF 年份抽样不一致 {len(mismatches)} 例：{mismatches[:3]}")


def audit_events() -> None:
    events = pd.read_csv(
        PROJECT_ROOT / "data" / "processed" / "event_table.csv", dtype={"symbol": str}
    )
    events["symbol"] = events["symbol"].str.zfill(6)
    check(
        "event_table/覆盖完整样本（行数与 6 位代码）",
        events["symbol"].str.len().eq(6).all() and len(events) == len(events.drop_duplicates()),
        {"行数": len(events), "公司": int(events["symbol"].nunique())},
    )
    coverage = events.groupby("fiscal_year")["has_audit_record"].mean().round(4).to_dict()
    scores_path = PROJECT_ROOT / "outputs" / "tables" / "anomaly_scores.csv"
    if scores_path.exists():
        scores = pd.read_csv(scores_path, dtype={"symbol": str})
        scores["symbol"] = scores["symbol"].str.zfill(6)
        keys_scores = set(zip(scores["symbol"], scores["fiscal_year"]))
        keys_events = set(zip(events["symbol"], events["fiscal_year"]))
        check(
            "event_table/键集与建模样本一致",
            keys_scores == keys_events,
            {
                "scores": len(keys_scores),
                "events": len(keys_events),
                "仅事件有": len(keys_events - keys_scores),
                "仅模型有": len(keys_scores - keys_events),
            },
        )
    check("event_table/审计意见覆盖", all(v > 0.99 for v in coverage.values()), coverage)
    counts = events.groupby("fiscal_year")[["violation_any_t1", "violation_disclosure_t1"]].sum()
    check("event_table/t+1 违规按年分布", True, counts.astype(int).to_dict())

    # Raw coverage of the violation export: which announcement years exist?
    raw = pd.read_excel(
        RAW / "csmar_events" / "STK_Violation_Main.xlsx", dtype=str, sheet_name=0
    ).iloc[2:]
    dates = pd.to_datetime(raw["DeclareDate"], errors="coerce")
    years = dates.dt.year.dropna().astype(int)
    check(
        "raw/违规公告年份覆盖（t+1 是否可观测）",
        years.max() >= 2024,
        {"最小": int(years.min()), "最大": int(years.max()),
         "各年": years.value_counts().sort_index().to_dict()},
    )
    if years.max() < 2024:
        ISSUES.append(
            "违规公告数据最大年份早于 2024：2023 财年的 t+1 标签不可观测，会机械性偏低"
        )


def audit_outputs() -> None:
    tables = PROJECT_ROOT / "outputs" / "tables"
    for path in sorted(tables.glob("*.csv")):
        frame = pd.read_csv(path)
        numeric = frame.select_dtypes("number")
        bad = int(numeric.isna().sum().sum())
        inf = int(np.isinf(numeric.to_numpy(dtype=float, na_value=np.nan)).sum())
        check(
            f"outputs/{path.name} 数值完整",
            bad == 0 and inf == 0,
            {"行": len(frame), "列": list(frame.columns)[:6], "NaN": bad, "inf": inf},
        )


def main() -> None:
    from datetime import datetime

    REPORT["generated"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    print("== 原始 CSMAR 期间检查 ==")
    annual = audit_raw_periods()
    print("== 中间表与原始年报逐值比对 ==")
    audit_intermediate(annual)
    print("== 特征表格式检查 ==")
    audit_feature_formats()
    print("== 事件表检查 ==")
    audit_events()
    print("== 输出表检查 ==")
    audit_outputs()
    print("== PDF 年份抽样检查 ==")
    audit_pdf_year_alignment()

    OUT.mkdir(parents=True, exist_ok=True)
    json_path = OUT / "data_audit_2026-11-23.json"
    json_path.write_text(json.dumps(REPORT, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    failures = [name for name, item in REPORT["checks"].items() if not item["ok"]]

    lines = [
        "# 数据审计：季报/年报错漏与格式合规",
        "",
        f"- 审计时间：{REPORT.get('generated', '')}",
        f"- 通过 {len(REPORT['checks']) - len(failures)} / {len(REPORT['checks'])}",
        f"- 失败：{failures if failures else '无'}",
        f"- 待人工确认：{ISSUES if ISSUES else '无'}",
        "",
        "| 检查项 | 结果 | 细节 |",
        "| --- | --- | --- |",
    ]
    for name, item in REPORT["checks"].items():
        detail = str(item.get("detail", "")).replace("|", "/")
        lines.append(
            f"| {name} | {'PASS' if item['ok'] else 'FAIL'} | {detail[:400]} |"
        )
    md_path = OUT / "data_audit_2026-11-23.md"
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"\n通过 {len(REPORT['checks']) - len(failures)} / {len(REPORT['checks'])}；失败：{failures}")
    print(f"报告：{md_path}")


if __name__ == "__main__":
    main()

