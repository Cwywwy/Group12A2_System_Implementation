# 计划：修复财务中间表合并缺陷并重跑管线

- 状态：**已完成（含第二轮）**（2026-11-23 02:49）
- 触发：核对报告指出 `finance_intermediate.csv` 三表按行号合并，73.4% 的年份资产负债表滞后一年；用户 2026-11-23 01:06 批复"同意修正，重新跑结果"。

## 目标与范围

修复 `src/data_ingestion/csmar_parser.py` 与 `scripts/run_03_build_finance_intermediate.py` 的合并逻辑，从 `run_03` 起重跑整条管线，把修正后的数字写进英文报告、中文报告、§5 源文本、图件与结果工作簿。不重下 PDF、不改数据源、不改模型设定。

## 模块划分

| 模块 | 职责 | 交互 | 状态 |
| --- | --- | --- | --- |
| `src/data_ingestion/csmar_parser.py` | 解析 CSMAR 日期为 `period_end`，只保留年报行，按键合并三表 | 产出中间表 | 修改 |
| `scripts/run_03_build_finance_intermediate.py` | 调用上述逻辑生成 `data/interim/finance_intermediate.csv` | 下游 `run_06` | 修改 |
| `src/features/*`、`src/models/*` | 特征与模型，未改 | 读中间表 | 不变 |
| `scripts/build_section5.py` | §5 叙述与表格生成，中英文 | 读 `outputs/tables/` | 修改（叙述与表头） |
| `scripts/build_report_figures.py` | 六张英文图 | 读 `outputs/tables/` | 新增 |
| `scripts/build_results_excel.py` | 中英结果工作簿 | 读 `outputs/tables/` | 不变（仅重跑） |
| 文档：`docs/manuscript_experiment_section.md`、`CHANGELOG.md`、核对报告 | 同步数字与说明 | — | 修改 |

## 阶段与完成标准

| 阶段 | 内容 | 完成标准 | 状态 |
| --- | --- | --- | --- |
| 1 | 备份 `finance_intermediate.csv`、`feature_table.csv`、`outputs/tables`、`outputs/reports` 到 `outputs/.tmp/backup_pre_rerun/` | 可回滚 | 完成 |
| 2 | 改解析与合并（12-31 过滤 + 键对齐） | `pytest tests/test_csmar_parser.py tests/test_finance_preflight.py` 通过 | 完成（7 passed） |
| 3 | 重跑 `run_03 → 06 → 07 → 07b → 11 → 12` | 中间表 19,966 行、完整样本 8,000、无重复键 | 完成 |
| 4 | 重写 §5 中英文叙述与表头 | 生成 markdown 无占位符、与表格一致 | 完成 |
| 5 | 重绘六图并替换进组员 docx | 131 段 / 6 表 / 6 图，旧数字零命中 | 完成 |
| 6 | 中文版重生成、工作簿重生成、测试与文档 | 126/126 通过；CHANGELOG 与核对报告更新 | 完成 |

## 预期产出（实际）

`11.23base/Group12A2_Final_EN_corrected.docx`、`outputs/manuscript/Group12A2_Final_CN.docx`、`docs/manuscript_experiment_section.md`、`docs/manuscript_chinese_experiment_section.md`、`outputs/figures/manuscript/figure_5_1…5_6.png`、`outputs/Group12A2_Results_Summary{,_EN}.xlsx`、`tests/reports/2026-11-23-01-47.report-1.md`。

## 测试策略

全量 `pytest`；对新数字做抽样对读（表 5.1–5.6 对 `outputs/tables/*.csv`）；docx 做旧数字字符串扫描与图件目视核对。

## 风险与限制

- 组员的 6 张图是旧结果的渲染，已用同结构新图替换；若他们另有 PPT/插图版本，需重新导出。
- 第一版（v0.1）结果建立在错表上，表 5.4 的对比已注明"融合相关由正转负部分反映数据修正"。
- 结论方向变化较大（财务–Beneish 相关由 +0.136 变 −0.048），摘要、§4.6、§5.5、§5.8 与幻灯片需同步；本次已改正文，幻灯片未改。

## 第二轮追加（2026-11-23 02:00–02:49）：列取错

修好行对齐后逐值审计发现收入仍有 418 行不一致，追查为列选择错误：`revenue` 命中第 6 列“营业总收入”（B001100000）而非第 7 列“营业收入”（B001101000），`cogs` 命中第 23 列“营业总成本”而非第 24 列“营业成本”，`depreciation` 的 `C002003000` 实为“处置长期资产收回的现金净额”（直接法现金流量表无折旧行）。

| 阶段 | 内容 | 完成标准 | 状态 |
| --- | --- | --- | --- |
| 7 | 备份到 `outputs/.tmp/backup_pre_fix2/`；改 `CODE_ALIASES` 与 `probe_field_columns()`；DEPI 中性化 | `pytest tests/test_csmar_parser.py` 通过 | 完成 |
| 8 | 重跑 `run_03 → 06 → 03b → 07 → 07b → 11 → 12`（事件表此前停在 8,000，一并重跑） | 中间表 19,966 行、样本 9,239 / 3,488、事件表 9,239 行 | 完成 |
| 9 | 再次改写 §5 中英文：新增 `_corr_clause()`、`_mscore_components()`，§5.7 解释 Beneish 方向为负 | 生成文本无旧数字，表 5.4/5.6 口径收紧 | 完成 |
| 10 | 刷新英文 docx（段落 + 表格 + 六图）、中英工作簿、核对报告、CHANGELOG、测试 | 131 段 / 6 表 / 6 图；126/126 通过 | 完成 |
| 11 | 新增 `scripts/run_02b_audit_data.py` 数据审计 | 审计报告落 `outputs/reports/data_audit_2026-11-23.md` | 完成（见审计报告） |
