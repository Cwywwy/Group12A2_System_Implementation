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
| mod_opinion | finance-only IF | 0.802 [0.774, 0.833] | 4.95 [4.29, 5.57] |
| mod_opinion | text-only IF | 0.520 [0.478, 0.557] | 0.98 [0.53, 1.36] |
| mod_opinion | fused IF | 0.769 [0.734, 0.801] | 4.56 [3.92, 5.24] |
| mod_opinion | fused AE | 0.690 [0.651, 0.735] | 3.43 [2.85, 4.08] |
| mod_opinion | Beneish M-Score | 0.242 [0.200, 0.281] | 0.64 [0.35, 0.96] |
| mod_opinion_wide | finance-only IF | 0.781 [0.753, 0.810] | 4.62 [4.11, 5.10] |
| mod_opinion_wide | text-only IF | 0.530 [0.496, 0.560] | 1.15 [0.79, 1.47] |
| mod_opinion_wide | fused IF | 0.759 [0.730, 0.785] | 4.25 [3.78, 4.74] |
| mod_opinion_wide | fused AE | 0.678 [0.646, 0.710] | 3.46 [2.95, 3.88] |
| mod_opinion_wide | Beneish M-Score | 0.276 [0.247, 0.312] | 0.73 [0.48, 1.01] |
| violation_any_t1_strict | finance-only IF | 0.581 [0.564, 0.595] | 1.87 [1.71, 2.03] |
| violation_any_t1_strict | text-only IF | 0.504 [0.489, 0.518] | 0.93 [0.80, 1.06] |
| violation_any_t1_strict | fused IF | 0.570 [0.553, 0.585] | 1.74 [1.58, 1.90] |
| violation_any_t1_strict | fused AE | 0.554 [0.538, 0.569] | 1.57 [1.40, 1.71] |
| violation_any_t1_strict | Beneish M-Score | 0.432 [0.414, 0.447] | 0.93 [0.79, 1.07] |
| violation_disclosure_t1_strict | finance-only IF | 0.600 [0.584, 0.619] | 2.12 [1.90, 2.34] |
| violation_disclosure_t1_strict | text-only IF | 0.512 [0.492, 0.527] | 0.97 [0.79, 1.12] |
| violation_disclosure_t1_strict | fused IF | 0.590 [0.574, 0.611] | 1.98 [1.77, 2.17] |
| violation_disclosure_t1_strict | fused AE | 0.564 [0.546, 0.584] | 1.69 [1.49, 1.89] |
| violation_disclosure_t1_strict | Beneish M-Score | 0.413 [0.394, 0.436] | 0.90 [0.74, 1.07] |
| violation_any_t1_loose | finance-only IF | 0.570 [0.555, 0.584] | 1.70 [1.58, 1.84] |
| violation_any_t1_loose | text-only IF | 0.497 [0.483, 0.510] | 0.91 [0.79, 1.01] |
| violation_any_t1_loose | fused IF | 0.557 [0.542, 0.572] | 1.60 [1.47, 1.73] |
| violation_any_t1_loose | fused AE | 0.544 [0.529, 0.559] | 1.42 [1.28, 1.55] |
| violation_any_t1_loose | Beneish M-Score | 0.425 [0.409, 0.438] | 0.87 [0.74, 0.99] |
| violation_disclosure_t1_loose | finance-only IF | 0.596 [0.580, 0.611] | 2.01 [1.85, 2.18] |
| violation_disclosure_t1_loose | text-only IF | 0.503 [0.486, 0.516] | 0.93 [0.77, 1.06] |
| violation_disclosure_t1_loose | fused IF | 0.582 [0.566, 0.599] | 1.89 [1.71, 2.06] |
| violation_disclosure_t1_loose | fused AE | 0.557 [0.541, 0.576] | 1.56 [1.40, 1.75] |
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

- The fused score on the strict disclosure label reaches AUC 0.590 [0.574, 0.611].

Rows marked `delta_*_vs_finance` are paired AUC differences against the
finance-only baseline; an interval covering zero means no detectable extra
rank information.

## Part 2 - v0.1 lexicon control on the repaired financial data

Both variants are fitted on the same 9,239 firm-years with the
same six financial features, the same preprocessing and the same Isolation
Forest settings; only the three text features change (current dictionary
versus the archived v0.1 values).

| Text measurement | Text-only rho | Text-only calibrated lift-10% | Fused rho | Fused calibrated lift-10% |
| --- | --- | --- | --- | --- |
| Current dictionary | -0.026 | 0.91 | -0.018 | 2.10 |
| v0.1 dictionary | -0.048 | 1.04 | -0.021 | 2.19 |

Top-decile overlap between the two text rankings: 0.584;
between the two fused rankings: 0.846.

Corpus check: the archived and the current text features agree on the token
count for 0.2% of the shared rows, with
correlations of 1.000 (readability), 0.615 (sentiment) and
0.847 (uncertainty).

Reading: the text block stays close to uncorrelated with the Beneish proxy
under either dictionary, so the near-zero text correlation in the main
results is not an artefact of the dictionary upgrade; the movement documented
in the appendix came from the financial-data repair and the benchmark change,
not from the lexicon.
