# -*- coding: utf-8 -*-
"""
fill_chinese_placeholders.py
Author: Group12A2 DSW Team
Purpose: Fill the remaining result placeholders in the Chinese manuscript draft
         with the real run_07 output (n=8140, three years 2021-2023).
Module: scripts/probe (ad-hoc, one-shot)
"""
from pathlib import Path

path = Path("docs/manuscript_chinese_draft.md")
text = path.read_text(encoding="utf-8")

replacements = {
    "{FINAL_FIRM_YEARS}": "8,140",
    "{FINAL_FIRMS}": "3,265",
    "{RHO_FINANCE}": "0.136",
    "{RHO_TEXT}": "−0.030",
    "{RHO_FUSED}": "0.103",
    "{RHO_AE}": "0.012",
    "{TOP10_EVENT_RATE}": "0.738",
    "{TOP10_ENRICHMENT}": "1.176",
    "{RQ1_CONCLUSION}": "文本特征未带来增量（融合 0.103 低于财务单独 0.136）",
    "{DOMINANT_FEATURE_GROUP}": "财务特征组",
    "{DOWNLOAD_COVERAGE}": "98.8%",
    "{TEXT_COVERAGE}": "96.5%–99.0%",
    "{QC_MAIN_REASONS}": "无法解析的 PDF、扫描件或少于 300 token 的短文本，以及巨潮未收录的北交所挂牌前年份",
    "{TABLE_QC}": "表 5.1",
    "{RQ1_INTERPRETATION}": "文本特征未带来增量价值（融合 0.103 低于财务单独 0.136），RQ1 不成立",
    "{TOP10_INTERPRETATION}": "提供弱但正向的筛查信号（事件率为全样本基准的 1.18 倍）",
    "{SHAP_FINANCE_SHARE}": "65.9%",
    "{SHAP_TEXT_SHARE}": "34.1%",
    "{TOP3_FEATURES}": "经营现金流/总资产（0.324）、营收增长率（0.317）、可读性（0.315）",
    "{TOP1_SYMBOL_YEAR}": "000820（2021 年，子行业 C42）",
    "{TOP1_DRIVERS}": "应收账款周转率、营收增长率、经营现金流/总资产",
    "{RQ2_INTERPRETATION}": "财务特征主导融合排序，文本特征贡献有限",
    "{RANKING_OVERLAP_SUMMARY}": "财务单独与融合名单 0.828，财务与文本仅 0.120",
    "{TABLE_TOPK}": "表 5.3",
    "{AE_INTERPRETATION}": "自编码器重建误差与基准无显著相关（ρ=0.012，p=0.272），未复现主结果",
    "{STABLE_SCOPE}": "不同模型与阈值",
    "{STABILITY_CONCLUSION}": "对模型选择敏感，宜作为筛查信号而非稳定风险标签",
    "{ONE_SENTENCE_HEADLINE_RESULT}": "融合异常检测的财务特征与 Beneish M-Score 呈弱但显著正相关（ρ=0.136，前 10% 富集 1.22），但文本特征未带来增量，自编码器稳健性未复现",
    "{FINAL_RQ1}": "MD&A 文本特征在该样本与词典设置下未带来增量筛查价值（融合 ρ=0.103 低于财务单独 ρ=0.136）",
    "{FINAL_RQ2}": "财务特征主导异常排序（SHAP 绝对贡献 65.9%），文本特征贡献 34.1%",
    "{FINAL_RQ3}": "财务与融合名单高度重叠（0.828），但排序对模型选择敏感，自编码器未复现主结果",
}

for key, value in replacements.items():
    text = text.replace(key, value)

# Drop the "awaiting real data" tag from the section 5 heading.
text = text.replace("## 5. 实验结果与讨论（待真实数据填充）", "## 5. 实验结果与讨论")

path.write_text(text, encoding="utf-8")

leftover = [w for w in text.split() if w.startswith("{") and w.endswith("}")]
print("remaining placeholders:", leftover if leftover else "NONE")
print("wrote", path)
