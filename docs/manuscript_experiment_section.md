# 5. Experiment and Results

> Status: FILLED with real `run_07` output (n = 8,140; three years 2021–2023).
> Numbers source: outputs/tables/*.csv, outputs/reports/descriptives_summary.md.
> Delete this banner before merging into the Word manuscript.

## 5.1 Final Sample and Data Coverage

The sample frame contains 3,694 manufacturing firms and 10,172 firm-years
(2021: 3,165; 2022: 3,404; 2023: 3,603). After merging the six financial
features, the three textual features and the Beneish M-Score, **8,140 firm-years
(80.0%) across 3,265 firms** have complete data and enter the main analysis
(2021: 2,430; 2022: 2,769; 2023: 2,941).

- MD&A text availability: 9,991 rows are of good quality, 7 are flagged as
  suspicious (scanned reports or fewer than 300 tokens) and 174 have no usable
  text. Yearly usable shares are 96.5% (2021), 99.0% (2022) and 99.0% (2023).
- Download audit: 10,051 PDFs verified correct out of 10,172 (98.8%); the 121
  missing files are mostly pre-listing OTC (NEEQ) years of Beijing Stock Exchange
  firms that CNINFO does not archive.

## 5.2 Descriptive Statistics

Table 5.1 reports the raw (pre-standardisation) distributions of the nine
features. The financial features are right-skewed with heavy tails (for example
`receivables_turnover` and `revenue_growth` reach extreme values), which is why
the pipeline winsorises each feature at the 1st and 99th percentiles before
standardisation.

| Feature | n | mean | std | min | max |
| --- | --- | --- | --- | --- | --- |
| roa | 10,110 | 0.094 | 0.726 | -11.33 | 47.99 |
| leverage | 10,172 | 0.404 | 1.776 | 0.014 | 178.35 |
| revenue_growth | 9,288 | 1.729 | 24.852 | -81.54 | 1,232.64 |
| ocf_to_assets | 10,135 | 0.015 | 0.080 | -0.758 | 3.236 |
| receivables_turnover | 10,096 | 112.18 | 3,124.36 | 0.0 | 281,021.9 |
| accruals_to_assets | 10,073 | 0.077 | 0.685 | -11.34 | 47.74 |
| readability | 9,998 | 0.0093 | 0.0019 | 0.0010 | 0.0336 |
| sentiment_balance | 9,998 | 0.0083 | 0.0046 | -0.020 | 0.0352 |
| uncertainty_ratio | 9,998 | 0.0025 | 0.0014 | 0.0 | 0.0224 |

The benchmark (Beneish M-Score above -1.78) marks 5,110 of the 8,140 usable
firm-years (62.8%) as "red flags". This share is much higher than the single-digit
incidence in Beneish's original US sample, so the benchmark is treated only as a
weak external reference, never as a training label.

## 5.3 Main Results (RQ1: does text add information?)

Table 5.2 reports the Spearman rank correlation between each anomaly ranking and
the Beneish M-Score, and Table 5.3 reports event rates and enrichment ratios at
the top-5%, top-10% and top-15% review thresholds.

| Model | Spearman rho | p-value |
| --- | --- | --- |
| Finance-only IF | 0.136 | < 0.001 |
| Text-only IF | -0.030 | 0.008 |
| Fused IF | 0.103 | < 0.001 |
| Fused autoencoder | 0.012 | 0.272 |

| Model | k | Event rate (M > -1.78) | Enrichment |
| --- | --- | --- | --- |
| Finance-only IF | 5% | 0.860 | 1.370 |
| Finance-only IF | 10% | 0.764 | 1.217 |
| Finance-only IF | 15% | 0.733 | 1.168 |
| Text-only IF | 10% | 0.574 | 0.914 |
| Fused IF | 5% | 0.835 | 1.331 |
| Fused IF | 10% | 0.738 | 1.176 |
| Fused IF | 15% | 0.712 | 1.134 |
| Fused autoencoder | 10% | 0.625 | 0.996 |

The finance-only Isolation Forest shows a weak but highly significant positive
rank agreement with the benchmark (rho = 0.136, p < 0.001) and its top-10% list
contains 1.22 times the sample-wide benchmark rate (1.37x at the top-5%
threshold). The text-only ranking is essentially uncorrelated (rho = -0.030), and
adding the three textual features to the fused model **does not improve** the
ranking (fused rho = 0.103 < finance-only 0.136). RQ1 is therefore answered in
the negative: in this sample, textual tone features do not add incremental value
over the financial features for flagging Beneish-style red flags.

## 5.4 Group Contributions (RQ2: finance vs text)

On the fused model, the financial group accounts for 65.9% of the total absolute
SHAP contribution and the textual group for 34.1%. The three most important global
features are `ocf_to_assets` (0.324), `revenue_growth` (0.317) and `readability`
(0.315), so the two groups both contribute but the financial side dominates,
consistent with RQ1.

The top-ranked firm-year is firm 000820 (2021, sub-industry C42), with a fused
anomaly score of 0.767 and a very high M-Score of 1,077.5. Its largest local SHAP
driver is `receivables_turnover`, followed by `revenue_growth` and
`ocf_to_assets`, indicating an unusually large receivables/revenue combination
relative to its subindustry-year peers.

## 5.5 Robustness (RQ3: ranking stability)

The top-10% overlap between the finance-only and fused rankings is 0.828 (they
largely agree because the fused model is dominated by financial features), while
the finance-only vs text-only overlap is only 0.120 (the two signals rank very
different firms). The autoencoder reconstruction-error ranking does not
replicate the main result: its correlation with the benchmark is 0.012 (p = 0.272)
and its top-10% enrichment is 0.996 (no better than chance). This shows the
finding is sensitive to the modelling choice and should be read as a screening
signal, not a stable risk label.

## 5.6 Discussion and Limitations

The score is a review-priority ranking signal, not a verdict on fraud. The
benchmark itself is imperfect in this setting: the -1.78 cut-off flags 62.8% of
the sample, so the enrichment ratios are diluted relative to a low-incidence
benchmark. Known approximations include bootstrap-sized sentiment and uncertainty
dictionaries, substring counting, exclusion of scanned or unreadable reports,
sparse subindustry-year standardisation fallback, and the use of the M-Score as a
proxy for disclosure risk. These are disclosed in the reproducibility guide (§5).

## Suggested figures (paths from run_07)

1. outputs/figures/score_distribution_if_fused.png (main text)
2. outputs/figures/topk_enrichment.png
3. outputs/figures/group_contributions.png
4. outputs/figures/shap_importance.png
5. outputs/figures/ranking_overlap.png
