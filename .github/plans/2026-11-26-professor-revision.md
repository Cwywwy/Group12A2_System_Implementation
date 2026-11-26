# 计划书：按教授四条意见修订，并将面板扩展到 2021–2025

- 创建日期：2026-11-26
- 项目：Group 12A2 FinTech 期末论文
- 交付截止：2026-12-15（展示同日 19:00）
- Python：3.12.14（`D:\UM study life\session 1\Intro Fintec\Final\DSW\.venv\Scripts\python.exe`）
- 执行位置：主检出版 `D:\UM study life\session 1\Intro Fintec\Final\DSW`，新分支 `feature/panel-2021-2025`
  （数据、`.venv`、`outputs/` 全在主检出；worktree 无 `data/`，且 `src/config.py` 的路径都以模块自身为根，故不在 worktree 执行）

---

## 1. 目标与范围

### 1.1 教授的原始意见与本文档的对应

| # | 教授原话 | 对应改动 | 阶段 |
| --- | --- | --- | --- |
| ① | 更像管理/金融类文章，建议采用管理类参考文献风格 | 全部参考文献转 APA 7 作者-年份制；44 处正文引用改写 | 阶段 4 |
| ② | 数据是否可能包含 2024 和 2025 年 | 面板 2021–2023 → **2021–2025**；违规结局止于 2023 并说明理由 | 阶段 0–2 |
| ③ | 简化或重组第 3、4 部分 | §3 研究方法 + §4 系统实现重排，§4 从 1,231 词压到 400–500 词 | 阶段 3 |
| ④ | 使用图表，为读者提供清晰图像 | 3 图 → 5 图，新增研究流程图与阈值漂移图 | 阶段 5 |

### 1.2 目标

1. 四条意见全部落到可指认的位置（正文段落/图表/参考文献表）。
2. 全稿只有一个样本口径：2021–2025；允许子样本，但每张表自行标注 n 与年份。
3. 决策可复核：每一个数字都由脚本从 `outputs/tables/` 生成，不手改 docx。
4. 学术诚信：不因样本变大而调词典、调参去找显著性；文本无增量的结论照实报告。

### 1.3 不做的部分（明确排除）

- 不补 2020 年（缺 2019 基期，且疫情年会破坏阈值漂移的解释；除非教授另行要求）。
- 不重构模型方法本身（Isolation Forest / Autoencoder / SHAP 的超参与设计不变）。
- 不改 12 页演示稿（用户未列入本次交付范围；数字变化的部分另行处理）。
- 不删除 `outputs/` 历史运行目录，只新增。

---

## 2. 现状基线（实测）

| 项目 | 现值 | 目标 |
| --- | --- | --- |
| 文档页数 | 22（正文 15 + 附录 7） | 内容优先，阶段 6 统一收口 |
| 全文字数 | 8,171 | — |
| §3 研究方法 | 755 词（3.1 201 / 3.2 225 / 3.3 137 / 3.4 192） | 保留方法，参数表下沉附录 |
| §4 系统实现 | 1,231 词（4.1 240 / 4.2 275 / 4.3 88 / 4.4 160 / 4.5 195 / 4.6 273） | **400–500 词**，3 小节 |
| 参考文献 | 24 条（14 条 GB/T 7714 + 10 条 APA 混排） | 24 条统一 APA 7 |
| 正文引用 | 44 处方括号数字，29 个不同编号 | 44 处作者-年份 |
| 图 | 3 张（§5 柱状图） | 5 张 |
| 表 | 正文 3 张 + 附录 7 张 | 正文 4–5 张 + 附录 |
| 样本 | n=9,239，公司 3,488，事件 204 | ≈15,800，事件 ≈320 |
| 财务 AUC / Beneish AUC | 0.802 / 0.242 | 待实跑（2021–24 上为 0.791 / 0.248） |
| 自动化测试 | 172 | ≥180 |

已知缺陷（本次一并修）：
- §4.1 与 §4.6 仍写「114 automated tests, with 114 passing」，实际 172。
- §4.6 的「handoff dated 11 November 2026」与现稿状态不符。

---

## 3. 关键决策与依据

