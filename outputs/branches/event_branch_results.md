# External-outcome evaluation (branch 3)

Event labels: modified audit opinions for fiscal year t (narrow = qualified,
disclaimer or adverse; wide adds the explanatory-paragraph cases) and CSMAR
violation announcements dated in fiscal year t+1 (any violation, and the
disclosure-related subset: delayed disclosure, misstatement, material
omission, fictitious profit or assets). Scores are used as risk rankings;
AUC and top-queue enrichment carry bootstrap 95% intervals.

## Headline findings

- The finance-only Isolation Forest score ranks firms with a modified audit
  opinion well above chance: AUC 0.640 [0.604, 0.677], with 1.91x enrichment and 9.6% of all events in the top-5% queue.
- The text-only score is close to chance for the same label (AUC 0.524 [0.481, 0.568]).
- The Beneish M-Score is *anti-correlated* with real modified opinions: AUC 0.405 [0.351, 0.458], i.e. the proxy benchmark used in the first specification is not merely noisy, it points the wrong way for this sample.
- Under firm-grouped cross validation the fused model beats the finance-only model in 8 of 8 label-by-model combinations and the bootstrap interval excludes zero in 5 of them; every point estimate is non-negative.

## Ranking quality of the existing scores

| Label | Score | AUC [95% CI] | PR-AUC | Lift top-10% [95% CI] |
| --- | --- | --- | --- | --- |
| mod_opinion | finance-only IF | 0.640 [0.604, 0.677] | 0.037 | 2.18 [1.60, 2.74] |
| mod_opinion | text-only IF | 0.524 [0.481, 0.568] | 0.026 | 1.06 [0.69, 1.50] |
| mod_opinion | fused IF | 0.618 [0.576, 0.656] | 0.035 | 1.97 [1.39, 2.58] |
| mod_opinion | fused AE | 0.471 [0.427, 0.509] | 0.021 | 0.90 [0.56, 1.26] |
| mod_opinion | Beneish M-Score | 0.405 [0.351, 0.458] | 0.021 | 1.33 [0.87, 1.79] |
| mod_opinion_wide | finance-only IF | 0.660 [0.629, 0.686] | 0.070 | 2.11 [1.70, 2.51] |
| mod_opinion_wide | text-only IF | 0.527 [0.493, 0.563] | 0.047 | 1.13 [0.82, 1.49] |
| mod_opinion_wide | fused IF | 0.633 [0.599, 0.663] | 0.068 | 2.08 [1.67, 2.53] |
| mod_opinion_wide | fused AE | 0.491 [0.462, 0.523] | 0.041 | 1.13 [0.84, 1.45] |
| mod_opinion_wide | Beneish M-Score | 0.419 [0.380, 0.456] | 0.037 | 1.25 [0.92, 1.60] |
| violation_any_t1 | finance-only IF | 0.530 [0.516, 0.545] | 0.239 | 1.22 [1.08, 1.35] |
| violation_any_t1 | text-only IF | 0.492 [0.478, 0.507] | 0.211 | 0.89 [0.79, 1.01] |
| violation_any_t1 | fused IF | 0.520 [0.506, 0.536] | 0.233 | 1.14 [1.02, 1.27] |
| violation_any_t1 | fused AE | 0.488 [0.473, 0.503] | 0.209 | 0.97 [0.85, 1.08] |
| violation_any_t1 | Beneish M-Score | 0.482 [0.468, 0.499] | 0.214 | 1.06 [0.95, 1.20] |
| violation_disclosure_t1 | finance-only IF | 0.549 [0.532, 0.566] | 0.170 | 1.27 [1.11, 1.43] |
| violation_disclosure_t1 | text-only IF | 0.500 [0.483, 0.517] | 0.146 | 0.93 [0.78, 1.08] |
| violation_disclosure_t1 | fused IF | 0.533 [0.517, 0.553] | 0.165 | 1.22 [1.07, 1.39] |
| violation_disclosure_t1 | fused AE | 0.484 [0.466, 0.501] | 0.141 | 0.94 [0.78, 1.09] |
| violation_disclosure_t1 | Beneish M-Score | 0.475 [0.458, 0.492] | 0.143 | 0.99 [0.85, 1.17] |

## Supervised comparison under firm-grouped cross validation

