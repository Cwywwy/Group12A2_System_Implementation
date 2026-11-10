# 课程论文可复现研究管线 · 项目计划书

- 项目：Group12A2 · Screening Financial Disclosure Risk through Textual-Financial Feature Fusion and Explainable Anomaly Detection: Evidence from Chinese A-share Manufacturing Firms
- 课程：Introduction to FinTech（Option 2: Research Manuscript，12–15 页 + 12 分钟 / 12 页演示）
- 创建日期：2026-11-05
- 状态：**已确认（用户批准），Phase 0 已完成、Phase 1–2 进行中、Phase 3 初版完成**
- Python 版本：**3.12.14**（bundled runtime：`C:\Users\Administrator\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe`；系统自带 3.4.4 不可用）

## 1. 目标与范围

把现有 proposal 升级为含 Experiments with Results 的可复现实证论文（及格导向，不追求创新，重点可复现）：

- 样本：中国 A 股制造业 **2021–2023**（基期 2020），财务数据 CSMAR、年报 MD&A 巨潮 cninfo。
- 特征：6 金融 + 3 文本（与大纲 §V.A/§V.B 一致），winsorize 后按制造业子行业-年份组内标准化（稀疏组 fallback）。
- 模型：Isolation Forest 主模型（500 trees、max_samples=256、固定种子、top-10% 阈值，5%/15% 敏感性）+ autoencoder 稳健排名 + SHAP 解释。
- 评估：Spearman（异常分 vs Beneish M-Score）、top-10% 事件率与 enrichment ratio。
- 范围外：不换 Wind、不扩年份（已确认 2021–2023）、不建 Web 应用、不做因果推断、不代写个人 Essay。

## 2. 环境与依赖

- `.venv`：用 Python 3.12.14 创建于项目根，依赖冻结到 `requirements.txt`。
- 核心依赖：pandas、numpy、openpyxl（读大 xlsx）、scikit-learn（IsolationForest、MLPRegressor 作 autoencoder）、shap、jieba（中文分词）、pypdf（年报 PDF 提取）、pytest。
- 说明：17.8MB 的 xlsx 用 pandas/openpyxl 直接读写（研究管线自身需求，不适合 Univer Facade 逐格循环）；docx/pptx 论文材料用 Univer 工具处理。
- 巨潮接口选型（决策记录）：官方开放平台 webapi.cninfo.com.cn 为 SPA，需开发者注册 + token（mcode），不作为主线；改用其公告检索页同源公共接口（免注册，akshare / cninfo-cli 同款）：`POST new/information/topSearch/query`（form 编码）取 orgId → `POST new/hisAnnouncement/query`（form 编码，JSON body 会被静默忽略）取公告列表 → `static.cninfo.com.cn` 下载 PDF。已实测全链路（2026-11-05，000001 平安银行 2021 年报 4,737,026 B）。

## 3. 目录与模块划分

```
DSW/
├─ .github/plans/            计划书（完成后归档 .github/plans/done/）
├─ .venv/
├─ data/
│  ├─ raw/csmar/             财务三表 .xlsx + 数据说明（用户下载）
│  ├─ raw/cninfo/{2021,2022,2023}/   年报 PDF（脚本批量下载，run_02）
│  ├─ interim/               MD&A 提取文本、中间表
│  └─ processed/             firm-year 特征表、异常分、基准
├─ src/
│  ├─ config.py              全局常量：种子、阈值、路径、特征定义
│  ├─ sample_frame.py        制造业样本框（读 STK_LISTEDCOINFOANL）
│  ├─ data_ingestion/
│  │  └─ cninfo_client.py    巨潮公告检索 + 年报 PDF 下载（公共接口）
│  ├─ features/
│  │  ├─ financial.py        6 金融特征
│  │  ├─ textual.py          MD&A 提取 + 分词 + 3 文本特征
│  │  ├─ beneish.py          Beneish M-Score（8 指标）
│  │  └─ standardise.py      winsorize + 子行业-年份组内标准化
│  ├─ models/
│  │  ├─ isolation_forest.py 主模型（固定参数、方向校正）
│  │  ├─ autoencoder.py      重建误差稳健排名（记录全部超参）
│  │  └─ shap_explain.py     全局 + 局部解释
│  ├─ evaluation/
│  │  └─ metrics.py          Spearman、事件率、enrichment ratio
│  └─ pipeline.py            总管线编排
├─ scripts/                  run_01_sample.py … 各阶段入口
├─ outputs/                  tables/ figures/ reports/
├─ docs/                     下载指引、特征字典、决策记录
└─ tests/ + tests/reports/   pytest 用例与报告
```

