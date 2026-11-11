# 复现指南（Reproduction Guide）

> 目标：让评审者/组员在干净环境里从零重跑整条管线，得到与论文报告一致的数字。
> 约定：所有命令在项目根目录 `D:\UM study life\session 1\Intro Fintec\Final\DSW` 执行。

## 0. 环境

- Python 3.12（项目开发用 3.12.14；3.11+ 均可）
- 依赖安装：`python -m venv .venv --system-site-packages`（或普通 venv）后
  `& ".venv\Scripts\python.exe" -m pip install -r requirements.txt`
- 验证：`& ".venv\Scripts\python.exe" -m pytest -q` 应全部通过（当前 77 个）

## 1. 数据准备

### 1.1 CSMAR 三表（组员手动下载，一次性）

按 `docs/csmar_download_guide.md` 下载 2020–2023 合并口径三表，把 xlsx 放入：

- `data/raw/csmar/FS_Combas.xlsx`（资产负债表）
- `data/raw/csmar/FS_Comins.xlsx`（利润表）
- `data/raw/csmar/FS_Comscfd.xlsx`（现金流量表）

生成中间表：

```powershell
& ".venv\Scripts\python.exe" -m src.data_ingestion.csmar_parser  # 待定，或调用脚本
```

输出 `data/interim/finance_intermediate.csv`（17 列标准模式），并打印 missing_field_report。

### 1.2 巨潮年报 PDF（脚本批量下载）

1. `scripts/run_01_sample.py` — 由 CSMAR 公司信息表生成样本框与下载清单
   （输出 `data/processed/manufacturing_sample_frame.csv`、`download_checklist.csv`）
2. 三路并行下载（每路约 1–1.5 小时，断点续传，可随时 Ctrl+C 重跑）：

```powershell
& ".venv\Scripts\python.exe" "scripts\run_02_download_annual_reports.py" --year 2021
& ".venv\Scripts\python.exe" "scripts\run_02_download_annual_reports.py" --year 2022
& ".venv\Scripts\python.exe" "scripts\run_02_download_annual_reports.py" --year 2023
```

3. `scripts/run_04_audit_downloads.py` — 审计缺失/过小/标题年份错位，输出
   `data/processed/download_audit.csv`；对 `missing`/`mismatched_year` 行重跑对应下载。

### 1.3 MD&A 文本特征提取

推荐（并行重算，v0.2 词典 + 词元匹配 + MD&A 原文缓存）：

```powershell
& ".venv\Scripts\python.exe" "scripts\run_05b_recompute_text_features.py" --workers 8
```

输出 `data/interim/text_features_{year}.csv`（同 run_05 模式）+ `data/interim/mda_text_{year}.jsonl`
（每行 `{"symbol","mda_text"}` 缓存原文，供以后换词典时免重提取 PDF）。

增量备选（单线程，同一命令可随时重跑、已处理文件自动跳过，每 25 个文件断点写盘）：

```powershell
& ".venv\Scripts\python.exe" "scripts\run_05_extract_mda_features.py" --year 2021
& ".venv\Scripts\python.exe" "scripts\run_05_extract_mda_features.py" --year 2022
& ".venv\Scripts\python.exe" "scripts\run_05_extract_mda_features.py" --year 2023
```

扫描件（`no_mda`）与过短切片在 `feature_table.text_quality` 中标记为 `suspicious`，按论文的处理规则报告。旧 v0.1 特征表会由 run_05b 自动备份到 `data/interim/v0.1_text_features_backup/`。

### 1.4 词典密度对照（可选，用于回应"词表是否太薄"）

```powershell
& ".venv\Scripts\python.exe" "scripts/run_05c_lexicon_density.py" --year 2021 --sample 200
```

输出 `outputs/tables/lexicon_density.csv`：在同一份 MD&A token 流上分别用 v0.1（引导版，位于
`data/external/dictionaries/v0.1_bootstrap_backup/`）与 v0.2（`data/external/dictionaries/`）词表计数，
给出每 1,000 词元的命中期密度与倍数。论文引用值：情感词 13.41 → 111.30（8.30×），
不确定词 2.14 → 5.66（2.64×）。

