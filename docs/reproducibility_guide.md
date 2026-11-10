# 复现指南（Reproduction Guide）

> 目标：让评审者/组员在干净环境里从零重跑整条管线，得到与论文报告一致的数字。
> 约定：所有命令在项目根目录 `D:\UM study life\session 1\Intro Fintec\Final\DSW` 执行。

## 0. 环境

- Python 3.12（项目开发用 3.12.14；3.11+ 均可）
- 依赖安装：`python -m venv .venv --system-site-packages`（或普通 venv）后
  `& ".venv\Scripts\python.exe" -m pip install -r requirements.txt`
- 验证：`& ".venv\Scripts\python.exe" -m pytest -q` 应全部通过（当前 39 个）

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

```powershell
& ".venv\Scripts\python.exe" "scripts\run_05_extract_mda_features.py" --year 2021
& ".venv\Scripts\python.exe" "scripts\run_05_extract_mda_features.py" --year 2022
& ".venv\Scripts\python.exe" "scripts\run_05_extract_mda_features.py" --year 2023
```

输出 `data/interim/text_features_{year}.csv`。扫描件（`no_mda`）与过短切片在
`feature_table.text_quality` 中标记为 `suspicious`，按论文的处理规则报告。

提取是**增量的**：同一命令可随时重跑，已处理文件自动跳过；每 25 个文件断点
写盘一次，中断后重启即续跑。北交所旧码补下的 PDF 只需在首遍结束后把同一
`--year` 命令再跑一遍即可补齐，无需手工清单。

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
- `topk_metrics.csv`（k=5%/10%/15% 事件率与 enrichment）
- `ranking_overlap.csv`（IF 与 AE 排序重叠，RQ3）
- `shap_global.csv`、`shap_group_contributions.csv`（RQ2）、`shap_local_top1.csv`
- `outputs/reports/autoencoder_config.json`（AE 完整超参存档）

## 4. 可复现性关键点

- 全部随机组件固定 `SEED=42`（Isolation Forest、autoencoder、SHAP 子采样）
- 超参数集中在 `src/config.py`；每步产物都是 CSV，可逐层核对
- 下载与提取均可断点续跑（已存在文件跳过、日志增量）
- 评估基准（Beneish M-Score）只出现在评估阶段，绝不进入训练输入

## 5. 已知近似与边界（论文中如实报告）

- 词典命中为原文子串计数（重叠词双计）；词典为引导版，定稿前需确认
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
- **中文终稿 Word**：`scripts/run_13_build_chinese_docx.py` 把 `docs/manuscript_chinese_draft.md` 转成 `outputs/manuscript/Group12A2_Final_CN.docx`（宋体正文/黑体标题/1.5 倍行距）。
- **英文终稿 Word**：`outputs/manuscript/Group12A2_Final_EN.docx`，由 `scripts/archive/insert_section5_results.js` 通过 Univer 工具把真实 §5 数字写入 `PaperDraft` 后导出（§1–§6 + 24 条参考文献 + 摘要结果句）。

论文正文的数字全部来自第 1–6 节的管线输出，不写死任何无法由脚本复现的常量。
