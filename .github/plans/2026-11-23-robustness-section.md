# 计划：把分支实验并入主论文（§5.8 稳健性与测量敏感性 + Table 5.7）

- 状态：**已完成**（2026-11-23，编号按用户确认改为 §5.8；执行结果见文末「执行结果」）
- 触发：用户 2026-11-23 指示把 `DSW_all` / `DSW_dv` / `DSW_bdpi` / `DSW_branch` 的分支实验并入主论文，作为稳健性与测量敏感性证据；不改既有结论方向、不改既有数字。
- 依据：`DSW_all/docs/extension_findings.md`（§4 2×2、§5 逐年阈值）、`DSW_dv/docs/dv_findings.md`（六标签、宽/严口径）、`DSW_branch/docs/branch_findings.md`（TF-IDF，仅作对照）。

## 已核现状（改动前基线，只读核对）

| 项目 | 实测 | 说明 |
| --- | --- | --- |
| 英文母本 | `11.23base/Group12A2_Final_EN_corrected.docx` | 131 段 / 6 表 / 6 内嵌图；全部段落样式 `Normal` |
| 母本可重建性 | 0 差异 | 用 `outputs/.tmp/apply_corrected_results.py` 从 `11.23base/Group12A2_Final_EN_.docx` 重跑，131 段文本与 6 表单元格逐一相同（`outputs/.tmp/repro_check.docx`） |
| 页数/词数 | **20 页 / 7,303 词**（Word COM 实测；A4、上下 1 英寸、1.45 倍行距） | 图件合计高 16.2 英寸 ≈ 1.7 页 |
| 中文版 | `outputs/manuscript/Group12A2_Final_CN.docx` | 73 段 / 6 表 / 0 图；可由 `outputs/manuscript/source/Group12A2_Final_CN.docx` 经 `patch_docx_cn` 重建（0 差异） |
| 测试基线 | `.venv\Scripts\python.exe -m pytest -q` → **126 passed** | Python 3.12.14（PATH 上的 3.4.4 不可用） |
| § 编号 | §5 只有 5.1–5.7，**没有 5.8** | 用户说的是"§5.9"，故编号需决策（风险 R1） |

## 目标与范围

**做**：新增一节稳健性/测量敏感性叙述与一张表；把三处"no incremental value"收窄到 Beneish 型无监督排序；摘要补一句（≤40 词）；结论补一句监督式小幅改善（≤0.018）；中英 docx、§5 markdown 源、CHANGELOG 同步。

**不做**：不重算任何实验（数字一律取上述三份 memo）；不改表 5.1–5.6 与图 5.1–5.6 的任何数值；不动主样本口径（§5.1–5.7 仍是 9,239 firm-years 制造业 2021–23）；TF-IDF 分支不写进正文表格（用户约束），正文最多一句对照或不写。

## 模块划分

| 模块 | 职责 | 交互 | 状态 |
| --- | --- | --- | --- |
| `scripts/build_section5.py` | 唯一文本/数字源：新增 `EXT_NUMBERS`、`_table_57()`/`_table_57_cn()`、`s59_*` 中英段落、收窄句与摘要句 | 被两个 patch 入口调用 | 修改 |
| `outputs/.tmp/apply_corrected_results.py` | 从 `EN_.docx` 重建英文母本；新增 14 段 + 1 表插入 | 写 `11.23base/…_corrected.docx` | 修改 |
| `scripts/build_section5.py::patch_docx` | 维护 `outputs/manuscript/Group12A2_Final_EN.docx`（非交付件，避免漂移） | 同上 | 修改 |
| `scripts/build_section5.py::patch_docx_cn` | 重建中文交付件 | 写 `outputs/manuscript/Group12A2_Final_CN.docx` | 修改 |
| `tests/test_build_section5.py` | 新增 Table 5.7 形状/取值、`s59_*` 键、收窄句断言 | — | 修改 |
| 文档 | `docs/manuscript_experiment_section.md`、`docs/manuscript_chinese_experiment_section.md`、`CHANGELOG.md` | — | 修改 |

## §5.9 结构与字数预算（英文，正文 745 词）