## 2. 特征表

```powershell
& ".venv\Scripts\python.exe" "scripts\run_06_build_feature_table.py"
```

输出 `data/processed/feature_table.csv`（样本框 + 6 金融特征 + M-Score + 3 文本特征 + 质量标记）。

## 3. 建模与评估

```powershell
& ".venv\Scripts\python.exe" "src/pipeline.py" "data\processed\feature_table.csv" "--output-dir" "outputs"
```

输出到 `outputs/tables/`：

- `anomaly_scores.csv`（四路排名分 + M-Score 基准标记）
- `model_metrics.csv`（Spearman 相关）
- `topk_metrics.csv`（双基准 legacy/calibrated × 4 模型 × k=5%/10%/15%，共 24 行）
- `ranking_overlap.csv`（IF 与 AE 排序重叠，RQ3）
- `shap_global.csv`、`shap_group_contributions.csv`（RQ2）、`shap_local_top1.csv`
- `lexicon_density.csv`（v0.1/v0.2 词表在同一 token 流上的命中密度，由 run_05c 生成）
- `outputs/reports/autoencoder_config.json`（AE 完整超参存档）

改动做法（换词典、换基准等）后需要对比两版结果时：

```powershell
& ".venv\Scripts\python.exe" "scripts/compare_runs.py" `
  --old "outputs/.tmp/v01_dual_benchmark/tables" --new "outputs/tables" `
  --label-old "v0.1 lexicon" --label-new "v0.2 lexicon"
```

输出两版的样本量、ρ 与 p、两个基准下的 top-5/10/15% 富集率变化、SHAP 组份额、
前 10% 名单重叠与第一名公司；`--old` 目录可指向无 `benchmark` 列的旧版 12 行表。

### 3.1 结果变量分支评估（探索性，不入论文主表）

如果想把基准从 M-Score 换成真实监管事件，先看 `outputs/reports/positive_result_branches.md`
（7 个分支的数据来源、成本、阳性概率、风险与推荐路线）。其中"零新增数据"的分支已用脚本实测：

```powershell
& ".venv\Scripts\python.exe" "scripts/analyze_branch_beneish_components.py"
```

输出 `outputs/tables/branch_component_correlations.csv`（4 个排序 × 9 个目标 = 36 行），
把 M-Score 拆成 DSRI/GMI/AQI/SGI/DEPI/SGAI/LVGI/TATA 八个分量分别求 Spearman ρ。
结论：文本单独对任一分量的 |ρ| ≤ 0.064，说明"基准太粗"不是文本无信号的原因；
这条分支只作为论文中"已排除度量层面解释"的补充证据，不改变主结果。

### 3.2 真实监管事件外部检验（论文 §5.7、表 5.5 与表 5.6）

数据来源为 CSMAR 两张事件表，放在 `data/raw/csmar_events/`（不入库）：

| 文件 | 内容 | 用途 |
| --- | --- | --- |
| `FIN_Audit.xlsx` | 审计意见（`Accper` 会计期间、`Audittyp` 意见类型） | 非标审计意见标签（窄口径：保留/无法表示/否定；宽口径另含带强调事项段） |
| `STK_Violation_Main.xlsx` | 违规处理（`DeclareDate` 公告日、`ViolationType`/`ViolationTypeID` 类型） | 违规标签，按公告年 t+1 对齐到年报年 t；`DISCLOSURE_CODES` P2501–P2506 为披露类 |

两张表都是 CSMAR 的「英文代码行 + 中文标签行 + 单位行 + 数据行」格式，解析器会丢弃前两行并按 `zfill(6)` 还原证券代码。

```powershell
# 1) 解析事件表并对齐到分析样本（8,140 个公司—年度）
& ".venv\Scripts\python.exe" "scripts\run_03b_build_event_table.py"

# 2) 无监督排序 + 有监督交叉验证（--boot 控制 bootstrap 次数，默认 1000，报告用 400 即可）
& ".venv\Scripts\python.exe" "scripts\run_07b_event_models.py" --boot 400
```

