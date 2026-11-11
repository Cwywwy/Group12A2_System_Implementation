# 分支调研 · Branch studies

为寻找阳性结果而做的四条支线，全部保留下结论与数据出处，便于答辩时说明「为什么不继续」。
Four side studies exploring whether a positive result is reachable, kept together with their verdicts.

| 文件 · File | 分支 · Branch | 结论 · Verdict |
| --- | --- | --- |
| `positive_result_branches.md` | 换真实结果变量的七条路线 · seven candidate outcome variables | t+1 问询函首选；非标审计意见兜底；重述/处罚备选 |
| `branch_component_correlations.csv` | 分支 1：把 Beneish M-Score 拆成八个分量再做秩相关 · component-level probe | 文本对任一分量 \\|ρ\\| ≤ 0.064 → 「基准太粗」被排除 |
| `branch2_inquiry_crawler_spec.md` | 分支 2：年报问询函自建爬虫评估 · inquiry-letter crawler spec | 深交所最干净；沪市须靠巨潮补；4.5–5 人日；有降级方案 |
| `event_branch_results.md` | 分支 3：真实监管事件（已升格为论文 §5.7）· real regulatory outcomes | 财务 AUC 0.640、前 10% 富集 2.18×；Beneish 仅 0.405 |

分支 3 的数据与代码已进入主流程：`data/processed/event_table.csv`、`src/data_ingestion/event_parser.py`、
`src/evaluation/event_eval.py`、`scripts/run_03b_build_event_table.py`、`scripts/run_07b_event_models.py`。
