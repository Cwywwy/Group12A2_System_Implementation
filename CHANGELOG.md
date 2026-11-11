# 变更日志

按日期分组，从新到旧。

## 2026-11-11

- 新增 §5.7「真实监管结果外部检验」（英文 `5.7 External Validation Against Real Regulatory Outcomes`）与 Table 5.5（5 个排序 × 非标审计意见 / t+1 披露类违规的 AUC 与前 10% 富集）、Table 5.6（按公司分组 5 折交叉验证 AUC 与 ΔAUC）：`build_section5.py` 增加 `_load_event_numbers()`、`_table_55`/`_table_56`（含中文版）、`_section57_en`/`_section57_cn`、`_abstract_external`/`_abstract_external_cn` 与中英文 Word 插入逻辑（英文锚 §5.5 正文、中文锚 `CN_SLOT_S55`）；markdown、中英 docx 与中文完整稿同步。
- 新增 `src/data_ingestion/event_parser.py`（解析 CSMAR `FIN_Audit.xlsx` / `STK_Violation_Main.xlsx`：跳过中英标签两行、代码 zfill(6)、审计意见窄/宽口径分类、违规 t+1 对齐）、`scripts/run_03b_build_event_table.py`（→ `data/processed/event_table.csv`，188 条非标意见 2.31%、327 条宽口径 4.02%、1,757 条 t+1 违规 21.58%、1,196 条披露类 14.69%）。
- 新增 `src/evaluation/event_eval.py`（bootstrap AUC/lift/recall、`StratifiedGroupKFold(groups=symbol)` OOF 预测、配对 ΔAUC）与 `scripts/run_07b_event_models.py`（四个标签 × 五个排序 × 三组特征 × 两种模型）；实测财务单独排序对非标意见 AUC 0.640、前 10% 富集 2.18×、Beneish 代理仅 0.405；文本单独在所有标签都弱于财务，但融合的 ΔAUC 全为正（+0.007~+0.026，5/8 区间不含 0）。
- 页数收敛：加入 §5.7 后英文终稿一度 16 页（超 12–15 页），新增 `BODY_LINE_SPACING = 1.45` 与 `_fit_body_spacing()`（只压原本 1.5 倍的正文段落）→ 英文 109 段 6 表 15 页、中文 73 段 6 表 9 页。
- 文档同步：`docs/manuscript_chinese_draft.md` 新增中文 §5.7 与摘要/结论外部检验句；`docs/manuscript_conclusion_section.md` 新增第四点结论并改写局限段；`docs/reproducibility_guide.md` 新增 §3.2（事件数据管线四脚本、两张表、`--boot` 用法）与 §7 §5.7/行距条目；`docs/team_handoff.md` 升 v0.3（新交付件段数与页数、外部检验数字、新命令）；`GUIDE.md` 更新头条数字、阶段表两行与交付件页数。
- 单测：`tests/test_build_section5.py` 新增 Table 5.5/5.6 中英形状、ΔAUC 列与 §5.7 段落断言，全套 **114/114 通过**。
- 新增 `scripts/run_14_publish_pdfs.py`：把 `outputs/.tmp/final_*.pdf` 覆盖到 `outputs/manuscript/`，逐个报告被 Acrobat/WPS 锁定的目标（退出码 2），避免手工复制时的静默失败。
- 新增 `docs/csmar_event_data_guide.md`：第二轮换结果变量所需的 CSMAR 数据指引——审计意见（必下）、会计差错更正/财务重述、违规处理、特别处理（可选）四张表的库路径、时间窗口、目标字段、导出命名（`data/raw/csmar_events/`）、自检方法、七个常见坑与"按订阅权限怎么选"的决策树；同时说明问询函不在 CSMAR 及其替代来源（交易所官网爬虫 / CNRDS / textdata）。
- 新增 `scripts/run_00c_inspect_csmar_export.py`：打印任意 CSMAR 导出（xlsx/csv）的 sheet、列名、行数、证券代码样例与长度，用于下载后 5 分钟自检（前导零、行数量级、意见类型列可读性），并已用根目录 `STK_LISTEDCOINFOANL.xlsx` 验证。
- 新增 `data/raw/csmar_events/README.md`（本地目录，data/ 不入库）：规定四个文件名与《数据说明》保留规则。
- `GUIDE.md`：§1.2 数据来源表新增事件变量指引入口，§5 阶段表新增 `run_00c_inspect_csmar_export.py`。