| 决策 | 内容 | 依据 |
| --- | --- | --- |
| D1 面板终点 | 2021–2025 | 用户决定「能拉的都拉」；2025 财报与审计意见已在盘上，PDF 实测可下载 |
| D2 违规结局 | 仅 FY2021–2023 | CSMAR 违规库存在入库滞后：2025 年 807 件（2021–24 均值 1,299，缺约 38%），2026 年 46 件（约 3.5%）。任何抓取都补不回 |
| D3 拟合口径 | 主分析 2021–2025 全体拟合；另加「2021–2024 拟合 → 2025 留出」稳健性 | 与 `run_c24` 设计一致，同时给一个无泄漏的样本外检验 |
| D4 参考文献 | APA 7 作者-年份 | 管理学/金融学主流期刊（JFE、TAR、JAR）均用作者-年份制 |
| D5 §3/§4 重组 | 方法归 §3，工程归 §4，参数进附录表 | 消除 §4.4 复述 §3.3、§4.5 复述 §3.3/3.4 的重复（现重复约 500 词） |
| D6 页数 | 内容优先，阶段 6 再按行距/字号/图表尺寸收口 | 用户选择 |
| D7 交付物 | 英文 v0.4（docx+pdf）、中文稿、两个 Excel；不含 slides | 用户选择 |
| D8 中文稿定位 | 只做英文正文的中文翻译（数字、图表标题、参考文献同步），不改论证 | 用户确认：中文稿是翻译件，不是二次创作 |
| D9 论文内不写修订说明 | 正文与附录都不出现「本次修改…」「回应审稿意见…」类段落 | 用户确认：回复由本人另行处理 |

---

## 4. 模块划分

| 模块 | 职责 | 交互方式 | 状态 |
| --- | --- | --- | --- |
| `src/config.py` | 年份口径单一真源 | 被全部脚本读取 | 修改 |
| `src/data_ingestion/csmar_parser.py` | 财报解析与期间过滤 | 输出 `finance_intermediate.csv` | 修改（年份上限） |
| `src/data_ingestion/cninfo_client.py` | 巨潮检索/下载 | 已被阶段 1 调用 | 不改 |
| `src/sample_frame.py` | 样本框与下载清单 | 生成 `download_checklist.csv` | 修改（年份参数化） |
| `scripts/run_01…run_11` | 数据到实验的流水线 | 顺序调用，产物落 `data/`、`outputs/` | 修改（年份） |
| `scripts/run_07d_holdout_year.py` | 留出年评估 | 读 `anomaly_scores.csv`，写 `holdout_2025.csv` | **新增** |
| `scripts/build_section5.py` | §5 与表格的唯一数字来源 | 写 docx 段落与表 | 修改 |
| `scripts/patch_manuscript_v05.py` | §3/§4 重组 + 引用改写 | 锚点替换 docx | **新增** |
| `src/reporting/references_apa.py` | 24 条文献的作者-年份映射与格式化 | 被 v05 补丁与校验脚本调用 | **新增** |
| `scripts/build_report_figures.py` | 5 张图 | 写 `outputs/figures/*.png` | 修改 |
| `scripts/build_results_excel.py` | 两个工作簿 | 写 `outputs/workbooks/*.xlsx` | 修改 |
| `scripts/run_13_build_chinese_docx.py` | 中文稿 | 写 `outputs/manuscript/*_CN.docx` | 修改 |
| `tests/test_year_window.py` | 年份边界回归测试 | pytest | **新增** |
| `tests/test_references_apa.py` | 引用完整性与格式测试 | pytest | **新增** |

---

## 5. 阶段拆分

> **状态（2026-11-26 收尾）**：阶段 0–6 全部完成，另增阶段 7「独立核验」。
> 交付：`Group12A2_Final_EN_v0.5.docx` / `.pdf`（19 页）、`Group12A2_Final_CN.docx` / `.pdf`（22 页）、
> 两张结果工作簿；测试 203 项全绿；`outputs/reports/audit_2026-11-26.md` 62 项检查 0 失败。
> 未做：2025 留出年（`run_07d`）因 2025 违规标签未定窗口而只保留审计意见口径的说明性文字；
> 页数仍未压缩到 12–15 页（用户 2026-11-26 指示先不处理）。

### 阶段 0：可行性闸门（0.5 天）

- 放开 `csmar_parser.py` 的年份上限（`20241231` → `20251231`，`2019..2023` → `2019..2025`）与 `SAMPLE_FISCAL_YEARS`。
- 用临时脚本重建 2025 年财务特征，只统计完整案例率。
- **完成标准**：2025 年制造业完整案例率 ≥ 2024 年的 90%（2024 约 3,600/3,666）。
- **若不达标**：退回「2025 只做财务单模留出年」，并在附录写明原因，不硬凑。
- 产出：`outputs/reports/phase0_2025_coverage.md`

