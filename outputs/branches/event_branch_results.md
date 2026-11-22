# External-outcome evaluation (branch 3)

Event labels: modified audit opinions for fiscal year t (narrow = qualified,
disclaimer or adverse; wide adds the explanatory-paragraph cases) and CSMAR
violation announcements dated in fiscal year t+1 (any violation, and the
disclosure-related subset: delayed disclosure, misstatement, material
omission, fictitious profit or assets). Scores are used as risk rankings;
AUC and top-queue enrichment carry bootstrap 95% intervals.

## Headline findings

- The finance-only Isolation Forest score ranks firms with a modified audit
  opinion well above chance: AUC 0.802 [0.774, 0.833], with 6.37x enrichment and 31.9% of all events in the top-5% queue.
- The text-only score is close to chance for the same label (AUC 0.520 [0.478, 0.557]).
- The Beneish M-Score is *anti-correlated* with real modified opinions: AUC 0.242 [0.200, 0.281], i.e. the proxy benchmark used in the first specification is not merely noisy, it points the wrong way for this sample.
- Under firm-grouped cross validation the fused model beats the finance-only model in 8 of 8 label-by-model combinations and the bootstrap interval excludes zero in 0 of them; every point estimate is non-negative.

## Ranking quality of the existing scores

| Label | Score | AUC [95% CI] | PR-AUC | Lift top-10% [95% CI] |
| --- | --- | --- | --- | --- |
| mod_opinion | finance-only IF | 0.802 [0.774, 0.833] | 0.111 | 4.95 [4.29, 5.57] |
| mod_opinion | text-only IF | 0.520 [0.478, 0.557] | 0.024 | 0.98 [0.53, 1.36] |
| mod_opinion | fused IF | 0.769 [0.734, 0.801] | 0.106 | 4.56 [3.92, 5.24] |
| mod_opinion | fused AE | 0.690 [0.651, 0.735] | 0.074 | 3.43 [2.85, 4.08] |
| mod_opinion | Beneish M-Score | 0.242 [0.200, 0.281] | 0.018 | 0.64 [0.35, 0.96] |
| mod_opinion_wide | finance-only IF | 0.781 [0.753, 0.810] | 0.180 | 4.62 [4.11, 5.10] |
| mod_opinion_wide | text-only IF | 0.530 [0.496, 0.560] | 0.045 | 1.15 [0.79, 1.47] |
| mod_opinion_wide | fused IF | 0.759 [0.730, 0.785] | 0.172 | 4.25 [3.78, 4.74] |
| mod_opinion_wide | fused AE | 0.678 [0.646, 0.710] | 0.124 | 3.46 [2.95, 3.88] |
| mod_opinion_wide | Beneish M-Score | 0.276 [0.247, 0.312] | 0.030 | 0.73 [0.48, 1.01] |
| violation_any_t1 | finance-only IF | 0.570 [0.555, 0.584] | 0.288 | 1.70 [1.58, 1.84] |
| violation_any_t1 | text-only IF | 0.497 [0.483, 0.510] | 0.209 | 0.91 [0.79, 1.01] |
| violation_any_t1 | fused IF | 0.557 [0.542, 0.572] | 0.276 | 1.60 [1.47, 1.73] |
| violation_any_t1 | fused AE | 0.544 [0.529, 0.559] | 0.262 | 1.42 [1.28, 1.55] |
| violation_any_t1 | Beneish M-Score | 0.425 [0.409, 0.438] | 0.188 | 0.87 [0.74, 0.99] |
| violation_disclosure_t1 | finance-only IF | 0.596 [0.580, 0.611] | 0.227 | 2.01 [1.85, 2.18] |
| violation_disclosure_t1 | text-only IF | 0.503 [0.486, 0.516] | 0.144 | 0.93 [0.77, 1.06] |
| violation_disclosure_t1 | fused IF | 0.582 [0.566, 0.599] | 0.216 | 1.89 [1.71, 2.06] |
| violation_disclosure_t1 | fused AE | 0.557 [0.541, 0.576] | 0.195 | 1.56 [1.40, 1.75] |
| violation_disclosure_t1 | Beneish M-Score | 0.407 [0.389, 0.425] | 0.124 | 0.85 [0.69, 1.00] |

## Supervised comparison under firm-grouped cross validation

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