- 新增 §5.6「从第一版到第二版：做法改进与结果差异」（英文 `5.6 From the First to the Second Specification`）与 Table 5.4（10×3 设定对比）：`build_section5.py` 增加 `_load_v01_metrics()`（读冻结的 `outputs/.tmp/v01_dual_benchmark/tables/`）、`_table_54()` / `_table_54_cn()`、`s56a`/`s56b` 段落与 Word 插入逻辑（英文锚 §5.5 正文、中文锚 `CN_SLOT_S55`），markdown 与中英 docx 同步。
- 终稿重建：英文 `Group12A2_Final_EN.docx` 101 段 4 表 → PDF **14 页**（在 12–15 页要求内），中文 `Group12A2_Final_CN.docx` 65 段 4 表 → PDF 8 页；摘要结果句同步为 v0.2（融合 0.103 / 财务 0.136 / 校准 1.84 / legacy 1.20）。
- 两版过程固化：新增 git tag `v0.1-baseline`（提交 `542395b`，第一版代码：引导词典 + 子串计数 + 仅 M > −1.78）与 `v0.2-calibrated`（第二版），第一版的数据/结果备份清单写入复现指南 §7；新增提交 `b700d27` 与清理提交 `4687e46`（不再跟踪版式探针临时文件）。
- 新增 `scripts/analyze_branch_beneish_components.py` 与 `outputs/tables/branch_component_correlations.csv`：把 M-Score 拆成 DSRI/GMI/AQI/SGI/DEPI/SGAI/LVGI/TATA 八个分量分别与四个排序求 Spearman ρ，实测文本单独对任一分量 |ρ| ≤ 0.064（财务对 DSRI −0.181、SGI 0.171）→ 排除"基准太粗"这一零成本分支。
- 新增 `outputs/reports/positive_result_branches.md`：7 个换结果变量分支的可行性评估（t+1 年报问询函为首选、非标审计意见为兜底、重述/处罚备选、内控否定与业绩预告修正排除），含数据来源、成本、文献先验、时间对齐与幸存者偏差风险清单、开工第一天的 CSMAR 订阅核对清单。
- 文档同步：`docs/manuscript_chinese_draft.md` 新增中文 5.6（含 10×3 表）；`docs/reproducibility_guide.md` 新增 §3.1 分支评估与 §7 两版版本控制条目；`GUIDE.md` 阶段表新增 `analyze_branch_beneish_components.py`。
- 单测：`tests/test_build_section5.py` 新增 Table 5.4 形状、中文表头与 §5.6 段落断言，全套 **88/88 通过**。