### 阶段 1：2025 数据获取（4–6 小时，无人值守）

- `run_01_sample.py` 重建样本框（2021–2025），清单新增 `fiscal_2025` 列（制造业 2025 行 3,762）。
- `run_02_download_annual_reports.py`：`--year` 放开到 2025；三个偏移区间并行（`--start/--end`），断点续传。
- `run_04_audit_downloads.py` + `run_09_repair_downloads.py` 收口缺失。
- `run_05_extract_mda_features.py --year 2025`、`run_05b`、`run_05c`。
- **完成标准**：2025 年 PDF 覆盖率 ≥ 97%；MD&A 抽取率 ≥ 98%（2024 年为 99.4%）。
- 产出：`data/raw/cninfo/2025/`、`data/interim/mda_text_2025.jsonl`、`data/processed/text_features_2025*.csv`

### 阶段 2：重跑模型与评估（0.5 天）

- `run_03` → `run_06` → `run_07` → `run_07b` → `run_07c` → `run_08` → `run_11` → `run_12`。
- 违规结局按 D2 限定 FY2021–2023，同时在 `event_ranking_metrics.csv` 中保留全样本但标注删失年份。
- 新增 `run_07d_holdout_year.py`：以 2021–2024 拟合、2025 打分。
- **完成标准**：`outputs/tables/*.csv` 全部为 2021–2025 口径；172 项旧测试仍全绿。
- 产出：新 `anomaly_scores.csv`、`model_metrics.csv`、`topk_metrics.csv`、`shap_*`、`holdout_2025.csv`

### 阶段 3：§3/§4 重组（1 天）

新结构：

- §3 Research Design
  - 3.1 Sample, data and measurement window（吸收 4.2 的数据治理叙述）
  - 3.2 Feature construction（原 3.2）
  - 3.3 Screening and evaluation design（合并原 3.3 + 3.4；参数移入附录 Table C1）
- §4 Implementation
  - 4.1 Pipeline architecture（原 4.1 精简）
  - 4.2 Engineering decisions and QC（原 4.3 + 4.5 的可复现部分）
  - 4.3 Reproduction status（原 4.6 改写：172 项测试、2021–2025 口径）

- **完成标准**：§4 ≤ 500 词；§3+§4 合计 ≤ 1,400 词（原 1,986）；无重复段落；无过期数字。
- 产出：`scripts/patch_manuscript_v05.py`、附录 Table C1（模型参数）

### 阶段 4：参考文献 APA 化（0.5 天）

- 24 条全部转 APA 7：`Author, A. A., & Author, B. B. (year). Title. Journal, vol(issue), pages. https://doi.org/...`
- 44 处正文引用改为 `(Healy & Palepu, 2001)` / `Healy and Palepu (2001)`。
- 逐条核对 DOI 与卷期页（原 [22]/[24] 曾补全过一次）。
- **完成标准**：`tests/test_references_apa.py` 通过；正文无方括号数字；参考文献表无混排。
- 产出：`src/reporting/references_apa.py`、改写后的 References 节

### 阶段 5：图表（0.5 天）

| 图 | 内容 | 来源 |
| --- | --- | --- |
| Fig 1 | 研究流程（数据 → 特征 → 三种打分 → 外部结局） | 新绘（示意图） |
| Fig 2 | 四路打分分布（按年） | `score_distribution_*.png` |
| Fig 3 | 分数与 Beneish 的 Spearman ρ（2021–2025 逐年） | `model_metrics.csv` |
| Fig 4 | Beneish 年度阈值漂移与富集度 | `descriptives` + `topk_metrics.csv` |
| Fig 5 | SHAP 组贡献 66.2% / 33.8% | `shap_group_contributions.csv` |

- **完成标准**：5 张图全部由脚本生成；正文每图有 2–3 句解读；图表编号连续。
- 产出：`outputs/figures/*.png`、正文图注

### 阶段 6：交付、验证与收口（0.5 天）

- `build_section5.py` → `patch_manuscript_v05.py` → pdf 导出 → 中文稿 → 两个 Excel。
- 全量测试 + 新增测试；报告写入 `tests/reports/2026-11-26-*.report-1.md`。
- `run_16_verify_manuscript.py` 校验数字一致性（文档内数字 vs `outputs/tables/`）。
- 更新 `README.md`、`CHANGELOG.md`、`docs/feature_dictionary.md`、`docs/handoff_for_ai.md`。
- 页数收口（D6）：行距、图尺寸、表字号。
- **完成标准**：docx/pdf/CN/xlsx 四类交付物齐备且数字一致；页数符合课程要求；测试全绿。
- 产出：`Group12A2_Final_EN_v0.4.docx` + `.pdf`、`Group12A2_Final_CN.docx`、两个 `.xlsx`