| Label | Model | Feature set | OOF AUC [95% CI] |
| --- | --- | --- | --- |
| mod_opinion | logit | finance | +0.778 [+0.740, +0.816] |
| mod_opinion | logit | text | +0.685 [+0.648, +0.724] |
| mod_opinion | logit | fused | +0.799 [+0.765, +0.832] |
| mod_opinion | hgb | finance | +0.746 [+0.704, +0.784] |
| mod_opinion | hgb | text | +0.590 [+0.551, +0.631] |
| mod_opinion | hgb | fused | +0.772 [+0.736, +0.807] |
| mod_opinion | logit | delta_fused_vs_finance | +0.020 [-0.002, +0.043] |
| mod_opinion | logit | delta_text_vs_finance | -0.094 [-0.140, -0.045] |
| mod_opinion | hgb | delta_fused_vs_finance | +0.026 [+0.002, +0.049] |
| mod_opinion | hgb | delta_text_vs_finance | -0.156 [-0.207, -0.098] |
| mod_opinion_wide | logit | finance | +0.713 [+0.682, +0.746] |
| mod_opinion_wide | logit | text | +0.665 [+0.638, +0.696] |
| mod_opinion_wide | logit | fused | +0.745 [+0.716, +0.772] |
| mod_opinion_wide | hgb | finance | +0.790 [+0.762, +0.820] |
| mod_opinion_wide | hgb | text | +0.606 [+0.575, +0.636] |
| mod_opinion_wide | hgb | fused | +0.799 [+0.773, +0.827] |
| mod_opinion_wide | logit | delta_fused_vs_finance | +0.032 [+0.012, +0.051] |
| mod_opinion_wide | logit | delta_text_vs_finance | -0.048 [-0.093, -0.004] |
| mod_opinion_wide | hgb | delta_fused_vs_finance | +0.009 [-0.008, +0.026] |
| mod_opinion_wide | hgb | delta_text_vs_finance | -0.184 [-0.228, -0.143] |
| violation_any_t1 | logit | finance | +0.582 [+0.568, +0.597] |
| violation_any_t1 | logit | text | +0.568 [+0.553, +0.583] |
| violation_any_t1 | logit | fused | +0.602 [+0.587, +0.616] |
| violation_any_t1 | hgb | finance | +0.612 [+0.598, +0.625] |
| violation_any_t1 | hgb | text | +0.537 [+0.523, +0.551] |
| violation_any_t1 | hgb | fused | +0.627 [+0.611, +0.639] |
| violation_any_t1 | logit | delta_fused_vs_finance | +0.020 [+0.010, +0.029] |
| violation_any_t1 | logit | delta_text_vs_finance | -0.013 [-0.033, +0.007] |
| violation_any_t1 | hgb | delta_fused_vs_finance | +0.015 [+0.004, +0.025] |
| violation_any_t1 | hgb | delta_text_vs_finance | -0.075 [-0.094, -0.056] |
| violation_disclosure_t1 | logit | finance | +0.606 [+0.588, +0.624] |
| violation_disclosure_t1 | logit | text | +0.569 [+0.554, +0.587] |
| violation_disclosure_t1 | logit | fused | +0.620 [+0.605, +0.638] |
| violation_disclosure_t1 | hgb | finance | +0.642 [+0.625, +0.659] |
| violation_disclosure_t1 | hgb | text | +0.533 [+0.515, +0.550] |
| violation_disclosure_t1 | hgb | fused | +0.649 [+0.632, +0.668] |
| violation_disclosure_t1 | logit | delta_fused_vs_finance | +0.014 [+0.003, +0.024] |
| violation_disclosure_t1 | logit | delta_text_vs_finance | -0.037 [-0.062, -0.011] |
| violation_disclosure_t1 | hgb | delta_fused_vs_finance | +0.006 [-0.004, +0.019] |
| violation_disclosure_t1 | hgb | delta_text_vs_finance | -0.109 [-0.135, -0.084] |

`delta_*_vs_finance` rows are AUC differences against the finance-only
baseline; an interval that covers zero means the extra feature block adds
no detectable rank information for that event.

## How to read this

- The audit-opinion label is contemporaneous with the fiscal year (the report
  for year t carries the opinion for year t), so it measures identification of
  risky disclosures rather than forecasting. The violation label is strictly
  forward-looking (announcements dated in t+1), which is why it is the harder
  and more honest predictive test - and the one where all scores are weakest.
- Modified opinions are rare (2.3%), so PR-AUC stays close to the base rate even
  for a useful ranking; AUC and top-queue enrichment are the informative metrics.
- Violation announcements mix disclosure problems with share-trading and other
  violations, which dilutes signal; the disclosure subset is cleaner but still
  driven by regulator capacity and media attention rather than by the accounts.