- 新增根目录 GUIDE.md（查阅指南，中英双语）：按「我想找 X」的检索表 + 顶层目录地图 + data 三层 + outputs 逐项清单 + scripts 阶段对照 + 五个坑 + 待确认事项。README「仓库内容」加入口，并把过时的测试用例数 39 修正为 77（实际 77/77）。
- 方向调整落地（换词典 + 重校准基准）：词典升 v0.2——姚加权等 (2021) 正式文本词表 3,585 正 / 1,633 负 + 扩充不确定性词表（~100 词），词频计数由子串改为 jieba 词元精确匹配（count_dictionary_tokens + jieba_userdict.txt 5,218 词）；Beneish 基准由单一 −1.78 改为 legacy/calibrated 双口径（calibrated=样本 M-Score 前 10% 分位）；src/pipeline.py、figures、narrate_results、descriptives、run_07 同步双基准，单测 77/77。
- 新增 scripts/run_05b_recompute_text_features.py（8 进程并行全量重提取 10,052 份年报 PDF + mda_text_{year}.jsonl 缓存），后台已启动（约 2–3 小时）；旧 text_features CSV 备份到 data/interim/v0.1_text_features_backup/。
- **v0.2 词典全量重跑完成**：run_05b 三年 10,052 份 PDF 全部重提取（2021 3,060/3,075 ok、2022 3,387、2023 3,590），run_06 特征表文本可用 9,991 条（与 v0.1 一致），run_07 重跑全部表格与图，单测 85/85。结果对比 v0.1：ρ text −0.030→−0.029、fused 0.103→0.103、AE 0.012(p=0.272)→0.009(p=0.409)；校准口径 top-10% 富集 text 1.07→0.85、fused 1.90→1.84、finance 1.87 不变；SHAP 财务 65.9%→65.4%；前 10% 重叠 finance–fused 0.828→0.817。阴性结论不变且更稳。
- 新增 scripts/run_05c_lexicon_density.py（同一 token 流上比较 v0.1/v0.2 词表命中密度，写 outputs/tables/lexicon_density.csv）：情感词每千词元 13.41→111.30（8.30×），证明否定结论不是词表过稀所致。
- 新增 scripts/compare_runs.py（对比两次运行的表格目录，输出样本、ρ、双基准富集率、SHAP、名单重叠与第一名的变化），用于 v0.1/v0.2 回归核对。
- 用 v0.2 数字回填 docs/manuscript_experiment_section.md、docs/manuscript_chinese_experiment_section.md、docs/manuscript_chinese_draft.md（摘要/§5/§6）、docs/manuscript_conclusion_section.md（§6 头条结果由占位符改为实测值）、docs/team_handoff.md。
- 重建演示稿：outputs/slides/Group12A2_Deck.pptx 与 .pdf（12 页）改用 v0.2 数字；修掉 build_slides.py 里两处硬编码（自编码器 p 值写死 0.27 → 读表 0.41、样本量写死 8,140 → 读表）。重跑 run_11_descriptives 与 run_12_narrate_results，新增 outputs/reports/v02_results_diff.md 记录 v0.1→v0.2 差异。
- 文档同步升 v0.2：feature_dictionary / reproducibility_guide / manuscript_implementation_section / manuscript_methodology_section / manuscript_assembly_checklist；修正词典标题误写（《中国上市公司文本信息披露的情感分析》→《语调、情绪及市场影响：基于金融情绪词典》）；slides 三稿与中文稿局限表述同步（bootstrap/引导版→公开词表+代理指标）。
- 新增 scripts/build_section5.py：单一数字源重写 §5 并把 Table 5.1–5.3 直接排进中英 Word 终稿（英文 91 段/中文 56 段槽位定位），解决交付件 11 页不足 12–15 页的硬风险；实测英文终稿 13 页。
- 新增 scripts/build_slides.py：从 outputs/tables 生成 12 页 16:9 演示稿 outputs/slides/Group12A2_Deck.pptx 与同名 PDF，数字与 §5 同源；新增 tests/test_build_section5.py，单测 85/85。

## 2026-11-10