| 序 | 段落 | 目标词数 |
| --- | --- | --- |
| 1 | 标题 `5.9 Robustness across Samples, Years and Outcome Definitions` | 8 |
| 2 | 导语：三条稳健性轴；声明本节是测量敏感性诊断，不改变 RQ1 的答案 | 70 |
| 3 | `5.9.1 Industry and Sample Year` | 5 |
| 4 | 2×2 设计与样本说明（完整案例、修正意见 t）+ 表引 | 105 |
| 5 | Table 5.7 表题 | 30 |
| 6 | 表后解读：行业边际 −0.024～−0.030、年份 ≤0.011 → 衰减来自行业构成 | 100 |
| 7 | `5.9.2 Threshold Calibration` | 4 |
| 8 | 合并阈值富集 0.637 / 0.630 / 0.767；逐年 q90 −1.26→−1.68 | 95 |
| 9 | 分年后倒挂更明显（2022–24 富集 <1，2024 仅 0.20–0.34）；与 §5.4 逐年 rho 稳定不矛盾 | 85 |
| 10 | `5.9.3 Outcome Definitions` | 4 |
| 11 | 六标签对照口径（固定样本 18,415；只报三个窄标签，宽口径噪声明说） | 100 |
| 12 | 基准错配解读：Beneish 只在修正意见上倒挂（0.277），更正/问询回到 0.44–0.53 | 105 |
| 13 | `5.9.4 Two Negative Results` | 4 |
| 14 | 扩展词典（+42/+51，ρ −0.027→−0.028）与 B+C+D+I（14,937，0.776/0.271） | 85 |

合计约 796 词（含标题与表题），落在 600–800 上沿。若需压到 700 以内：删段 9 的"与 §5.4 一致"句、段 14 的词典句。

## Table 5.7 位置与构造

- **插入锚点**：第 100 段（`The external validation is the sharpest test in this paper`）之后、第 101 段（`6. Conclusion, Limitations, and Ethical Boundary`）之前。新段占 P101–P114，原"6. Conclusion"顺延为 P115，References 由 P106 顺延为 P120，总段数 131 → **145**。
- **表体**：9 行 × 6 列，双面板，编号 **Table 5.7**（表数 6 → 7）。

| 行 | A | B | C | D | E | F |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | Sample | Years | n | Events | Finance IF AUC | Beneish M-Score AUC |
| 1 | Manufacturing (C) | 2021–23 | 9,239 | 204 | 0.802 | 0.242 |
| 2 | Manufacturing (C) | 2021–24 | 12,586 | 254 | 0.791 | 0.248 |
| 3 | Non-financial, all industries | 2021–23 | 13,556 | 380 | 0.772 | 0.273 |
| 4 | Non-financial, all industries | 2021–24 | 18,415 | 469 | 0.767 | 0.277 |
| 5 | Panel B: outcome label (n = 18,415) | Events | Finance IF | Text IF | Fused IF | Beneish |
| 6 | Modified opinion (t) | 469 | 0.767 | 0.537 | 0.745 | 0.277 |
| 7 | Annual restatement (t+1, strict) | 449 | 0.629 | 0.484 | 0.605 | 0.443 |
| 8 | Annual inquiry (t+1) | 604 | 0.632 | 0.481 | 0.607 | 0.477 |

- **构造方式**：`copy.deepcopy` 复制现有表 5.6（`T005`，7 行 × 6 列，列数正好一致）的 `tbl` 元素 → 深拷贝 2 个数据行补齐 9 行 → `addnext` 到表题段之后 → 逐格改写文本（沿用 `set_cell` 的 run 写法，样式与边框随模板保留）。表宽沿用模板列宽。
- **表题**：`Table 5.7. Robustness across samples, years and outcome definitions. Panel A: complete-case sample with a modified audit opinion in t. Panel B: three outcome labels on the fixed 2021-2024 non-financial sample.`

## 收窄句（三处，逐一给改写后文本）

1. 摘要 P003：`add no incremental value to the unsupervised screen` → `add no incremental value to the Beneish-style unsupervised screen`。
2. §5.5 P082：`The negative claim is that the three MD&A features do not improve the unsupervised ranking against the Beneish M-Score (…)` → `The negative claim is narrower than a null for text as such: the three MD&A features do not improve the Beneish-style unsupervised ranking (rho -0.018 fused, -0.021 finance-only, against -0.026 for text alone).`（数字零改动）
3. 结论 P102：保留原句并把"ranking"限定为"Beneish-style unsupervised ranking"，其后追加一句：`On the supervised event labels in §5.9 the fused block does add a small increment, at most 0.018 AUC over financial features, which leaves the answer to RQ1 unchanged.`

## 摘要新增句（≤40 词，候选 31 词）

`Widening the sample from manufacturing to all non-financial industries (n = 9,239 to 18,415) costs the screen 0.024-0.030 AUC at a fixed year, and on regulatory labels fusion gains at most 0.018.`

