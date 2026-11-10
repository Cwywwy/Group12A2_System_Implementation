"""One-off: prepend today's changelog bullets under the 2026-11-11 heading."""

from pathlib import Path

path = Path("CHANGELOG.md")
text = path.read_text(encoding="utf-8")
header = "## 2026-11-11\n"
assert header in text, "heading missing"

bullets = """
- 新增 §5.6「从第一版到第二版：做法改进与结果差异」（英文 `5.6 From the First to the Second Specification`）与 Table 5.4（10×3 设定对比）：`build_section5.py` 增加 `_load_v01_metrics()`（读冻结的 `outputs/.tmp/v01_dual_benchmark/tables/`）、`_table_54()` / `_table_54_cn()`、`s56a`/`s56b` 段落与 Word 插入逻辑（英文锚 §5.5 正文、中文锚 `CN_SLOT_S55`），markdown 与中英 docx 同步。
- 终稿重建：英文 `Group12A2_Final_EN.docx` 101 段 4 表 → PDF **14 页**（在 12–15 页要求内），中文 `Group12A2_Final_CN.docx` 65 段 4 表 → PDF 8 页；摘要结果句同步为 v0.2（融合 0.103 / 财务 0.136 / 校准 1.84 / legacy 1.20）。
- 两版过程固化：新增 git tag `v0.1-baseline`（提交 `542395b`，第一版代码：引导词典 + 子串计数 + 仅 M > −1.78）与 `v0.2-calibrated`（第二版），第一版的数据/结果备份清单写入复现指南 §7；新增提交 `b700d27` 与清理提交 `4687e46`（不再跟踪版式探针临时文件）。
- 新增 `scripts/analyze_branch_beneish_components.py` 与 `outputs/tables/branch_component_correlations.csv`：把 M-Score 拆成 DSRI/GMI/AQI/SGI/DEPI/SGAI/LVGI/TATA 八个分量分别与四个排序求 Spearman ρ，实测文本单独对任一分量 |ρ| ≤ 0.064（财务对 DSRI −0.181、SGI 0.171）→ 排除"基准太粗"这一零成本分支。
- 新增 `outputs/reports/positive_result_branches.md`：7 个换结果变量分支的可行性评估（t+1 年报问询函为首选、非标审计意见为兜底、重述/处罚备选、内控否定与业绩预告修正排除），含数据来源、成本、文献先验、时间对齐与幸存者偏差风险清单、开工第一天的 CSMAR 订阅核对清单。
- 文档同步：`docs/manuscript_chinese_draft.md` 新增中文 5.6（含 10×3 表）；`docs/reproducibility_guide.md` 新增 §3.1 分支评估与 §7 两版版本控制条目；`GUIDE.md` 阶段表新增 `analyze_branch_beneish_components.py`。
- 单测：`tests/test_build_section5.py` 新增 Table 5.4 形状、中文表头与 §5.6 段落断言，全套 **88/88 通过**。
"""
text = text.replace(header, header + bullets, 1)
path.write_text(text, encoding="utf-8")
print("changelog updated")