- CSMAR 三表到位：用户把 FS_Combas/FS_Comins/FS_Comscfd.xlsx 放入 data/raw/csmar/（135.31/64.39/62.4 MB）；字段映射经 probe 验证全部正确，csmar_parser 无需改动；run_03 产出 finance_intermediate.csv（10,646 行×16 列）、run_06 产出 feature_table.csv（10,172 行×20 列）。
- 诊断出 CSMAR 年份范围错误：三表实际覆盖 2022–2025（资产负债表另含 2026 一季度），缺 2020 与 2021 基期年 → 导致 Beneish M-Score 仅 2023 年可算（2979/3603），2021/2022 样本无金融前值；已请用户按 docs/csmar_download_guide.md 第 40 行重新下载报告期 2020-01-01~2023-12-31 并覆盖现有文件。
- run_07 在真实数据上端到端跑通（n=2,947 个 9 特征+M-Score 完整行，均为 2023 年）：8 张图 + 7 张表全部生成；Spearman ρ = if_finance 0.021 / if_text −0.013 / if_fused 0.024 / ae_fused −0.046，top-10% 富集率 ≈1.0（单年子集，非最终结论，待三年数据补全后重跑）。
- 修复 src/pipeline.py SHAP 子采样缺陷：n>2000 时 top-1 审查优先行可能不在随机子样本内导致 `get_loc` KeyError；现强制把 top-1 行并入 SHAP 子样本，local 解释永远可用；完整套件 76/76 通过。
- 修复 src/features/beneish.py 除零缺陷：基期营收/总资产为 0 时比率产生 ±inf，25 个 M-Score 为正无穷污染基准标记与秩相关；现 inf/-inf 统一转 NaN（该 firm-year 视为 M-Score 无定义）；新增回归测试，完整套件 77/77 通过；重跑 run_06 后 finance_ok 2979→2954。
- 全量 QC 与描述统计正式生成（完整三路文本数据）：run_08 qc_summary 显示 issue_share 2021=0.62%/2022=0.47%/2023=0.70%（qc_issues 181 行）；run_11 descriptives_summary 显示下载覆盖 97.1%/99.5%/99.6%、文本可得率 96.5%/99.0%/99.0%；发现 Beneish M-Score 在 2023 年极端右偏（min −3.5e7/max 1.3e5、>−1.78 的 flag 率约 66%），作为基准适用性讨论点记录，待三年数据补全后复核。
- 三年完整实验完成（用户补全 2020–2023 CSMAR 三表）：新文件覆盖后 run_03 产出 finance_intermediate 20,103 行（balance 96,528/income 115,931/cashflow 96,525 行，均合并口径）；run_06 finance_ok 2,954→8,276；run_07 有效样本 n=8,140，Spearman ρ = if_finance 0.136(p<0.001) / if_text −0.030 / if_fused 0.103(p<0.001) / ae_fused 0.012(不显著)，top-10% 富集率 = if_finance 1.217 / if_fused 1.176；SHAP 组贡献 finance 0.659/text 0.341。诚实结论：财务异常分与 Beneish M-Score 有弱但显著的正排序相关，文本特征未带来增量（RQ1 不成立），AE 稳健性未复现。results_narrative.md 已生成。
- 论文结果回填：docs/manuscript_experiment_section.md（英文 §5）用真实数字填充（n=8,140/三年 ρ/富集/SHAP/局部分析）；docs/manuscript_chinese_draft.md 摘要与 §5/§6 全部 27 处占位符用真实结果替换（fill_chinese_placeholders.py 一次性替换，剩余占位符 NONE）。
- 英文终稿 Word 组装完成：insert_section5_results.js 在 PaperDraft（worktree wt-mwautyhj-9j1kvo）内①setText 替换旧 §5 为「5. Experiment and Results」+5.1/5.2/5.3 真实数字②摘要 appendText 结果句③插入 5.4 Robustness(RQ3)/5.5 Discussion④插入词典出处参考文献 [22]-[24]（姚加权2021/Loughran-McDonald 2011/曾庆生2018）；导出 outputs/manuscript/Group12A2_Final_EN.docx（91 段、24 条参考文献、§5 标题正确、摘要末尾含结果句）；worktree merge 被用户拒绝，保留 draft（docx 已从 worktree 导出成功，merge 为可选操作）。注意 [22]/[24] 中文文献精确标题/期刊未核实，待用户核对。
- 中文终稿 Word 组装完成：scripts/run_13_build_chinese_docx.py 把 docs/manuscript_chinese_draft.md 转成 outputs/manuscript/Group12A2_Final_CN.docx（宋体正文/黑体标题/1.5 倍行距，53 非空段，标题/摘要/关键词/§1-§6 齐全）；同时修正中文稿 §6 结论段一处不准确表述（原把财务单独 ρ=0.136 误挂「融合」，改为「财务单独模型 ρ=0.136…融合模型 ρ=0.103」）。
- 参考文献 [22]/[24] 精确出处已 web 查证并补全（原词典头部注释只给作者+年份，且标题不准）：[22] 姚加权、冯绪、王赞钧、纪荣嵘、张维《语调、情绪及市场影响：基于金融情绪词典》管理科学学报 2021,24(5):26-46（词典注释误写为《中国上市公司文本信息披露的情感分析》）；[24] 曾庆生、周波、张程、陈信元《年报语调与内部人交易：“表里如一”还是“口是心非”？》管理世界 2018,(9):143-160。英文终稿 + 中文终稿（docx+PDF）已重新生成。

## 2026-11-06

