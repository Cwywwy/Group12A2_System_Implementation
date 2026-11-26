"""Assemble the Chinese manuscript markdown from the three translated parts.

Tables are copied from the English deliverable so the two versions cannot
drift: only labels are translated, every number stays byte-identical.
"""
from __future__ import annotations

from pathlib import Path

from docx import Document

WORK = Path("outputs/work")
OUT = Path("docs/manuscript_chinese_draft.md")
EN_DOCX = Path("outputs/manuscript/Group12A2_Final_EN_v0.5.docx")

LABELS = {
    "Model": "模型",
    "Spearman rho": "Spearman ρ",
    "p-value": "p 值",
    "Finance-only IF": "仅财务 IF",
    "Text-only IF": "仅文本 IF",
    "Fused IF": "融合 IF",
    "Fused autoencoder": "融合自编码器",
    "Score": "分数",
    "AUC: opinion": "AUC：非标意见",
    "AUC: disclosure violation t+1": "AUC：t+1 披露违规",
    "Lift: opinion": "lift：非标意见",
    "Lift: disclosure violation": "lift：披露违规",
    "finance-only IF": "仅财务 IF",
    "text-only IF": "仅文本 IF",
    "fused IF": "融合 IF",
    "fused AE": "融合 AE",
    "Beneish M-Score": "Beneish M 值",
    "Feature set": "特征集",
    "ΔAUC vs finance": "相对仅财务的 ΔAUC",
    "Finance only": "仅财务",
    "Logit": "Logit",
    "Gradient boosting": "梯度提升",
    "Text only": "仅文本",
    "Fused": "融合",
    "Panel A: sample frame": "Panel A：样本框架",
    "Years": "年份",
    "n": "n",
    "Events": "事件数",
    "AUC: finance-only": "AUC：仅财务",
    "AUC: Beneish": "AUC：Beneish",
    "Manufacturing (C)": "制造业（C）",
    "All non-financial industries": "全部非金融行业",
    "Panel B: outcome label, 2021-2024 non-financial sample":
        "Panel B：结果标签（2021-2024 非金融样本）",
    "AUC: text-only": "AUC：仅文本",
    "AUC: fused": "AUC：融合",
    "Modified audit opinion in t": "t 年非标审计意见",
    "Annual-report inquiry letter in t+1": "t+1 年报问询函",
    "Annual-report restatement announced in t+1 (strict)": "t+1 年报重述（严格口径）",
    "Feature": "特征",
    "mean": "均值",
    "std": "标准差",
    "min": "最小值",
    "max": "最大值",
    "k": "k",
    "Event rate (legacy)": "事件率（legacy）",
    "Enrichment (legacy)": "富集倍数（legacy）",
    "Event rate (recalibrated)": "事件率（样本校准）",
    "Enrichment (recalibrated)": "富集倍数（样本校准）",
    "Design choice": "设计选择",
    "First specification (v0.1)": "第一设定（v0.1）",
    "Second specification (v0.2)": "第二设定（v0.2）",
    "Sentiment lexicon": "情感词典",
    "Bootstrap list of 38 positive / 33 negative terms": "引导版：正 38 / 负 33 词",
    "Yao et al. (2021): 3,585 positive / 1,633 negative terms":
        "Yao et al.（2021）：正 3,585 / 负 1,633 词",
    "Lexicon matching": "词典匹配方式",
    "Substring counting on raw text": "原始文本子串计数",
    "jieba token match with a 5,218-term user dictionary": "jieba 词元精确匹配（用户词典 5,218 词）",
    "Sentiment hits per 1,000 tokens": "每千词元情感词命中",
    "Uncertainty list": "不确定性词表",
    "23 terms": "23 词",
    "About 100 terms (Loughran-McDonald and Zeng et al.)":
        "约 100 词（Loughran-McDonald 与 Zeng et al.）",
    "Beneish benchmark": "Beneish 基准",
    "Literal M > -1.78 only": "仅取 M > -1.78",
    "Literal M > -1.78 and sample top decile (M > -1.44, 10%)":
        "M > -1.78 与样本前十分位（M > -1.44，10%）双口径",
    "Text-only / fused rank correlation": "仅文本 / 融合秩相关",
    "Autoencoder rank correlation (p)": "自编码器秩相关（p 值）",
    "Text-only top-10% enrichment (recalibrated)": "仅文本前 10% 富集（样本校准）",
    "Answer to RQ1": "对 RQ1 的回答",
    "No incremental value for the Beneish screen": "对 Beneish 筛选无增量价值",
    "Unchanged for the Beneish screen; small positive but statistically indistinguishable increments in supervised models (Table 5.6)":
        "Beneish 筛选结论不变；监督式模型仅有小幅正向但统计上无法区分的增量（表 5.3）",
    "Definition": "定义",
    "Outcome label": "结果标签",
    "Fused - finance": "融合 − 仅财务",
    "Text - finance": "仅文本 − 仅财务",
    "Calendar-year t+1": "日历年 t+1",
    "Any violation announced in t+1": "t+1 年公告的任意违规",
    "Logistic": "逻辑回归",
    "Disclosure violation announced in t+1": "t+1 年公告的披露类违规",
    "Modified audit opinion (narrow)": "非标审计意见（窄口径）",
    "Modified audit opinion (wide)": "非标审计意见（宽口径）",
    "Strict gate": "严格闸门",
    "Step": "步骤",
    "Rule applied": "适用规则",
    "Firm-years dropped": "剔除公司-年",
    "Firm-years retained": "保留公司-年",
    "Manufacturing firm-year frame, 2021-2025": "制造业公司-年样本框架（2021-2025）",
    "Beneish M-Score computable (previous-year statement available)":
        "Beneish M 值可计算（上一年度报表可得）",
    "All six financial features non-missing": "六项财务特征均无缺失",
    "All three MD&A features non-missing": "三项 MD&A 特征均无缺失",
    "Analysis sample (3,773 firms)": "分析样本（3,773 家公司）",
    "Any opinion other than unqualified in t": "t 年非标准无保留意见（含保留、无法表示、否定）",
    "322 (2.0% of 16,408)": "322（占 16,408 的 2.0%）",
    "Not applicable": "不适用",
    "Also counts unqualified opinions with an explanatory paragraph in t":
        "另计入 t 年带解释性说明段的无保留意见",
    "593 (3.6% of 16,408)": "593（占 16,408 的 3.6%）",
    "Any STK_Violation announcement dated in the calendar year after the report":
        "报告披露日之后一个日历年内公告的任意 STK_Violation 记录",
    "1,965 (21.3% of 9,239)": "1,965（占 9,239 的 21.3%）",
    "1,543 of 1,965 (78.5%)": "1,543 / 1,965（78.5%）",
    "Delayed disclosure, misstatement, material omission, fictitious profit or assets":
        "推迟披露、虚假记载、重大遗漏、虚构利润或资产",
    "1,337 (14.5% of 9,239)": "1,337（占 9,239 的 14.5%）",
    "1,040 of 1,337 (77.8%)": "1,040 / 1,337（77.8%）",
}