| 模块 | 职责 | 交互方式 | 状态 |
| --- | --- | --- | --- |
| sample_frame | 读公司基本信息表，按 IndustryCodeD 筛制造业，输出 firm-year 清单 | 供 features 与下载清单使用 | 新增·已完成 |
| data_ingestion | 巨潮公共接口检索公告 + 下载 PDF（过滤摘要/半年度/英文/修订） | 供 run_02 批量脚本调用 | 新增·已完成 |
| csmar_parser | 容错解析 CSMAR 三表（表头定位、别名映射、合并口径过滤） | CSMAR xlsx → 中间表 | 新增·已完成初版（4 单测过，待真实文件校验） |
| financial | 6 金融特征公式与 winsorize | 读 CSMAR 三表 → 特征表 | 新增·已完成初版 |
| textual | 按标题定位 MD&A、jieba 分词、3 文本指标 | 读 PDF → 指标 | 新增·已完成初版 |
| beneish | 8 指标 + M-Score（仅作基准，不进训练） | 读三表 → 基准表 | 新增·已完成初版 |
| standardise | 子行业-年份组内 z 标准化 + 稀疏 fallback | 特征表 → 模型矩阵 | 新增·已完成初版 |
| isolation_forest | 三矩阵分别拟合，异常分方向校正 | 矩阵 → 排名 | 新增·已完成初版 |
| autoencoder | MLPRegressor 重建误差排名，超参全记录 | 矩阵 → 排名 | 新增·已完成初版 |
| shap_explain | TreeExplainer 全局/局部贡献 | 模型 → 图表 | 新增·已完成初版 |
| metrics | 三种评估指标 + top-k 重叠 | 排名×基准 → 表 | 新增·已完成初版 |
| pipeline | 阶段编排与产物落盘 | 以上所有 | 新增·已完成初版（demo 冒烟通过） |

特征公式（初版，最终以特征字典固化）：

- 金融：ROA=净利润/资产总计；资产负债率=负债合计/资产总计；营收增长率=(营收_t−营收_{t-1})/营收_{t-1}；经营现金流/资产=经营活动现金流净额/资产总计；应收账款周转率=营业收入/应收账款净额；总应计/资产=(净利润−经营现金流净额)/资产总计。
- 文本：可读性（基于文档化长度-复杂度规则，参考 Xu-Yao-Chen 2019 思路）；情感平衡=正向词比例−负向词比例（词典：姚加权等 2021 中文金融情感词典，NTUSD 补充）；不确定性比率=不确定词数/总词数（词典来源与版本写入特征字典）。
- Beneish M-Score：8 指标标准公式（DSRI/GMI/AQI/SGI/DEPI/SGAI/LVGI/TATA），阈值 −1.78 仅用于基准标记。

## 4. 阶段拆分与完成标准（对齐课程里程碑）

