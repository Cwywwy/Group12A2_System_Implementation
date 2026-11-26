# External-outcome evaluation (branch 3)

Event labels: modified audit opinions for fiscal year t (narrow = qualified,
disclaimer or adverse; wide adds the explanatory-paragraph cases) and CSMAR
violation announcements dated in fiscal year t+1 (any violation, and the
disclosure-related subset: delayed disclosure, misstatement, material
omission, fictitious profit or assets). Scores are used as risk rankings;
AUC and top-queue enrichment carry bootstrap 95% intervals.

## Headline findings

- The finance-only Isolation Forest score ranks firms with a modified audit
  opinion well above chance: AUC 0.787 [0.762, 0.809], with 6.59x enrichment and 32.9% of all events in the top-5% queue.
- The text-only score is close to chance for the same label (AUC 0.524 [0.488, 0.556]).
- The Beneish M-Score is *anti-correlated* with real modified opinions: AUC 0.263 [0.233, 0.298], i.e. the proxy benchmark used in the first specification is not merely noisy, it points the wrong way for this sample.
- Under firm-grouped cross validation the fused model beats the finance-only model in 7 of 8 label-by-model combinations and the bootstrap interval excludes zero in 0 of them; every point estimate is non-negative.

## Ranking quality of the existing scores

| Label | Score | AUC [95% CI] | PR-AUC | Lift top-10% [95% CI] |
| --- | --- | --- | --- | --- |
| mod_opinion | finance-only IF | 0.787 [0.762, 0.809] | 0.096 | 4.72 [4.22, 5.28] |
| mod_opinion | text-only IF | 0.524 [0.488, 0.556] | 0.022 | 1.15 [0.85, 1.50] |
| mod_opinion | fused IF | 0.759 [0.729, 0.787] | 0.097 | 4.60 [4.17, 5.12] |
| mod_opinion | fused AE | 0.696 [0.663, 0.723] | 0.061 | 3.26 [2.76, 3.73] |
| mod_opinion | Beneish M-Score | 0.263 [0.233, 0.298] | 0.015 | 0.65 [0.40, 0.94] |
| mod_opinion_wide | finance-only IF | 0.786 [0.768, 0.804] | 0.174 | 4.54 [4.17, 4.95] |
| mod_opinion_wide | text-only IF | 0.522 [0.496, 0.549] | 0.040 | 1.13 [0.89, 1.40] |
| mod_opinion_wide | fused IF | 0.762 [0.740, 0.782] | 0.172 | 4.49 [4.12, 4.87] |
| mod_opinion_wide | fused AE | 0.698 [0.670, 0.720] | 0.119 | 3.34 [2.99, 3.69] |
| mod_opinion_wide | Beneish M-Score | 0.288 [0.266, 0.316] | 0.029 | 0.79 [0.59, 1.02] |
| violation_any_t1 | finance-only IF | 0.573 [0.557, 0.586] | 0.289 | 1.71 [1.59, 1.86] |
| violation_any_t1 | text-only IF | 0.494 [0.479, 0.506] | 0.207 | 0.90 [0.80, 1.02] |
| violation_any_t1 | fused IF | 0.557 [0.541, 0.572] | 0.276 | 1.58 [1.47, 1.72] |
| violation_any_t1 | fused AE | 0.546 [0.533, 0.561] | 0.262 | 1.48 [1.33, 1.61] |
| violation_any_t1 | Beneish M-Score | 0.425 [0.409, 0.438] | 0.188 | 0.87 [0.74, 0.99] |
| violation_disclosure_t1 | finance-only IF | 0.598 [0.582, 0.614] | 0.228 | 2.02 [1.84, 2.20] |
| violation_disclosure_t1 | text-only IF | 0.499 [0.482, 0.513] | 0.143 | 0.93 [0.78, 1.07] |
| violation_disclosure_t1 | fused IF | 0.581 [0.565, 0.598] | 0.217 | 1.88 [1.72, 2.07] |
| violation_disclosure_t1 | fused AE | 0.561 [0.545, 0.578] | 0.195 | 1.62 [1.46, 1.78] |
| violation_disclosure_t1 | Beneish M-Score | 0.407 [0.389, 0.425] | 0.124 | 0.85 [0.69, 1.00] |