CAPTION_PREFIX = {
    0: "**表 5.1.",
    1: "**表 5.2.",
    2: "**表 5.3.",
    3: "**表 A1.",
    4: "**表 B1.",
    5: "**表 B2.",
    6: "**表 B3.",
    7: "**表 B4.",
    8: "**表 B5.",
    9: "**表 B6.",
}

PIPELINE_FIGURE = (
    "**图 4.1. 从样本框到复核队列的研究流程**",
    "",
    "注：三条带分别是获取、特征构建与建模阶段，按执行顺序排列；每一阶段都写出可检查的 "
    "CSV 产物，因此任一阶段都可凭其输入独立重跑。",
    "",
)


def md_table(rows: list[list[str]]) -> str:
    header, body = rows[0], rows[1:]
    lines = ["| " + " | ".join(header) + " |",
             "|" + "|".join([" --- "] * len(header)) + "|"]
    for row in body:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def main() -> None:
    doc = Document(EN_DOCX)
    parts = [(WORK / f"cn_part{n}.md").read_text(encoding="utf-8").strip()
             for n in (1, 2, 3)]
    text = "\n\n".join(parts)
    text = text.replace(
        "将它带有非标准审计意见的公司—年度观测排到样本其余观测之下(AUC 0.242)，而仅财务排序达到 0.802",
        "它将带有非标准审计意见的公司—年度观测排到样本其余观测之下（AUC 0.263），而仅财务排序达到 0.787",
    )

    lines = text.split("\n")
    inserted = 0
    for index, table in enumerate(doc.tables):
        rows = [[cell.text.strip() for cell in row.cells] for row in table.rows]
        rows = [[LABELS.get(cell, cell) for cell in row] for row in rows]
        block = md_table(rows).split("\n")
        prefix = CAPTION_PREFIX[index]
        for position, line in enumerate(lines):
            if line.startswith(prefix):
                lines[position + 1:position + 1] = [""] + block
                inserted += 1
                break
        else:
            raise SystemExit(f"caption not found for table {index}")
    text = "\n".join(lines)

    lines = text.split("\n")
    for position, line in enumerate(lines):
        if line.startswith("### 4.2 "):
            lines[position:position] = list(PIPELINE_FIGURE)
            break
    else:
        raise SystemExit("subsection 4.2 not found")
    text = "\n".join(lines)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    if OUT.exists():
        backup = OUT.with_suffix(".md.bak")
        backup.write_text(OUT.read_text(encoding="utf-8"), encoding="utf-8")
    OUT.write_text(text, encoding="utf-8")
    print(f"wrote {OUT} ({inserted} tables, {len(text):,} chars)")


if __name__ == "__main__":
    main()