- 三路巨潮年报下载全部完成：2021=2,976 ok/189 missing、2022=3,200 ok/204 missing、2023=3,358 ok/245 missing；missing 以 920xxx 北交所新代码为主（巨潮仅按 2025-10 切换前的旧码收录）。
- 北交所旧码恢复方案落地：官方新旧代码对照表（bseinfo.net）→ data/external/bse_920_code_mapping.csv（248 行，156 个缺失 920xxx 全覆盖）；cninfo_client 新增 search_annual_reports_bse（BSE 旧码需 category 空值 + searchkey='年度报告' 单页命中，category_ndbg_bj 下 0 hits、无 category 键 0 hits、不设 searchkey 时单页 30 行内无年报）；标题过滤收紧（更正公告/说明会预告/披露提示性 等公告型标题不再误收）；新增 scripts/run_10_bse_legacy_download.py（按旧码检索、按新码落盘）；单测 62/62。
- 新增 QC 模块 src/features/qc.py 与 run_08 驱动脚本（文本特征逐行质量标记 + 下载审计并入 + qc_summary/qc_issues 输出）；run_05 增加每 25 文件断点写盘防进度丢失；单测增至 50/50。
- run_02 新增 --codes/--force 定向修复参数（审计→补下闭环）；2022/2023 MD&A 提取并行启动，checkpoint 已验证生效（25 文件即落盘）。
- 新增 docs/slides_deck_draft.md 演示稿初稿（12 页英文 slide 文案+讲者备注，结果页留占位）与 docs/team_handoff.md 组员分工交接清单（含 CSMAR 三表命名、命令速查、截止提醒）。
- run_07 端到端冒烟通过（演示特征表 n=240：pipeline→8 张图→outputs/reports/experiment_summary.md，exit 0）；修复 run_07 docstring 反斜杠 SyntaxWarning。
- 新增 scripts/run_00_env_check.py 管线就绪探针（一键显示 14 项输入的就绪/缺失状态，供组员自查）。
- data/raw/csmar/README.md 与 data/raw/cninfo/README.md：数据落位说明（CSMAR 三表精确文件名与口径、cninfo 自动目录说明）。
- locate_mda 二次修复（strong-line 打分）：目录行以「第X节」开头但正文标题独占一行时，旧逻辑误选 56 字符目录切片（实例 000408：4 tokens）；改为「标题独占一行且非目录行（无点线/页码尾数）才算强候选，否则取最长切片」；新增回归测试，单测 51/51；三路提取已用修复后代码重启（旧进程全部 kill，2022/2023 靠 checkpoint 只损失 <25 文件）。
- 新增 scripts/run_09_repair_downloads.py（读 download_audit.csv 定向重下，dry-run 默认、--apply 才下载，写 repair_log）；已 dry-run 冒烟通过。
- 新增 scripts/run_03_build_finance_intermediate.py（CSMAR 三表 → 金融中间表：probe_field_columns 只读所需列以适配 466MB 真实文件）；csmar_parser 按真实文件校准：支持现代版式（英文代码表头行+英文名称行+单位行）、Typrep 合并口径过滤、CSMAR 物料代码映射（A001000000 资产总计等）、_parse_period 自动丢弃单位行；新增现代版式 2 测试，单测 59/59。
- 修复 src/pipeline.py 两处问题：SHAP 复用已拟合的融合 IF（不再重复拟合）；top-1 局部解释行与 SHAP 子采样索引对齐（n>2000 时原实现会错位到别的公司）。新增 tests/test_pipeline.py 3 条端到端测试（输出齐全、top1 一致性、全缺行报错）；单测 57/57。
- 新增 feature_table 集成测试（样本框+金融中间表+文本帧全链路）；修复契约缺口：build_feature_table 现在会在缺 sga 列时用 sga_sales+sga_admin 兜底合成；单测 54/54。
- 新增 docs/manuscript_experiment_section.md 实验章节英文模板（24 Nov 交付，5.x 结构与表图占位）。
- 标题识别缺陷修复：部分年报标题为「YYYY年度报告」式样（缺第二个年，如 水井坊2021年度报告/北方稀土2021年度报告全文），旧过滤器只认「年年度报告」→ 大量误报 missing；新增 _has_annual_report_tag 双式样匹配 + select 同年锁定复用；run_09 二轮修复后单测 64/64。
- run_04 审计合并 repair_log（symbol/fiscal_year→code/year 列名归一、按 mtime 最新覆盖）：终审 **ok=10,051 / missing=121 / mismatched_year=0 / too_small=0**（覆盖 98.8%）；run_09 两轮合计恢复 20 个错位/缺失文件。
- 数据边界确认并文档化：121 个 missing 中 71 个为 920xxx 北交所公司在挂牌前的 NEEQ 三板年份（巨潮不收录三板公告，orgId 检索 0 结果），约 50 个为退市/重组/长期停牌类；由 QC 标记 download_missing，论文中作为数据可得性边界陈述。
- 真实数据冒烟通过：run_06 用真实样本框+资产负债表中间表+部分文本帧产出 feature_table.csv（10,172 行；text ok 1,390/missing 8,782=提取进行中；finance 0=待 FS_Comins/FS_Comscfd）；run_08 真实数据 QC 输出 qc_summary.csv（issue_share ≈0.9%）与 qc_issues.csv（121 download_missing+13 no_mda+2 suspicious_short）；三特征分布正常（readability 均值 0.0087、sentiment 0.009、uncertainty 0.0024）。
- 新增描述统计模块：src/reporting/descriptives.py（下载覆盖/文本可得性/特征摘要/Beneish 标记四类表、无 tabulate 依赖）+ scripts/run_11_descriptives.py → outputs/reports/descriptives_summary.md；真实数据冒烟：10,172 firm-years、3,694 家、下载覆盖 97.1%/99.5%/99.6%（2021/22/23）、text ok 1,390（提取进行中）；单测 68/68。
- 新增一键流程编排：scripts/run_99_full_pipeline.py（按序跑 01→03→04→05(三年)→08→06→11→07→12，--stage 过滤/--skip-05/退出码 2=前置未就绪跳过，runbook 写 outputs/reports/pipeline_runbook.md）；复现指南新增 §6。
- 新增结果叙事模块：src/reporting/narrate_results.py（把 model_metrics/topk_metrics/ranking_overlap/shap_* 表转成英文 Results 段落，RQ1-RQ3 自动填数、对角自配对剔除）+ scripts/run_12_narrate_results.py → outputs/reports/results_narrative.md（服务于 24 Nov 实验章节）；单测 73/73。
- 新增 docs/manuscript_methodology_section.md：§3 研究设计过去时改写版（对齐实际实现，超参/种子/标准化/评估全部填实：IF 500×256×seed42×top10%、AE 16-8-16 瓶颈8、winsor 1-99%、<20 稀疏组回退、Beneish -1.78、Spearman+富集率）。
- 实现章节 QA + 词典出处排查：更新 docs/manuscript_implementation_section.md 状态附录为当前数字（下载完成 10,051/121、提取 900/975/900）；确认词典文件为 UTF-8（PowerShell 显示乱码为假象）；发现词典出处（姚加权 2021、Loughran-McDonald 2011、曾庆生 2018）未列入 proposal 21 条参考文献，已在组装清单新增「待补参考文献」3 条；词典为 v0.1 引导小子集（38/33/23 词）已如实披露。
- 新增终稿组装文档：docs/manuscript_assembly_checklist.md（评分 Option 2 要求逐节对齐来源文件/状态/剩余工作 + 方法学事实索引 + 风险）；docs/manuscript_conclusion_section.md（§6 结论英文草稿，含一处待填头条结果占位）。
- 修复 run_05 断点续传缺陷：重启时 set_index('symbol').to_dict('index') 丢弃索引列，carried-over 行 symbol 变 NaN（污染 2022/2023 共 175 行，QC 显示 '000nan'）；现改为读回时重新挂回 symbol、过滤非法行、写盘前按 symbol 去重；2022/2023 任务已用修复后代码重启（NaN 行自动重提取，2021 无此问题未动）。
- 强化 MD&A 批量提取容错：`extract_mda_features()` 现在把损坏或不可读 PDF 记为 `pdf_error`（含异常类型）而不终止整批断点任务；新增回归测试，完整套件 74/74 通过（3 条既有合成样本警告）。复现指南与实验章节模板已同步 `pdf_error` 的 QC/披露口径。
- 强化 run_03 CSMAR 三表预检：利润表或现金流量表缺失时，先列明缺失文件并以 exit 2 退出，不再无意义读取 466MB 资产负债表或写出部分金融表；CLI 冒烟验证通过，新增回归测试，完整套件 75/75 通过。
- 补充 QC 回归断言：损坏或不可读年报的 `pdf_error` 状态会明确进入 `qc_issues.csv`，避免被静默视为正常样本；新增端到端一行特征→issues 表验证，完整套件 76/76 通过。
- 新增 `docs/slides_deck_spec.md`，锁定 12 页汇报的版式、英文文案、结果页替换规则与演示边界；已在 `course_paper_materials.univer` 的 `manuscript-assembly` 草稿工作区创建 Presentation Unit 并完成、检查第 1–2 页（标题、研究问题）视觉稿，均无布局 lint 问题。
- 完成评分表第三部分「System Implementation and/or Model Development」正文：英文 §4（4.1–4.6 共 23 段、约 2,600 词，研一平实语气，全部事实对齐既有代码/文档，无虚构结果）写入 Group12A2 原论文（原 §4→§5、§5→§6 已重编号，作者/摘要/§1–§3/参考文献 [1]–[21] 原样未动）；同步生成中文对照版（独立 Doc Unit，中文字体宋体）。交付：`outputs/manuscript/Group12A2_System_Implementation_EN.docx/.pdf` 与 `..._CN.docx/.pdf`；python-docx 校验通过（英文 84 段/21 条参考文献/Times New Roman，中文 23 段/宋体）。