产物：`data/processed/event_table.csv`（键 `symbol` + `fiscal_year`，含四个 0/1 标签与 `opinion_class`）、`data/processed/event_table.json`（覆盖率与事件率）、`outputs/tables/event_ranking_metrics.csv`（每个 label×分数：AUC 与 bootstrap 区间、PR-AUC、top-5/10/15% 富集率与召回）、`outputs/tables/event_supervised_metrics.csv`（按 `symbol` 分组的 5 折 OOF AUC，含 `delta_fused_vs_finance` 与 `delta_text_vs_finance` 两行）、`outputs/reports/event_branch_results.md`（表 5.5 与表 5.6 的文字版）。

要点：①分组交叉验证用 `StratifiedGroupKFold(groups=symbol)`，避免同一公司跨折泄漏；②`delta_text_vs_finance` 全为负，`delta_fused_vs_finance` 全为正但很小，论文只能写"融合有小而一致的增量"；③审计意见与年报同期，属识别而非预测，只有 t+1 违规是严格前瞻；④Beneish 代理对非标意见的 AUC 为 0.405（低于随机），是本论文最值得强调的反差。

## 4. 可复现性关键点

- 全部随机组件固定 `SEED=42`（Isolation Forest、autoencoder、SHAP 子采样）
- 超参数集中在 `src/config.py`；每步产物都是 CSV，可逐层核对
- 下载与提取均可断点续跑（已存在文件跳过、日志增量）
- 评估基准（Beneish M-Score）只出现在评估阶段，绝不进入训练输入

## 5. 已知近似与边界（论文中如实报告）

- 词典命中为 jieba 词元精确匹配（词典 v0.2：姚加权等 (2021) 正式文本词表 3,585 正 / 1,633 负 + 扩充不确定性词表）；子串计数仅存在于 v0.1 引导版（已归档备份）
- 文本特征只覆盖有文本层且能找到 MD&A 章节标题的年报；扫描件标记后按规则处理。不可读或结构损坏的 PDF 写为 `pdf_error` QC 行，不中断批量任务
- 组内标准化稀疏组（<20 条）退回全样本均值/方差
- SHAP 计算对 >2000 行做固定种子子采样
- 巨潮接口为公开检索接口（非官方 API），下载限速由脚本 `REQUEST_PAUSE_SECONDS` 控制

## 6. 一键流程（可选）

数据齐备后可用编排脚本按序执行全部阶段（含三路 MD&A 提取）：

```powershell
.venv\Scripts\python.exe scripts\run_99_full_pipeline.py
# 或跳过耗时的提取阶段：
.venv\Scripts\python.exe scripts\run_99_full_pipeline.py --skip-05
# 只跑某几个阶段：
.venv\Scripts\python.exe scripts\run_99_full_pipeline.py --stage 06_features 11_descriptives
```

每阶段退出码 2 表示前置数据未就绪（跳过并记录），非 0/2 视为失败；
执行记录写在 `outputs/reports/pipeline_runbook.md`。

## 7. 论文成文产物

实验结果与论文正文由以下脚本/产物承接，最终 Word 都在 `outputs/manuscript/`：

- **英文结果段落**：`scripts/run_12_narrate_results.py` 读 `outputs/tables/` 生成 `outputs/reports/results_narrative.md`（RQ1–RQ3 自动填数）。
- **§5 重写与表格排版**：`scripts/build_section5.py` 读 `outputs/tables/*.csv` 与 `data/processed/feature_table.csv`，同时生成三份产物——英文 §5 markdown（`docs/manuscript_experiment_section.md`）、中文 §5 markdown（`docs/manuscript_chinese_experiment_section.md`）、以及把 Table 5.1–5.3 直接排进正文的 Word 终稿（`--docx` 改英文、`--docx-cn` 改中文）。所有数字与表格都由 CSV 现算，重跑 `run_07` 后一条命令即可刷新；脚本按固定的段落槽位（英文母版 91 段 / 中文母版 56 段）定位，若 Word 段落结构改变需同步 `SLOT_*` / `CN_SLOT_*` 常量。
  改表格前先确认母版干净：`outputs/manuscript/source/` 存着**不含表格**的英文/中文母版，脚本默认从母版读、往 `outputs/manuscript/` 写。直接把已插表的交付件当输入会重复插表并把段落槽位冲掉。
