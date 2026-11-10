# -*- coding: utf-8 -*-
"""
run_07_experiment.py
Author: Group12A2 DSW Team
Purpose: Phase 4 driver: pipeline run + report figures + summary markdown.
Module: scripts

Usage:
    .venv/Scripts/python scripts/run_07_experiment.py [feature_table.csv]

Exit codes: 2 = feature table missing (run run_06 first / wait for CSMAR data).

Revision History
-----------------
2026-11-06  initial version.
"""
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config import OUTPUTS
from src.pipeline import run_pipeline
from src.reporting.figures import make_all_figures

DEFAULT_FEATURE_CSV = Path("data/processed/feature_table.csv")


def _write_summary(summary: dict, out_path: Path) -> None:
    lines = [
        "# 实验摘要（自动生成）",
        "",
        f"- 生成时间：{datetime.now():%Y-%m-%d %H:%M}",
        f"- 有效样本：{summary['n_rows']} 个 firm-year（9 特征 + M-Score 完整）",
        "",
        "## Spearman 秩相关（异常得分 vs Beneish M-Score）",
        "",
        "| 模型 | ρ |",
        "| --- | --- |",
    ]
    for model, rho in summary["spearman"].items():
        lines.append(f"| {model} | {rho} |")
    lines += [
        "",
        "## top-10% 审查名单表现（样本校准基准：M-Score top-10%）",
        "",
        "| 模型 | 事件率 | 富集率 |",
        "| --- | --- | --- |",
    ]
    for model in summary["spearman"]:
        lines.append(
            f"| {model} | {summary['event_rate_top10'][model]} | {summary['enrichment_top10'][model]} |"
        )
    lines += [
        "",
        "## top-10% 审查名单表现（legacy 基准：M > -1.78）",
        "",
        "| 模型 | 事件率 | 富集率 |",
        "| --- | --- | --- |",
    ]
    for model in summary["spearman"]:
        lines.append(
            f"| {model} | {summary['event_rate_top10_legacy'][model]} | {summary['enrichment_top10_legacy'][model]} |"
        )
    lines += [
        "",
        f"- IF-融合模型审查优先第 1 名：{summary['top1_symbol']}",
        "",
        "图件见 outputs/figures/，明细表见 outputs/tables/。",
    ]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    feature_csv = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_FEATURE_CSV
    if not feature_csv.exists():
        print(f"[run_07] 缺少特征表：{feature_csv}")
        print("[run_07] 请先运行 run_06（需 CSMAR 三表与逐年文本特征），或使用演示数据：")
        print("[run_07]   .venv\\Scripts\\python scripts\\run_03_make_demo_data.py")
        return 2

    summary = run_pipeline(feature_csv)
    figures = make_all_figures(OUTPUTS / "tables", OUTPUTS / "figures")
    _write_summary(summary, OUTPUTS / "reports" / "experiment_summary.md")

    print(f"[run_07] 有效样本 n={summary['n_rows']}")
    print(f"[run_07] Spearman ρ = {summary['spearman']}")
    print(f"[run_07] top-10% 富集率（样本校准）= {summary['enrichment_top10']}")
    print(f"[run_07] top-10% 富集率（legacy -1.78）= {summary['enrichment_top10_legacy']}")
    print(f"[run_07] 审查优先第 1 名 = {summary['top1_symbol']}")
    for path in figures:
        print(f"[run_07] 图件: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
