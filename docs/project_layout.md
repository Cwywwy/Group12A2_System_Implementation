# 项目文件地图（Project Layout）

> 最后更新：2026-11-11 晚（目录整理后）。
> 目的：一眼看清「数据源 → 第一版 → 第二版 → 各分支 → 定稿」分别在哪，哪些是临时文件。

## 一、五层结构速查

| 层 | 位置 | 内容 | 是否入库 |
| --- | --- | --- | --- |
| ① 数据源 | `data/raw/`、`data/external/` | 巨潮年报 PDF（41 GB）、CSMAR 三表、CSMAR 事件表、上市公司名单、情感词典 | 否（`data/` 被 gitignore） |
| ② 第一版（v0.1 基线） | `data/archive_v0.1/`、`outputs/archive_v0.1/` | 引导版词典、旧文本特征、旧特征表、旧结果表、旧一轮图表 | 部分 |
| ③ 第二版（v0.2，当前） | `data/interim/`、`data/processed/`、`outputs/tables|figures|reports/` | 全量词典文本特征、当前特征表与事件表、当前全部结果 | 是 |
| ④ 各分支 | `outputs/branches/` | 换结果变量的可行性调研、Beneish 分量探针、问询函爬虫规格、真实事件检验报告 | 是 |
| ⑤ 定稿 | `outputs/manuscript/`、`outputs/slides/` | 中英文终稿 docx/PDF、系统实现报告、12 页演示稿 | 是 |

## 二、定稿文件（提交用）

`outputs/manuscript/`：

| 文件 | 说明 |
| --- | --- |
| `Group12A2_Final_EN.docx` / `.pdf` | **英文终稿**：109 段 + 6 张表 + 24 条参考文献，打印 15 页（要求 12–15 页） |
| `Group12A2_Final_CN.docx` / `.pdf` | **中文终稿**：73 段 + 6 张表，打印 9 页 |
| `Group12A2_System_Implementation_EN/CN.docx` / `.pdf` | 系统实现报告（附录） |
| `source/Group12A2_Final_EN.docx`、`source/Group12A2_Final_CN.docx` | **母版**（不含表格），`build_section5.py` 从母版读、往上一级写 |

`outputs/slides/`：`Group12A2_Deck.pptx` / `.pdf`（12 页，由 `scripts/build_slides.py` 生成，数字与正文同源）。

> 提交前确认以 `outputs/manuscript/` 为准，不要用根目录的历史副本（已移入 `_trash/`）。

## 三、第一版（v0.1）归档

第一版 = 引导版小词典 + 子串计数 + 单一 `M > −1.78` 基准。代码在 `git tag v0.1-baseline`（提交 `542395b`）。

| 位置 | 内容 |
| --- | --- |
| `data/archive_v0.1/dictionaries/` | v0.1 三个词表（正 38 / 负 33 / 不确定 23 词） |
| `data/archive_v0.1/text_features/` | v0.1 文本特征三份 CSV |
| `data/archive_v0.1/feature_table.csv` | v0.1 特征表（8,276 行可用） |
| `outputs/archive_v0.1/tables/` | v0.1 全套结果表（$\rho$、top-k、SHAP、重叠），供 §5.6 的 Table 5.4 读取 |
| `outputs/archive_v0.1/prev_run/` | 最早一轮的图表与摘要（无 benchmark 列），`compare_runs.py` 的默认 `--old` |

取出第一版代码重跑：`git worktree add ../DSW-v01 v0.1-baseline`。

## 四、第二版（v0.2，当前结果）

- 词典：`data/external/dictionaries/`（姚加权等 2021 正式版 3,585 正 / 1,633 负；`jieba_userdict.txt` 5,218 词）
- 中间产物：`data/interim/text_features_{2021,2022,2023}.csv`、`mda_text_{年}.jsonl`（缓存的 MD&A 原文，可复算）
- 特征表 / 事件表：`data/processed/feature_table.csv`、`event_table.csv`（+ `.json`）
- 结果：`outputs/tables/`（8 张主表 + 事件两张）、`outputs/figures/`（8 张图）、`outputs/reports/`（实验摘要、描述统计、叙事、v0.1→v0.2 差异）

## 五、各分支（`outputs/branches/`）

