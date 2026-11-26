# Strict t+1 event timing and v0.1 lexicon control

## Part 1 - disclosure-date gated t+1 labels

The original label counts an announcement as forward-looking when its
calendar year equals fiscal year + 1. The strict label also requires the
announcement date to fall strictly after the annual-report disclosure date
of fiscal year t (within 365 days).

| Label | Loose n | Strict n | Dropped | Share dropped |
| --- | --- | --- | --- | --- |
| violation_any_t1_strict | 1,965 | 1,543 | 422 | 21.5% |
| violation_disclosure_t1_strict | 1,337 | 1,040 | 297 | 22.2% |

Firm-years without a usable disclosure date keep no strict label and are
counted in the diagnostics table: 1 rows.

### Ranking quality on the strict labels

| Label | Score | AUC [95% CI] | Lift top-10% [95% CI] |
| --- | --- | --- | --- |
| mod_opinion | finance-only IF | 0.805 [0.778, 0.836] | 5.00 [4.27, 5.60] |
| mod_opinion | text-only IF | 0.513 [0.471, 0.551] | 0.98 [0.57, 1.39] |
| mod_opinion | fused IF | 0.767 [0.733, 0.799] | 4.56 [3.91, 5.17] |
| mod_opinion | fused AE | 0.686 [0.648, 0.729] | 3.19 [2.56, 3.88] |
| mod_opinion | Beneish M-Score | 0.242 [0.200, 0.281] | 0.64 [0.35, 0.96] |
| mod_opinion_wide | finance-only IF | 0.785 [0.757, 0.812] | 4.68 [4.12, 5.17] |
| mod_opinion_wide | text-only IF | 0.524 [0.492, 0.554] | 1.10 [0.76, 1.42] |
| mod_opinion_wide | fused IF | 0.757 [0.729, 0.783] | 4.39 [3.94, 4.90] |
| mod_opinion_wide | fused AE | 0.677 [0.644, 0.707] | 3.27 [2.77, 3.72] |
| mod_opinion_wide | Beneish M-Score | 0.276 [0.247, 0.312] | 0.73 [0.48, 1.01] |
| violation_any_t1_strict | finance-only IF | 0.583 [0.567, 0.597] | 1.87 [1.71, 2.04] |
| violation_any_t1_strict | text-only IF | 0.501 [0.485, 0.515] | 0.92 [0.80, 1.06] |
| violation_any_t1_strict | fused IF | 0.570 [0.554, 0.586] | 1.74 [1.59, 1.91] |
| violation_any_t1_strict | fused AE | 0.556 [0.540, 0.570] | 1.64 [1.47, 1.77] |
| violation_any_t1_strict | Beneish M-Score | 0.432 [0.414, 0.447] | 0.93 [0.79, 1.07] |
| violation_disclosure_t1_strict | finance-only IF | 0.603 [0.586, 0.622] | 2.12 [1.90, 2.36] |
| violation_disclosure_t1_strict | text-only IF | 0.508 [0.488, 0.523] | 0.96 [0.79, 1.14] |
| violation_disclosure_t1_strict | fused IF | 0.590 [0.572, 0.609] | 1.97 [1.79, 2.19] |
| violation_disclosure_t1_strict | fused AE | 0.567 [0.549, 0.588] | 1.75 [1.55, 1.97] |
| violation_disclosure_t1_strict | Beneish M-Score | 0.413 [0.394, 0.436] | 0.90 [0.74, 1.07] |
| violation_any_t1_loose | finance-only IF | 0.573 [0.557, 0.586] | 1.71 [1.59, 1.86] |
| violation_any_t1_loose | text-only IF | 0.494 [0.479, 0.506] | 0.90 [0.80, 1.02] |
| violation_any_t1_loose | fused IF | 0.557 [0.541, 0.572] | 1.58 [1.47, 1.72] |
| violation_any_t1_loose | fused AE | 0.546 [0.533, 0.561] | 1.48 [1.33, 1.61] |
| violation_any_t1_loose | Beneish M-Score | 0.425 [0.409, 0.438] | 0.87 [0.74, 0.99] |
| violation_disclosure_t1_loose | finance-only IF | 0.598 [0.582, 0.614] | 2.02 [1.84, 2.20] |
| violation_disclosure_t1_loose | text-only IF | 0.499 [0.482, 0.513] | 0.93 [0.78, 1.07] |
| violation_disclosure_t1_loose | fused IF | 0.581 [0.565, 0.598] | 1.88 [1.72, 2.07] |
| violation_disclosure_t1_loose | fused AE | 0.561 [0.545, 0.578] | 1.62 [1.46, 1.78] |
| violation_disclosure_t1_loose | Beneish M-Score | 0.407 [0.389, 0.425] | 0.85 [0.69, 1.00] |

