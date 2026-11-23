# 组员分工与交接说明（Group12A2）

> 状态：v0.3 交接清单（**2026-11-24 更新**，数字口径 v0.3 / n=9,239）。分工为建议默认值，组内可自行调整；调整后请同步更新本文件。
> 本文面向组员，简体中文。

## 一、当前状态（2026-11-24）

- 数据管线全部完成：巨潮年报 PDF 下载终审 ok=10,051 / missing=121（覆盖 98.8%，missing 为北交所挂牌前年份等数据边界）；MD&A 文本特征三路提取全部完成；CSMAR 三表（2020–2023）到位并跑出 finance_intermediate 20,103 行。
- **有效样本 n=9,239**（3,488 家公司，2021–2023；流失链 10,172 → 9,414 → 9,413 → 9,239）。财务单独模型与 Beneish M-Score 微弱**反向**（ρ=−0.021、p=0.040；legacy 前 10% 富集 1.69、校准口径 2.45），文本特征几乎不相关（ρ=−0.026），自编码器未复现（ρ=−0.007、p=0.528）。
- **第二版对比（附录 B3）**：v0.1（引导词典 + 子串计数）与 v0.3（全量词典 + 词元匹配）在同一批修复后财务口径上重算 —— 融合 ρ 由 +0.103 变为 −0.018，这个符号翻转**来自数据修复而非换词典**（旧词典在修复后数据上已给出 −0.021）。
- **真实事件外部检验（正文 §5.6）**：四个 0/1 标签 —— 非标审计意见 204 条 = 2.21%、宽口径 355 = 3.84%、t+1 违规 1,965 = 21.27%、t+1 披露类违规 1,337 = 14.47%。财务单独排序对非标意见 AUC **0.802**、前 10% 队列富集 **4.95 倍**；Beneish 代理 AUC 仅 **0.242**（低于随机）。分组交叉验证：融合块相对财务块点估计 +0.002~+0.012、**8 个组合无一区间排除 0**（严格时序门下 6/8 为正、仍 0 个排除 0）；文本块单独在 16 个格子上显著更差（−0.068~−0.248）。论文表述必须是「文本单独更差、但融合有小而一致的互补增量且不可区分于零」。
- **t+1 严格时序（附录 B.3）**：要求公告日晚于当年年报披露日，标签由 1,965/1,337 降为 1,543/1,040（丢 21.5% / 22.2%），结论不弱反强（披露违规 AUC 0.596 → 0.600）。
- **交付件**：唯一在维护的是 `outputs/manuscript/Group12A2_Final_EN_v0.3.docx` + `.pdf`（15 页正文 + 7 页附录，22 页 / 137 段 / 10 表 / 8,274 词）。旧的 23 页英文稿、中文稿与 11-11 版 PDF 保留作历史对照，**不再维护**。
- 全部单测 **172/172** 通过（约 30 s）；复现指南见 `docs/reproducibility_guide.md`，修订总册见 `docs/revision/v0.3_consistency_revision.md`。

## 二、建议分工

| 成员 | 学号 | 主要负责 |
| --- | --- | --- |
| 汪进宇 Jinyu Wang | MC644879 | 数据：CSMAR 三表下载与放入 `data/raw/csmar/`、数据说明归档 |
| 陈文远 Wenyuan Chen | MC644700 | 特征与模型：feature_table 校验、QC 复核、模型参数确认 |
| 吴明轩 Mingxuan Wu | MC637835 | 实验与图表：run_07 出数字、图件检查、实验章节填数 |
| Kolawole Sunday O. | MC650023 | 成文与演示：章节合并进 Word、slides 定稿、演示排练 |

## 三、剩余待办

1. **演示幻灯片（未做）**：`outputs/slides/Group12A2_Deck.pptx` 仍是 11-11 版，结论页写着 "MD&A text features add none"，在 v0.3 语境下须限定为「对 Beneish 式无监督排序无增量」，且缺严格时序与词典对照两项。按用户决策本轮不重建。
2. **旧件不再维护**：`Group12A2_Results_Summary*.xlsx` 与旧 PDF / 中文稿仍是旧口径（8,140 / 3,265），需要就重跑 `build_results_excel.py` 与 `run_14_publish_pdfs.py`，否则不要引用。
3. **可选**：若想进一步做阳性结果，最省力的是问询函（深交所接口干净、约 4.5–5 人日，见 `outputs/branches/branch2_inquiry_crawler_spec.md`），但会改变论文定位，需先与教授确认。

> 参考文献 [22]/[24] 的精确出处已于 2026-11-10 查证补全（见 CHANGELOG），无需组员再核对。

## 四、一键命令速查

```text
.venv\Scripts\python.exe -m pytest -q                                  # 全部单测（172/172）
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