## 阶段与完成标准

| 阶段 | 内容 | 完成标准 | 状态 |
| --- | --- | --- | --- |
| 1 | 备份母本与中文件到 `outputs/.tmp/backup_pre_robustness/` | 可回滚 | 待办 |
| 2 | `build_section5.py`：新增 `EXT_NUMBERS`、`_table_57`/`_table_57_cn`、`s59_*` 中英段落、收窄句、摘要句；`render_markdown*` 接上 | `--markdown` 生成无占位、节次连续 | 待办 |
| 3 | `apply_corrected_results.py`：14 段 + Table 5.7 插入、三处收窄改写 | 母本 145 段 / 7 表 / 6 图 | 待办 |
| 4 | 中文版重建（含 §5.9 与新增表） | 中文 87 段左右 / 7 表；`patch_docx_cn` 从源件可重建 | 待办 |
| 5 | 测试：Table 5.7 形状与行值、`s59_*` 键、收窄句与摘要句断言 | 全量 pytest 通过（126 + 新增，预计 ~132） | 待办 |
| 6 | 文档：两节 markdown、CHANGELOG（2026-11-23 段追加） | 与正文一致 | 待办 |
| 7 | 交付核对：段/表/图计数、8 个旧串零命中、新数字逐项对 memo、Word COM 页数与词数、英式拼写扫描 | 全部通过并写核对报告 | 待办 |

## 验证清单（交付前必跑）

1. 段落 145、表 7、图 6（`len(doc.inline_shapes)`）。
2. 旧串零命中：`8,140` / `3,265` / `62.8` / `0.136` / `0.812` / `600898` / `1,757` / `1,196`。
3. 新数字逐项对 memo：9,239/204/0.802/0.242；12,586/254/0.791/0.248；13,556/380/0.772/0.273；18,415/469/0.767/0.277；0.637/0.630/0.767；−1.26→−1.68；0.537/0.745；449/0.629/0.484/0.605/0.443；604/0.632/0.481/0.607/0.477；−0.018～+0.010（7/12）；14,937/0.776/0.271；ρ −0.027→−0.028。
4. 内部一致性：Table 5.7 第 1 行必须等于 Table 5.5 第 1 行（0.802 / 0.242）与 §5.3 的 n = 9,239。
5. 全量 `pytest`；测试报告落 `tests/reports/`。
6. Word COM 复核页数与词数，若页数增长超 2 页上报。

## 风险与限制

- **R1 编号**：§5 没有 5.8，直接用 "5.9" 会在正文留下空号。建议改为 **5.8**（表号仍是 5.7）；若坚持 5.9，需接受空号。
- **R2 页数**：英文母本已 20 页 / 7,303 词，超出 CHANGELOG 记录的 12–15 页口径；本节再加约 2 页（≈22 页）。三条可选：接受溢出 / 压到 600 词并只留段 6、12（表仍单张）/ 先压图（需另行授权，因为图不能动）。
- **R3 中文结论陈旧**：中文件 P064/P065 仍是旧口径（ρ=0.136、0.103、SHAP 65.9%/34.1%、重叠 0.828、富集 1.22），英文母本已无这些数字。"中英一致"这条验收标准**无法靠只加 §5.9 达成**，必须重写中文结论段；这属于超出 E 项的新增改动，需确认。
- **R4 样本切换**：Panel B 是 18,415 的 2021–24 非金融样本，与 §5.1–5.7 的 9,239 制造业 2021–23 不同；正文必须显式说明，否则读者会以为表 5.5 与 5.7 冲突（表 5.5 的 text/fused 为 0.520/0.769，Panel B 为 0.537/0.745，差异来自样本而非模型）。
- **R5 宽口径标签**：宽口径年报更正噪声大（财务 AUC 0.525 vs 严口径 0.629），表内只报严口径，正文用一句说明为何舍弃宽口径。
- **R6 TF-IDF**：按用户约束不并入主表；正文不出现 TF-IDF 数字，仅在三份 memo 与 CHANGELOG 里留档。如需一句对照，请在确认时说明。

## 预计文件清单

新增：`.github/plans/2026-11-23-robustness-section.md`（本文件）、`tests/reports/<时间戳>.report-N.md`。

修改：`scripts/build_section5.py`、`outputs/.tmp/apply_corrected_results.py`、`tests/test_build_section5.py`、`11.23base/Group12A2_Final_EN_corrected.docx`、`outputs/manuscript/Group12A2_Final_CN.docx`、`outputs/manuscript/Group12A2_Final_EN.docx`、`docs/manuscript_experiment_section.md`、`docs/manuscript_chinese_experiment_section.md`、`CHANGELOG.md`。

