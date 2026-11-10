# -*- coding: utf-8 -*-
"""
strip_result_backticks.py
Author: Group12A2 DSW Team
Purpose: Remove the Markdown backticks that still wrap result values in the
         Chinese draft, while keeping code identifiers (pdf_error, SEED=42, etc.).
Module: scripts/probe (ad-hoc, one-shot)
"""
from pathlib import Path

path = Path("docs/manuscript_chinese_draft.md")
text = path.read_text(encoding="utf-8")

# Only strip backticks around result values; leave code identifiers alone.
result_values = [
    "8,140", "3,265", "0.103", "0.136", "0.738", "1.176", "−0.030", "0.012",
    "98.8%", "96.5%–99.0%", "65.9%", "34.1%",
    "财务特征组",
    "表 5.1", "表 5.3",
    "无法解析的 PDF、扫描件或少于 300 token 的短文本，以及巨潮未收录的北交所挂牌前年份",
    "提供弱但正向的筛查信号（事件率为全样本基准的 1.18 倍）",
    "经营现金流/总资产（0.324）、营收增长率（0.317）、可读性（0.315）",
    "000820（2021 年，子行业 C42）",
    "应收账款周转率、营收增长率、经营现金流/总资产",
    "财务特征主导融合排序，文本特征贡献有限",
    "财务单独与融合名单 0.828，财务与文本仅 0.120",
    "自编码器重建误差与基准无显著相关（ρ=0.012，p=0.272），未复现主结果",
    "不同模型与阈值",
    "对模型选择敏感，宜作为筛查信号而非稳定风险标签",
    "融合异常检测的财务特征与 Beneish M-Score 呈弱但显著正相关（ρ=0.136，前 10% 富集 1.22），但文本特征未带来增量，自编码器稳健性未复现",
    "文本特征未带来增量（融合 0.103 低于财务单独 0.136）",
    "文本特征未带来增量价值（融合 0.103 低于财务单独 0.136），RQ1 不成立",
]

for value in result_values:
    text = text.replace(f"`{value}`", value)

path.write_text(text, encoding="utf-8")

leftover = [w for w in text.split() if w.startswith("{") and w.endswith("}")]
print("remaining placeholders:", leftover if leftover else "NONE")
print("wrote", path)