## Supervised comparison under firm-grouped cross validation

| Label | Model | Feature set | OOF AUC [95% CI] |
| --- | --- | --- | --- |
| mod_opinion | logit | finance | +0.865 [+0.842, +0.884] |
| mod_opinion | logit | text | +0.640 [+0.605, +0.673] |
| mod_opinion | logit | fused | +0.864 [+0.841, +0.885] |
| mod_opinion | hgb | finance | +0.859 [+0.837, +0.880] |
| mod_opinion | hgb | text | +0.612 [+0.576, +0.646] |
| mod_opinion | hgb | fused | +0.863 [+0.840, +0.882] |
| mod_opinion | logit | delta_fused_vs_finance | -0.000 [-0.009, +0.007] |
| mod_opinion | logit | delta_text_vs_finance | -0.225 [-0.259, -0.188] |
| mod_opinion | hgb | delta_fused_vs_finance | +0.004 [-0.002, +0.011] |
| mod_opinion | hgb | delta_text_vs_finance | -0.247 [-0.280, -0.207] |
| mod_opinion_wide | logit | finance | +0.822 [+0.802, +0.839] |
| mod_opinion_wide | logit | text | +0.636 [+0.613, +0.660] |
| mod_opinion_wide | logit | fused | +0.828 [+0.808, +0.847] |
| mod_opinion_wide | hgb | finance | +0.861 [+0.843, +0.876] |
| mod_opinion_wide | hgb | text | +0.599 [+0.574, +0.624] |
| mod_opinion_wide | hgb | fused | +0.863 [+0.845, +0.878] |
| mod_opinion_wide | logit | delta_fused_vs_finance | +0.006 [-0.001, +0.013] |
| mod_opinion_wide | logit | delta_text_vs_finance | -0.186 [-0.216, -0.159] |
| mod_opinion_wide | hgb | delta_fused_vs_finance | +0.002 [-0.004, +0.008] |
| mod_opinion_wide | hgb | delta_text_vs_finance | -0.262 [-0.291, -0.232] |
| violation_any_t1 | logit | finance | +0.637 [+0.622, +0.651] |
| violation_any_t1 | logit | text | +0.567 [+0.552, +0.583] |
| violation_any_t1 | logit | fused | +0.640 [+0.625, +0.654] |
| violation_any_t1 | hgb | finance | +0.640 [+0.626, +0.655] |
| violation_any_t1 | hgb | text | +0.525 [+0.511, +0.539] |
| violation_any_t1 | hgb | fused | +0.647 [+0.633, +0.662] |
| violation_any_t1 | logit | delta_fused_vs_finance | +0.003 [-0.004, +0.010] |
| violation_any_t1 | logit | delta_text_vs_finance | -0.070 [-0.089, -0.051] |
| violation_any_t1 | hgb | delta_fused_vs_finance | +0.007 [-0.002, +0.016] |
| violation_any_t1 | hgb | delta_text_vs_finance | -0.115 [-0.136, -0.095] |
| violation_disclosure_t1 | logit | finance | +0.672 [+0.654, +0.689] |
| violation_disclosure_t1 | logit | text | +0.570 [+0.553, +0.588] |
| violation_disclosure_t1 | logit | fused | +0.673 [+0.655, +0.689] |
| violation_disclosure_t1 | hgb | finance | +0.671 [+0.655, +0.688] |
| violation_disclosure_t1 | hgb | text | +0.526 [+0.513, +0.544] |
| violation_disclosure_t1 | hgb | fused | +0.679 [+0.664, +0.696] |
| violation_disclosure_t1 | logit | delta_fused_vs_finance | +0.001 [-0.005, +0.007] |
| violation_disclosure_t1 | logit | delta_text_vs_finance | -0.102 [-0.126, -0.078] |
| violation_disclosure_t1 | hgb | delta_fused_vs_finance | +0.008 [-0.002, +0.016] |
| violation_disclosure_t1 | hgb | delta_text_vs_finance | -0.145 [-0.169, -0.122] |

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
