# 第一版结果归档 · v0.1 results archive

第一版（v0.1）在引导词典 + 子串计数 + 单一 `M > -1.78` 基准下的结果表与图表。
Results of the first specification (bootstrap lexicon, substring counting, a single M > -1.78 cut-off).

| 路径 · Path | 内容 · Contents |
| --- | --- |
| `tables/` | v0.1 全套结果表：`model_metrics.csv`、`topk_metrics.csv`、`ranking_overlap.csv`、SHAP 三表、`anomaly_scores.csv`。论文 §5.6 的 Table 5.4 从这里读数（`scripts/build_section5.py` 的 `V01_TABLES`）。 |
| `prev_run/` | 最早一轮的图表与摘要（topk 表尚未含 benchmark 列），`scripts/compare_runs.py` 的默认 `--old`。 |

两版对比 · compare the two specifications:

```powershell
& ".venv\Scripts\python.exe" "scripts/compare_runs.py" --old "outputs/archive_v0.1/tables" --new "outputs/tables"
```