## 2026-11-05

- 完成环境搭建：.venv（Python 3.12.14）、依赖冻结 requirements.txt、pytest 就绪（Phase 0）。
- 完成制造业样本框：3,694 家公司 / 10,172 个 firm-year（2021–2023），输出 `data/processed/` 清单与下载打卡表。
- 完成巨潮（cninfo）公告检索与 PDF 下载客户端（公共接口、免注册），端到端验证通过；启动 2021–2023 三路批量下载。
- 完成特征工程初版：financial（6 金融特征）、textual（MD&A 提取 + 3 文本特征）、beneish（M-Score 基准）、standardise（winsorise + 组内标准化），单测 14 个全过。
- 新增 docs/feature_dictionary.md 固化全部公式与预处理规则（v0.1，词典为引导版）。
- 完成 Phase 3 建模评估初版：isolation_forest（三矩阵、方向校正）、autoencoder（MLPRegressor 重建误差、超参落盘 JSON）、shap_explain（全局/分组/局部）、metrics（Spearman/事件率/enrichment/top-k 重叠）、pipeline 总编排；单测 29 个全过。
- 演示数据冒烟通过：80 家×4 年合成数据跑通全管线，fused Spearman=0.506、top-10% enrichment=4.0×、planted anomaly 命中 top1。
- 新增 CSMAR 三表容错解析器 csmar_parser（表头定位、别名映射、合并口径过滤、日期多格式），单测 4 个全过（共 33/33）。
- MD&A 定位算法修复：改为「最长标题候选切片」，正文章节不再被目录短切片截断（实测 000008：67→7,835 tokens、000012：90→11,085 tokens），并支持备用标题「经营情况讨论与分析/管理层分析与讨论」；单测增至 36/36。
- 新增特征表融合模块 feature_table（样本框+金融特征+M-Score+文本特征合并、text_quality 三分类）与 run_06 驱动脚本；单测增至 39/39。
- 新增 docs/reproducibility_guide.md 复现指南 v0.1（环境→数据→特征→建模→输出全流程命令与已知近似）。
- 修复 select_annual_report 跨年误选缺陷：选择范围锁定同年报告（含 更新后/更新前/全文 变体），无同年报告时返回 missing 而非误下其他年份；新增 2 测试（41/41 通过）；删除 4 个已确认的错位 PDF 待重下。
- 新增图件模块 src/reporting/figures.py（得分分布/富集率/特征组贡献/SHAP 重要性/排序重叠 + make_all_figures 批量）与 run_07 实验驱动（pipeline+图件+实验摘要一键出）；matplotlib 3.11.2 入 requirements；单测增至 47/47。
- 新增 docs/slides_outline.md 演示大纲骨架（12 页，含占位与分工建议）。
