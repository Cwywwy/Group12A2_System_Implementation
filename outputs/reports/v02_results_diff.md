# v0.1 → v0.2 结果差异报告（换词典 + 双基准）

生成时间：2026-11-11 04:27
对比对象：文本特征 v0.1（引导词典、子串计数） → v0.2（姚加权等 2021 正式词表、jieba 词元匹配）
数据来源：`outputs/.tmp/v01_dual_benchmark/tables`（旧）与 `outputs/tables`（新）
生成命令：`.venv\Scripts\python.exe scripts\compare_runs.py --old ... --new ...`

> 结论：换词典后阴性结论不变，且可以排除"词表太薄"这一解释；数字层面对比见下。

```old = outputs\.tmp\v01_dual_benchmark\tables (v0.1 bootstrap lexicon)
new = outputs\tables (v0.2 Yao2021 lexicon)

Sample (v0.1 bootstrap lexicon -> v0.2 Yao2021 lexicon)
-------------------------------------------------------
firm-years        8,140 -> 8,140
firms             3,265 -> 3,265
legacy flag rate  0.628 -> 0.628 (+0.000)
decile cut-off    16.52 -> 16.52 (+0.00)

Spearman rho against the Beneish M-Score
----------------------------------------
Finance-only IF      rho 0.136 -> 0.136 (+0.000)   p < 0.001 -> < 0.001
Text-only IF         rho -0.030 -> -0.029 (+0.000)   p 0.008 -> 0.008
Fused IF             rho 0.103 -> 0.103 (+0.001)   p < 0.001 -> < 0.001
Fused autoencoder    rho 0.012 -> 0.009 (-0.003)   p 0.272 -> 0.409

Top-k enrichment (calibrated benchmark, M top-10%)
--------------------------------------------------
[calibrated]
  Finance-only IF      k=5%  enrichment 2.555 -> 2.555 (+0.000)
  Finance-only IF      k=10%  enrichment 1.867 -> 1.867 (+0.000)
  Finance-only IF      k=15%  enrichment 1.638 -> 1.638 (+0.000)
  Text-only IF         k=5%  enrichment 1.106 -> 0.909 (-0.197)
  Text-only IF         k=10%  enrichment 1.069 -> 0.848 (-0.221)
  Text-only IF         k=15%  enrichment 1.040 -> 0.893 (-0.147)
  Fused IF             k=5%  enrichment 2.555 -> 2.727 (+0.172)
  Fused IF             k=10%  enrichment 1.904 -> 1.843 (-0.061)
  Fused IF             k=15%  enrichment 1.572 -> 1.532 (-0.041)
  Fused autoencoder    k=5%  enrichment 1.425 -> 1.376 (-0.049)
  Fused autoencoder    k=10%  enrichment 1.253 -> 1.253 (+0.000)
  Fused autoencoder    k=15%  enrichment 1.155 -> 1.155 (+0.000)
[legacy]
  Finance-only IF      k=5%  enrichment 1.370 -> 1.370 (+0.000)
  Finance-only IF      k=10%  enrichment 1.217 -> 1.217 (+0.000)
  Finance-only IF      k=15%  enrichment 1.168 -> 1.168 (+0.000)
  Text-only IF         k=5%  enrichment 0.896 -> 0.845 (-0.051)
  Text-only IF         k=10%  enrichment 0.914 -> 0.922 (+0.008)
  Text-only IF         k=15%  enrichment 0.942 -> 0.935 (-0.007)
  Fused IF             k=5%  enrichment 1.331 -> 1.346 (+0.016)
  Fused IF             k=10%  enrichment 1.176 -> 1.198 (+0.022)
  Fused IF             k=15%  enrichment 1.134 -> 1.135 (+0.001)
  Fused autoencoder    k=5%  enrichment 1.010 -> 1.006 (-0.004)
  Fused autoencoder    k=10%  enrichment 0.996 -> 0.994 (-0.002)
  Fused autoencoder    k=15%  enrichment 0.988 -> 0.989 (+0.001)

SHAP group shares
-----------------
finance  0.659 -> 0.654 (-0.004)
text     0.341 -> 0.346 (+0.004)

Ranking overlap (top-10% Jaccard)
---------------------------------
if_finance   vs if_text      0.120 -> 0.111 (-0.010)
if_finance   vs if_fused     0.828 -> 0.817 (-0.011)
if_finance   vs ae_fused     0.369 -> 0.373 (+0.005)
if_text      vs if_finance   0.120 -> 0.111 (-0.010)
if_text      vs if_fused     0.264 -> 0.256 (-0.009)
if_text      vs ae_fused     0.155 -> 0.147 (-0.007)
if_fused     vs if_finance   0.828 -> 0.817 (-0.011)
if_fused     vs if_text      0.264 -> 0.256 (-0.009)
if_fused     vs ae_fused     0.367 -> 0.362 (-0.005)
ae_fused     vs if_finance   0.369 -> 0.373 (+0.005)
ae_fused     vs if_text      0.155 -> 0.147 (-0.007)
ae_fused     vs if_fused     0.367 -> 0.362 (-0.005)

Top-ranked firm-year
--------------------
v0.1 bootstrap lexicon: 000820 (2021) score 0.767 M-Score 1077.5
v0.2 Yao2021 lexicon: 000820 (2021) score 0.759 M-Score 1077.5