---

## 6. 测试策略

| 层级 | 内容 |
| --- | --- |
| 单元 | 年份边界（2019–2025 解析、2026 拒绝）、APA 格式化、引用映射完整性 |
| 集成 | `run_03`→`run_06` 在新年份区间产出行数与年份分布正确 |
| 回归 | 172 项旧测试；`run_16` 文档数字与表格一致性 |
| 边界 | 2025 年缺失文本、当年新上市（无基期）、零收入/零资产除法 |
| 报告 | `tests/reports/<YYYY-MM-DD-HH-mm>.report-<n>.md`，含通过/失败计数与失败原因 |

---

## 7. 风险与限制

| 风险 | 影响 | 缓解 |
| --- | --- | --- |
| 违规标签删失（2025/2026） | Table 5.2 违规列无法覆盖 2024–2025 | D2 + 脚注 + 附录数据可得性表；主动披露 |
| 2025 PDF 缺失（北交所 920 段等） | 2025 样本略小 | 覆盖率门槛 97%；缺失按不完整案例剔除 |
| 2025 特征完整率不足 | 面板不齐 | 阶段 0 闸门，不达标则退为附录扩展 |
| 文本仍无增量 | 教授可能追问「那为什么还要文本」 | 照实报告，并把结论写成方法学发现（词典级文本在中文 MD&A 上信息量有限） |
| 页数压不下来 | 超出课程页数要求 | 阶段 6 统一收口；必要时附录独立成文件 |
| CSMAR 2025 数据后续被修订 | 数字与提交版不一致 | 记录下载日期与文件哈希；提交版冻结 |

---

## 8. 文件清单

### 新增

- `.github/plans/2026-11-26-professor-revision.md`（本文档）
- `scripts/run_07d_holdout_year.py`
- `scripts/patch_manuscript_v05.py`
- `src/reporting/references_apa.py`
- `tests/test_year_window.py`
- `tests/test_references_apa.py`
- `outputs/reports/phase0_2025_coverage.md`
- `outputs/manuscript/Group12A2_Final_EN_v0.4.docx` + `.pdf`

### 修改

- `src/config.py`（`SAMPLE_YEARS = (2021, …, 2025)`、`FIN_YEARS`）
- `src/data_ingestion/csmar_parser.py`（年份上限）
- `src/sample_frame.py`（年份参数化）
- `scripts/run_02_download_annual_reports.py`（`--year` choices）
- `scripts/run_99_full_pipeline.py`（`--years` 默认值）
- `scripts/build_section5.py`、`scripts/build_report_figures.py`、`scripts/build_results_excel.py`、`scripts/run_13_build_chinese_docx.py`
- `README.md`、`CHANGELOG.md`、`docs/feature_dictionary.md`、`docs/handoff_for_ai.md`、`docs/reproducibility_guide.md`

### 删除

- 无（`patch_manuscript_v03/v04.py` 保留作历史补丁）

---

## 9. 时间线

| 日 | 内容 |
| --- | --- |
| D1 上午 | 阶段 0 闸门 |
| D1 下午 – D2 上午 | 阶段 1（无人值守，同时推进阶段 3 的结构改写） |
| D2 | 阶段 2 重跑 |
| D3 | 阶段 3 + 阶段 4 |
| D4 | 阶段 5 + 阶段 6 |
| 缓冲 | 3–4 天，留给定稿与展示准备 |

---

## 10. 已确认的范围（2026-11-26）

| 事项 | 结论 |
| --- | --- |
| 样本窗口 | 2021–2025（用户确认「能拉的都拉」，2025 文本一并补齐） |
| 中文稿 | 英文正文的中文翻译件，数字、图表标题、参考文献同步；不改论证 |
| 修订说明 | 不产出 response letter；论文内也不出现任何「本次修改 / 回应意见」类语句 |
| 演示稿 | 本次不做，如有需要由用户另行提出 |
| 页数 | 内容优先，阶段 6 统一收口 |
| 违规结局 | 限制在 FY2021–2023，正文脚注 + 附录可得性表说明