- **中文终稿 Word**：`scripts/run_13_build_chinese_docx.py` 把 `docs/manuscript_chinese_draft.md` 转成 `outputs/manuscript/Group12A2_Final_CN.docx`（宋体正文/黑体标题/1.5 倍行距）。
- **英文终稿 Word**：`outputs/manuscript/Group12A2_Final_EN.docx`，由 `scripts/archive/insert_section5_results.js` 通过 Univer 工具把真实 §5 数字写入 `PaperDraft` 后导出（§1–§6 + 24 条参考文献 + 摘要结果句），再由 `build_section5.py` 刷新 §5 与三张表。
- **§5.6 第一版与第二版对比**：同一脚本生成 `5.6 From the First to the Second Specification` / `5.6 从第一版到第二版`，含 Table 5.4（10×3 设定对比）与两段说明；数字来自 `outputs/.tmp/v01_dual_benchmark/tables/`（冻结的第一版结果表）与 `outputs/tables/lexicon_density.csv`，缺文件时自动降级为定性表述。
- **§5.7 真实监管结果外部检验**：同一脚本生成 `5.7 External Validation Against Real Regulatory Outcomes` / `5.7 面向真实监管结果的外部检验`，含 Table 5.5（5×5：四个排序 + Beneish 代理对非标意见与 t+1 违规的 AUC 与前 10% 富集）与 Table 5.6（7×6：分组交叉验证 AUC 与 ΔAUC）；数字来自 3.2 节两个事件脚本，缺表时整节自动省略。重建后英文终稿 109 段 6 表（15 页）、中文终稿 73 段 6 表（9 页）。
- **行距收敛**：正文原本 1.5 倍行距，加入 §5.7 后英文稿一度 16 页（超出 12–15 页要求），脚本用 `BODY_LINE_SPACING = 1.45` 与 `_fit_body_spacing()` 把正文压到 15 页；只调整原本 1.5 倍的正文段落，标题、表格与脚注不动。若后续再增内容，优先压缩这段函数而不是删正文。
- **两版过程的版本控制**：`git tag v0.1-baseline`（提交 `542395b`）保存第一版代码——小规模引导词典、子串计数、仅 M > −1.78 基准；`git tag v0.2-calibrated`（提交 `b700d27`）保存第二版。第一版的数据与结果另有文件级备份：`data/external/dictionaries/v0.1_bootstrap_backup/`、`data/interim/v0.1_text_features_backup/`、`data/processed/v0.1_feature_table.csv`、`outputs/.tmp/v01_prev_run/`、`outputs/.tmp/v01_dual_benchmark/`。用 `git worktree add ../v01 v0.1-baseline` 可把第一版完整检出重跑。
- **PDF**：本机无 LibreOffice，PDF 由 Univer 导入 docx 后打印（`univer_import` → `univer_print_pdf`），终稿英文 12–15 页（满足 Option 2 页数要求）。注意 `outputs/manuscript/*.pdf` 常被 Acrobat/WPS 占用，打印时先落到 `outputs/.tmp/`，关闭阅读器后再跑 `scripts/run_14_publish_pdfs.py` 覆盖（脚本会逐个报告仍被锁定的目标，退出码 2）。
- **演示幻灯片**：`scripts/build_slides.py` 读 `outputs/tables/` 生成 12 页 16:9 演示稿 `outputs/slides/Group12A2_Deck.pptx`（版式规范见 `docs/slides_deck_spec.md`），并与 §5 共用同一套数字（`build_section5.collect_numbers()`），所以正文与幻灯片不会出现两套数。重跑 `run_07` 后再跑一次脚本即可刷新；PDF 版同名输出在 `outputs/slides/Group12A2_Deck.pdf`。

论文正文的数字全部来自第 1–6 节的管线输出，不写死任何无法由脚本复现的常量。
