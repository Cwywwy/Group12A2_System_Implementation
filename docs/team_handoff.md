# 组员分工与交接说明（Group12A2）

> 状态：v0.3 交接清单（2026-11-11 晚更新，含 §5.6 与 §5.7）。分工为建议默认值，组内可自行调整；调整后请同步更新本文件。
> 本文面向组员，简体中文。

## 一、当前状态（2026-11-11 晚）

- 数据管线全部完成：巨潮年报 PDF 下载终审 ok=10,051 / missing=121（覆盖 98.8%，missing 为北交所挂牌前年份等数据边界）；MD&A 文本特征三路提取全部完成；CSMAR 三表（2020–2023）到位并跑出 finance_intermediate 20,103 行。
- 真实实验完成：有效样本 n=8,140（3,265 家公司，2021–2023）；财务单独模型与 Beneish M-Score 弱但显著正相关（ρ=0.136、legacy 前 10% 富集 1.22，样本校准口径 1.87），文本特征未带来增量（融合 ρ=0.103、校准富集 1.84），自编码器未复现（ρ=0.009、p=0.409）。文本词典已换为姚加权等（2021）正式版（每千词元命中 111.3 个情感词，为旧引导版的 8.3 倍），阴性结论不变。
- **新增第二版对比（§5.6）**：Table 5.4 用 10 行逐项对比第一版（引导词典 + 子串计数 + M>−1.78）与第二版（全量词典 + 词元匹配 + 双基准），证明"改进的是阴性结论的可信度"。第一版代码与数据全部保留（`git tag v0.1-baseline`、`outputs/.tmp/v01_dual_benchmark/`）。
- **新增真实事件外部检验（§5.7）**：从 CSMAR `FIN_Audit.xlsx` 与 `STK_Violation_Main.xlsx` 构造四个 0/1 标签（非标审计意见 188 条 = 2.31%、宽口径 327 = 4.02%、t+1 违规 1,757 = 21.58%、t+1 披露类违规 1,196 = 14.69%）。财务单独排序对非标意见 AUC **0.640**、前 10% 队列富集 **2.18 倍**；Beneish 代理对同一结果 AUC 仅 **0.405**（低于随机）；分组交叉验证中文本块带来 +0.007~+0.026 的 AUC 增量（5/8 组合区间不含 0）。论文表述必须是"文本单独更差、但融合有小而一致的互补增量"。
- 论文终稿已交付：英文 `outputs/manuscript/Group12A2_Final_EN.docx`（109 段、6 张表、24 条参考文献、15 页）+ 中文 `outputs/manuscript/Group12A2_Final_CN.docx`（73 段、6 张表、9 页），均有对应 PDF。
- 全部单测 114/114 通过；复现指南见 `docs/reproducibility_guide.md`。

## 二、建议分工

| 成员 | 学号 | 主要负责 |
| --- | --- | --- |
| 汪进宇 Jinyu Wang | MC644879 | 数据：CSMAR 三表下载与放入 `data/raw/csmar/`、数据说明归档 |
| 陈文远 Wenyuan Chen | MC644700 | 特征与模型：feature_table 校验、QC 复核、模型参数确认 |
| 吴明轩 Mingxuan Wu | MC637835 | 实验与图表：run_07 出数字、图件检查、实验章节填数 |
| Kolawole Sunday O. | MC650023 | 成文与演示：章节合并进 Word、slides 定稿、演示排练 |

## 三、剩余待办

1. **终稿 PDF 覆盖**：`outputs/manuscript/*.pdf` 被 Acrobat/WPS 占用，新 PDF（英文 15 页 / 中文 9 页）已生成在 `outputs/.tmp/`，关闭阅读器后覆盖即可。
2. **演示幻灯片**：`scripts/build_slides.py` 已生成 12 页 `outputs/slides/Group12A2_Deck.pptx`（数字同源），但版式日期与 §5.7 两表尚未加进 deck；若要更新，先改 `build_slides.py` 再加两页或替换 RQ1 页表格，然后重跑脚本 + `univer_print_pdf`。
3. **可选**：若想进一步做阳性结果，最省力的是问询函（深交所接口干净、约 4.5–5 人日，见 `outputs/reports/branch2_inquiry_crawler_spec.md`），但会改变论文定位，需先与教授确认。

> 参考文献 [22]/[24] 的精确出处已于 2026-11-10 查证补全（见 CHANGELOG），无需组员再核对。

## 四、一键命令速查

```text
.venv\Scripts\python.exe -m pytest -q                                  # 全部单测（114/114）
.venv\Scripts\python.exe scripts\run_03_build_finance_intermediate.py  # 三表→金融中间表
.venv\Scripts\python.exe scripts\run_03b_build_event_table.py          # 事件表→event_table.csv
.venv\Scripts\python.exe scripts\run_07b_event_models.py --boot 400    # 事件外部检验（§5.7）
.venv\Scripts\python.exe scripts\build_section5.py --markdown --markdown-cn --docx --docx-cn  # 重建 §5 与终稿
.venv\Scripts\python.exe scripts\run_06_build_feature_table.py         # 特征表
.venv\Scripts\python.exe scripts\run_07_experiment.py                  # 建模+图表+摘要
.venv\Scripts\python.exe scripts\run_12_narrate_results.py             # 结果英文叙事
.venv\Scripts\python.exe scripts\run_13_build_chinese_docx.py          # 中文稿→Word
.venv\Scripts\python.exe scripts\run_99_full_pipeline.py               # 一键全流程
```

## 五、注意

- 提交时间：11-24 实验章节 4 页、12-15 终稿 + 晚 7 点演示（11-10 实现章节已交）。
- Individual Essay（12-20，3000 词）由每人自己写；教授明确警告不要用 ChatGPT。
- 版权：CSMAR 与巨潮数据仅限本课程作业使用，演示附录保留版权声明页。
- 论文诚实结论（勿改成"发现欺诈"）：模型输出仅用于审查优先级排序，文本特征未带来增量、自编码器未复现，如实报告即可。