### Supervised comparison on the strict labels

| Label | Model | Feature set | OOF AUC [95% CI] |
| --- | --- | --- | --- |
| mod_opinion | logit | finance | +0.865 [+0.835, +0.895] |
| mod_opinion | logit | text | +0.680 [+0.646, +0.723] |
| mod_opinion | logit | fused | +0.866 [+0.835, +0.899] |
| mod_opinion | hgb | finance | +0.861 [+0.833, +0.888] |
| mod_opinion | hgb | text | +0.613 [+0.577, +0.652] |
| mod_opinion | hgb | fused | +0.873 [+0.848, +0.898] |
| mod_opinion | logit | delta_fused_vs_finance | +0.002 [-0.013, +0.014] |
| mod_opinion | logit | delta_text_vs_finance | -0.184 [-0.232, -0.138] |
| mod_opinion | hgb | delta_fused_vs_finance | +0.012 [-0.005, +0.027] |
| mod_opinion | hgb | delta_text_vs_finance | -0.248 [-0.295, -0.204] |
| mod_opinion_wide | logit | finance | +0.807 [+0.782, +0.830] |
| mod_opinion_wide | logit | text | +0.663 [+0.635, +0.693] |
| mod_opinion_wide | logit | fused | +0.815 [+0.791, +0.837] |
| mod_opinion_wide | hgb | finance | +0.844 [+0.820, +0.867] |
| mod_opinion_wide | hgb | text | +0.605 [+0.575, +0.639] |
| mod_opinion_wide | hgb | fused | +0.851 [+0.829, +0.871] |
| mod_opinion_wide | logit | delta_fused_vs_finance | +0.008 [-0.006, +0.019] |
| mod_opinion_wide | logit | delta_text_vs_finance | -0.144 [-0.182, -0.111] |
| mod_opinion_wide | hgb | delta_fused_vs_finance | +0.007 [-0.006, +0.017] |
| mod_opinion_wide | hgb | delta_text_vs_finance | -0.240 [-0.276, -0.208] |
| violation_any_t1_strict | logit | finance | +0.637 [+0.621, +0.651] |
| violation_any_t1_strict | logit | text | +0.569 [+0.554, +0.585] |
| violation_any_t1_strict | logit | fused | +0.641 [+0.624, +0.656] |
| violation_any_t1_strict | hgb | finance | +0.648 [+0.632, +0.667] |
| violation_any_t1_strict | hgb | text | +0.528 [+0.512, +0.544] |
| violation_any_t1_strict | hgb | fused | +0.655 [+0.639, +0.671] |
| violation_any_t1_strict | logit | delta_fused_vs_finance | +0.004 [-0.004, +0.010] |
| violation_any_t1_strict | logit | delta_text_vs_finance | -0.068 [-0.090, -0.046] |
| violation_any_t1_strict | hgb | delta_fused_vs_finance | +0.007 [-0.002, +0.017] |
| violation_any_t1_strict | hgb | delta_text_vs_finance | -0.120 [-0.141, -0.098] |
| violation_disclosure_t1_strict | logit | finance | +0.666 [+0.646, +0.684] |
| violation_disclosure_t1_strict | logit | text | +0.566 [+0.548, +0.586] |
| violation_disclosure_t1_strict | logit | fused | +0.664 [+0.644, +0.682] |
| violation_disclosure_t1_strict | hgb | finance | +0.674 [+0.656, +0.691] |
| violation_disclosure_t1_strict | hgb | text | +0.522 [+0.503, +0.541] |
| violation_disclosure_t1_strict | hgb | fused | +0.673 [+0.654, +0.690] |
| violation_disclosure_t1_strict | logit | delta_fused_vs_finance | -0.002 [-0.011, +0.005] |
| violation_disclosure_t1_strict | logit | delta_text_vs_finance | -0.100 [-0.126, -0.072] |
| violation_disclosure_t1_strict | hgb | delta_fused_vs_finance | -0.001 [-0.011, +0.009] |
| violation_disclosure_t1_strict | hgb | delta_text_vs_finance | -0.152 [-0.176, -0.126] |

### Reading

- The fused score on the strict disclosure label reaches AUC 0.590 [0.572, 0.609].

Rows marked `delta_*_vs_finance` are paired AUC differences against the
finance-only baseline; an interval covering zero means no detectable extra
rank information.