| 文件 | 分支 | 结论 |
| --- | --- | --- |
| `positive_result_branches.md` | 换结果变量的 7 条路线 | t+1 问询函首选、非标审计意见兜底、重述/处罚备选；含成本与风险清单 |
| `branch_component_correlations.csv` | 分支 1：Beneish 八分量探针 | 文本单独对任一分量 |ρ| ≤ 0.064 → "基准太粗"被排除 |
| `branch2_inquiry_crawler_spec.md` | 分支 2：问询函爬虫 | 深交所最干净；沪市必须靠巨潮补；4.5–5 人日；有降级方案 |
| `event_branch_results.md` | 分支 3：真实监管事件 | 已升格为论文 §5.7；表 5.5 / 表 5.6 的文字版 |

分支 3 的数据已进入主流程：`data/processed/event_table.csv`（审计意见 + 违规），代码 `src/data_ingestion/event_parser.py`、`src/evaluation/event_eval.py`。

## 六、数据源

```
data/
├─ raw/
│  ├─ cninfo/{2021,2022,2023}/*.pdf   巨潮年报原文（约 41 GB，10,052 份）
│  ├─ csmar/                           CSMAR 三表（FS_Combas/FS_Comins/FS_Comscfd）+ STK_LISTEDCOINFOANL.xlsx
│  └─ csmar_events/                    FIN_Audit.xlsx（审计意见）、STK_Violation_Main.xlsx（违规处理）
├─ external/                            姚加权 2021 词典原始文件、BSE 代码映射
├─ interim/                             中间产物（当前版本）
├─ processed/                           特征表、事件表、下载审计与 QC
└─ archive_v0.1/                        第一版数据（见第三节）
```

数据获取方式见 `docs/csmar_download_guide.md`、`docs/csmar_event_data_guide.md`、`docs/cninfo_download_guide.md`。

## 七、代码与文档

- `src/`：`config.py`（路径与超参）、`pipeline.py`、`data_ingestion/`（含 `event_parser.py`）、`features/`、`models/`、`evaluation/`（含 `event_eval.py`）、`reporting/`
- `scripts/`：`run_00`–`run_14` 分阶段入口 + `run_99` 一键流程；`build_section5.py`（论文 §5 + 表格）、`build_slides.py`（演示稿）、`compare_runs.py`、`analyze_branch_beneish_components.py`、`run_05c_lexicon_density.py`
- `scripts/archive/`：早期一次性脚本（回填占位符、插入 §4/§5 等），仅作历史参考
- `docs/`：`reproducibility_guide.md`、三份数据下载指引、`feature_dictionary.md`、论文各节 markdown、`team_handoff.md`、`manuscript_assembly_checklist.md`
- 根目录：`README.md`（简介）、`GUIDE.md`（查阅指南）、`CHANGELOG.md`（变更日志）

## 八、课程材料（`course_materials/`）

课程给的原始材料，不属于交付物，也不参与管线：`course_paper_materials.univer`（446 MB，论文原始 Univer 文档）、`grading_rubric.univer`、`Grading and Report Requirement for FinTech 2026-Modified.docx`、`Financial_Disclosure_Quality_Assessment_English_Outline(1).docx`、`Copyright notice.pdf`。

## 九、临时文件与清理

- `_trash/`：2026-11-11 整理时移出的历史文件（旧提交副本 61 段无表格、`docs/CSMAR guide.docx`、演示首页 SVG 草稿、`slides_preview/` PNG、`outputs/.tmp/` 全部版式探针），**已于当日删除**（46 MB）。如需再清一次，用下面的脚本。
- **仍被占用、暂未删除**（共约 472 MB）：`outputs/.tmp/*.univer`（18 个版式探针）与根目录 `course_paper_materials.univer`（446 MB）、`grading_rubric.univer`。它们被 DeepSeek Harness 的 Univer 服务持有句柄，`Rename` 与 `Remove` 都会报"另一个进程正在使用此文件"。**重启 DSH 后**运行：

```powershell
.venv\Scripts\python.exe scripts\run_15_cleanup_workspace.py           # 先看清单（干跑）
.venv\Scripts\python.exe scripts\run_15_cleanup_workspace.py --apply   # 再删
```

  脚本 `scripts/run_15_cleanup_workspace.py`：清理 `_trash/`、`outputs/.tmp/*.univer`、根目录课程材料重复副本（先比对 `course_materials/` 同名副本的体积）、`__pycache__` 与 `.pytest_cache`；默认干跑，加 `--apply` 才真正删除。
- `outputs/.tmp/` 是暂存区：重新生成 PDF 时脚本会往这里写中间产物，属正常临时文件，不要提交（已在 `.gitignore` 中）。