| 阶段 | 内容 | 完成标准 | 预期产出 | 目标日期 |
| --- | --- | --- | --- | --- |
| 0 环境与确认 | .venv + 依赖 + 本计划确认 | 全部依赖可导入、pytest 可运行 | .venv、requirements.txt | 11-06 ✅ 已完成 |
| 1 数据接入 | 脚本下载巨潮 PDF；用户下载 CSMAR 三表；解析器与演示数据 | 演示数据跑通全管线；真实数据校验脚本就绪 | 解析器、demo 数据、制造业公司清单 | 11-08 🚧 收尾中：**三路下载完成+BSE 旧码恢复完成（run_10：403 downloaded/69 missing=未挂牌年份）**；**终审 run_04：ok=10,051 / missing=121 / mismatched_year=0 / too_small=0（覆盖 98.8%）**；121 missing=71 个 920xxx 挂牌前 NEEQ 年份（巨潮不收录，数据边界已文档化）+约 50 个退市/重组类；csmar_parser 已按真实 FS_Combas.xlsx（466MB）校准（现代英文版式+Typrep+物料代码映射，64/64 单测）；**run_03 已用真实资产负债表产出 finance_intermediate.csv（2020–2023 共 20,103 行；样本 2021–2023 覆盖 10,172/10,172）**；FS_Comins/FS_Comscfd 待组员放齐后重跑 run_03；MD&A 三路提取 checkpoint 进行中（2021=325/2022=475/2023=450 行） |
| 2 特征工程 | 特征字典 + 实现 + 单测 | 9 特征 + M-Score 单测全过 | 特征表（interim） | 11-09 🚧 进行中：四模块初版+单测已过；特征表融合模块 feature_table + run_06 就绪（已用真实资产负债表+部分文本帧冒烟：10,172 行、text ok 1,390）；MD&A 三路提取进行中（checkpoint 2021=425/2022=600/2023=550 行，2022/2023 已修 symbol 丢失缺陷并重启）；QC run_08 真实数据冒烟通过（issue_share≈0.9%）；文本特征分布正常 |
| 3 建模与评估 | IF / AE / SHAP + 三种评估 | 三矩阵结果表与图产出、方向校正记录 | outputs 表图 | 11-10 前 ✅ 初版完成：models/evaluation/pipeline 初版 + demo 全管线冒烟（fused Spearman=0.506、top-10% enrichment=4.0×、planted anomaly 命中 top1）；回补 reporting/figures + run_07；本轮 pipeline 两修复（SHAP 复用拟合模型、top-1 局部解释索引对齐）+ tests/test_pipeline.py 端到端 3 条（57/57 单测） |
| 4 成文 | 10 Nov 交 6 页实现章节；24 Nov 交 4 页实验章节；12-15 终稿 + 12 页演示 | 三份交付物齐备 | manuscript 更新 | 11-10 / 11-24 / 12-15 🚧 进行中：System Implementation 6 页英文+中文已写；Experiment 4 页英文模板已写（docs/manuscript_experiment_section.md）并已用真实数字填充；**英文终稿 Word 已交付 outputs/manuscript/Group12A2_Final_EN.docx（91 段、§1–§6、24 条参考文献、摘要结果句）**；**中文终稿 Word 已交付 outputs/manuscript/Group12A2_Final_CN.docx（53 段、宋体/黑体、§1–§6）**；结果自动叙事 run_12 → results_narrative.md；**剩余：slides 结果页（用户暂停，待明确要求恢复）+ [22]/[24] 中文参考文献精确出处（待用户核对）** |
| 5 自检 | 复现走查 + 缺失报告 + 一键重跑 | 干净环境重跑成功 | 复现说明、日志 | 12-10 🚧 进行中（提前启动）：docs/reproducibility_guide.md 复现指南 v0.1 已写；scripts/run_00_env_check.py 就绪探针已加（当前 10/14：缺 3 个 CSMAR 三表文件 + 2021 文本特征提取中） |

课程评分口径：10 Nov（6 页，15%）、24 Nov（4 页，10%）、15 Dec 终稿+演示（10%）、提前提交 bonus ≤10；个人 Essay（50%，20 Dec）由组员自行撰写。

## 5. 测试策略

- pytest 覆盖每模块正向、边界、错误案例（空值、极值、缺文件、编码错误、稀疏组）。
- 演示数据：合成中间表（80 家 × 4 年，20% planted anomaly）+ 特征表 → smoke test 跑通全管线（11-05 通过；假年报 PDF 省略，因 textual 已用真实年报验证）。
- 真实数据先用缩减样本（随机 200 家）验证，再全量；报告注明缩减比例与原因（AGENTS.md §6）。
- 测试报告写入 `tests/reports/<YYYY-MM-DD-HH-mm>.report-<n>.md`。

## 6. 风险与限制

| 风险 | 后果 | 缓解 |
| --- | --- | --- |
| 数据下载进度慢 | 10 Nov 里程碑缺真数据 | 管线与真实数据解耦，demo 先行 |
| 年报 PDF 扫描件/标题变体 | MD&A 提取失败 | 失败计数并逐项报告（大纲要求） |
| 子行业-年份组稀疏 | 组内标准化不稳 | 已定 fallback：组内样本不足时退全样本标准化 |
| 组员 4 人 vs 规定 ≤3 | 教授判罚风险 | 已告知用户，需与教授确认（用户负责） |
| 词典版权 | 不可引用 | 只用公开发表词表并注明版本 |
| 系统 Python 3.4.4 | 无法运行新库 | 用 bundled Python 3.12.14 建 .venv |

## 7. 预计文件清单

- 新增：src/、scripts/、tests/、outputs/、docs/、data/ 目录下全部文件，requirements.txt、README.md、本计划书。
- 修改：无（现有 docx/xlsx 只读引用，不改动原文）。
- 删除：check_sheet_extent.js、dump_outline_text.js（临时文档读取工具，完成论文读取后清理）。

## 8. 规则遵守

- 新增文件默认简体中文；论文本体保持已有英文（英式拼写）不变。
- 程序文件含 banner（文件名 / 作者 "Group12A2 DSW Team" / 用途 / 模块）与 revision history。
- 建议初始化 git 仓库便于回滚与同步（当前非 git；是否执行待用户确认）。
