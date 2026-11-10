# 论文终稿组装清单（12-15 交付用）

File:     docs/manuscript_assembly_checklist.md
Author:   Group12A2 DSW Team
Purpose:  把评分标准 Option 2（12–15 页研究稿件）要求与仓库内已有素材逐节对齐，
          标出每节来源文件、状态与剩余工作，供组员合并终稿时对照。

Revision History:
  2026-11-06  initial version.

## 一、评分要求（Grading and Report Requirement，Option 2 Research Manuscript）

- 12–15 页正文 + 12 分钟 / 12 页演示；里程碑 22 Sep 5% / 6 Oct 10% / 10 Nov 15% /
  24 Nov 10% / 15 Dec 10% 终稿+演示。
- 小组最多 3 人（⚠️ 现署 4 人，需与教授确认，见风险）。

## 二、稿件逐节对照表

| # | 稿件节 | 来源文件（现稿） | 状态 | 剩余工作 |
| --- | --- | --- | --- | --- |
| 题名页 | Title + 4 位作者 + 学号 | Group12A2 docx 首页 | 已有 | 与教授确认 4 人是否合规 |
| 摘要 | Abstract + Keywords | Group12A2 docx（已是终稿语气，英文） | 基本定稿 | 实证数字出来后可补 1 句结论性结果 |
| 1 | Introduction | Group12A2 docx §1（含 3 个 RQ） | 基本定稿 | 无 |
| 2 | Literature Review | Group12A2 docx §2（21 篇文献） | 基本定稿 | 无 |
| 3 | Research Design & Methodology | docs/manuscript_methodology_section.md（过去时已写，超参已填实） | 已定稿 | 与 §4 措辞最终对齐 |
| 4 | System Implementation | docs/manuscript_implementation_section.md（6 页英文，已写） | 基本定稿 | 无（状态附录已更新为当前数字） |
| 5 | Experiment & Results | docs/manuscript_experiment_section.md（模板）+ outputs/reports/results_narrative.md（run_12 自动生成） | 待真实数据 | 数据齐后跑 run_99 → run_12 出叙事 → 填表图 |
| 6 | Conclusion | docs/manuscript_conclusion_section.md（英文草稿，已写） | 基本定稿 | 填头条结果句（1 处占位） |
| 参考 | References | Group12A2 docx §References（21 条已全） | 需补 3 条词典来源 | 见下「待补参考文献」 |

## 三、待补参考文献（词典出处，proposal 21 条中缺失）

词典文件 `data/external/dictionaries/` 头部注释声明的来源，终稿 References 必须补全，否则 §4.3 的词典出处与参考文献不一致：

1. 姚加权等 (2021)《中国上市公司文本信息披露的情感分析》——正向/负向情感词典骨架。
2. Loughran T, McDonald B (2011). When is a liability not a liability? Textual analysis, dictionaries, and 10-Ks. *Journal of Finance*, 66(1), 35–65. —— uncertain 词表英译来源。
3. 曾庆生等 (2018) 年报语调研究常用词——不确定性词补充。

⚠️ 词典当前为「初始引导版 v0.1」（正向 38 / 负向 33 / 不确定 23 词的小子集），
复现指南 §5 与实现章节 §4.3 均已如实披露「定稿前需替换为完整公开词表并注明版本号」；
若最终来不及替换，须在论文局限中明确说明词典规模与引导性质（已具备披露文案）。

## 四、方法学事实来源（终稿核对时逐项对齐仓库）

- 特征字典：docs/feature_dictionary.md（6 财务 + 3 文本，公式/字段/分母/离群值/标准化全定）
- 样本框规则：scripts/run_01_sample.py + src/data/sample_frame.py（制造业=IndustryCodeD startswith C）
- 财务中间表：scripts/run_03_build_finance_intermediate.py + src/data/financial.py（Beneish M 由三表算）
- 下载/提取：scripts/run_02/run_05 + src/cninfo/（巨潮公开接口、断点续传、审计）
- 建模：src/models/（Isolation Forest 500 trees/max_samples 256/SEED 42；autoencoder sklearn MLPRegressor）
- 评估：src/metrics/（Spearman vs M-Score、top-10% 事件率/富集率、top-k 重叠）
- 复现入口：docs/reproducibility_guide.md（含 §6 一键流程 run_99）

## 五、剩余写作文本（按优先级）

1. §5 实验章节填表图（依赖真实数据，跑 run_99 后由 run_12 自动生成叙事草稿）。
2. §6 结论填头条结果句（1 处占位，真实数据出来后）。
3. 摘要补一句结论性结果（真实数据出来后）。
4. 12 页 slides 文案（docs/slides_deck_draft.md 已备骨架，数据出来填图）。

## 六、风险

- **4 人组 vs "up to 3 members"**：最硬风险，需尽快与教授确认，否则影响演示打分。
- 数据缺口：FS_Comins/FS_Comscfd 未到 → 财务特征无法建 → 实验阻塞（等组员放入 data/raw/csmar/）。
- MD&A 提取进行中（约 2–3 小时），完成后 QC 收口。