## 执行结果（2026-11-23）

### 与计划的偏差

1. **编号 5.9 → 5.8**：用户确认改为 5.8（§5 原本只到 5.7，避免留空号）。
2. **表格形态**：用户确认单表双面板 9×6（面板 A 四行 2×2、面板 B 三行标签），表数 6→7。
3. **"方向一致"改为实测口径**：用户 C 项要求写"小幅但方向一致的改善（≤0.018）"，但 `DSW_dv/docs/dv_findings.md` 记录 12 组中 7 组区间整体为负、范围 −0.018～+0.010。正文因此写"增量绝对值 ≤0.018，且在可与零区分之处为负"，未使用"方向一致"。
4. **中文版范围扩大**：中文结论段原是旧口径（ρ=0.136 / 0.103、富集 1.22、SHAP 65.9%/34.1%、重叠 0.828），仅加 §5.8 无法做到"中英一致"，故一并重写（用户已确认）。
5. **另出精简版**：用户要求"另保留一份：结果在正文只作补充说明、过程移附录、保持 12–15 页"。已产出 `11.23base/Group12A2_Final_EN_corrected_compact.docx`；但正文本身已有 20 页，实测 22 页，**12–15 页不可能靠挪附录达成**，删减菜单见 R2 与测试报告。

### 实测

| 产物 | 段 | 表 | 图 | 页（Word COM） |
| --- | --- | --- | --- | --- |
| `Group12A2_Final_EN_corrected.docx` | 145 | 7 | 6 | **23** |
| `Group12A2_Final_EN_corrected_compact.docx` | 138 | 7 | 6 | **22** |
| `outputs/manuscript/Group12A2_Final_CN.docx` | 87 | 7 | 0 | **10** |

- §5.8 正文 766 词（预算 600–800）；表 5.7 = 9×6；stale 串（8,140 / 3,265 / 62.8 / 0.136 / 0.812 / 600898 / 1,757 / 1,196）三份产物均 0 命中。
- 全套测试 **130 passed**（基线 126 + 新增 4）。


## 精简版压缩执行（2026-11-23 第二轮）

用户指令（m00511）："除参考文献外都执行" —— 清单第 1、2、3、4、6 项执行，第 5 项（参考文献字号/栏数）不做。

### 做了什么

| 项 | 动作 | 结果 |
| --- | --- | --- |
| 1 | §5.6 两版对照（含表 5.4）整节移附录 | 现 Appendix B.2 + 表 B3 |
| 2 | 表 5.3（13 行）移附录 | 现表 B2 |
| 3 | 六图减三图（留 5.2/5.3/5.5） | 删图 5.1/5.4/5.6，余三图重编号 5.1–5.3 |
| 4 | 表 5.1（10 行）移附录 | 现表 B1 |
| 6 | §5.3 SHAP 段合并（并入原图注警语）、版面收紧 | 行距 1.45→1.2，图高上限 2.3 in |
| — | 附录另存为独立文件 | `Group12A2_Final_EN_corrected_compact_appendix.docx` |

### 关键教训

**把表挪进同一文件的附录不减页**——附录仍然打印。第一轮执行后精简版仍是 22 页（正文由 21 页降到 17 页，附录吃掉 4–5 页）。达到 12–15 页需要两件事同时做：附录移出主文件 + 版面收紧。

### 实测（Word COM，每文件新开实例）

| 产物 | 段 | 表 | 图 | 页 | 词 |
| --- | --- | --- | --- | --- | --- |
| `Group12A2_Final_EN_corrected.docx`（母本） | 145 | 7 | 6 | 23 | 8,327 |
| `Group12A2_Final_EN_corrected_compact.docx`（投稿版） | 117 | 3 | 3 | **15** | 6,827 |
| `Group12A2_Final_EN_corrected_compact_appendix.docx`（附录） | 14 | 4 | 0 | 4 | 1,261 |
| `outputs/manuscript/Group12A2_Final_CN.docx` | 87 | 7 | 0 | 10 | 8,678 |

- 编号连续性：正文表 5.1–5.3、图 5.1–5.3、§5.1–5.6；附录表 A1、B1–B3。
- 交叉引用：正文指 `Supplementary Table B1/B2`、`the supplementary appendix`；原 §5.7 → §5.6，原 `Section 5.6` → 补充附录。
- stale 串在四份产物中均 0 命中；全套 **130 passed**。
