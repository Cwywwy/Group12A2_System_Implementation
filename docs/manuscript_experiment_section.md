# 5. Experiment and Results

> Status: regenerated from `run_07` output by `scripts/build_section5.py`.
> Sample: n = 8,140 firm-years, 3,265 firms, 2021-2023.
> Delete this banner before merging into the Word manuscript.

## 5.1 Final Sample and Data Coverage

The sample frame contains 3,694 manufacturing firms and 10,172 firm-years (2021: 3,165; 2022: 3,404; 2023: 3,603). After merging the six financial features, the three textual features and the Beneish M-Score, 8,140 firm-years (80.0%) across 3,265 firms have complete data and enter the main analysis (2021: 2,430; 2022: 2,769; 2023: 2,941). MD&A text availability is high: 9,998 rows are of good quality, 7 are flagged as suspicious (scanned reports or fewer than 300 tokens) and 174 have no usable text; the yearly usable shares are 96.7% (2021), 99.1% (2022), 99.0% (2023). The download audit verified 10,051 PDFs correct out of 10,172 (98.8%); the 121 missing files are mostly pre-listing OTC (NEEQ) years of Beijing Stock Exchange firms that CNINFO does not archive.

## 5.2 Descriptive Statistics and Main Results (RQ1)

Table 5.1 reports the raw (pre-standardisation) distributions of the nine features, Table 5.2 the rank correlation between each anomaly ranking and the Beneish M-Score, and Table 5.3 the event rates and enrichment ratios at the top-5%, top-10% and top-15% review thresholds under both benchmark definitions.

Table 5.1. Descriptive statistics of the nine features before standardisation (10,172 firm-years).

| Feature | n | mean | std | min | max |
| --- | --- | --- | --- | --- | --- |
| roa | 10,110 | 0.0944 | 0.7263 | -11.330 | 47.999 |
| leverage | 10,172 | 0.4037 | 1.776 | 0.0143 | 178.35 |
| revenue_growth | 9,288 | 1.729 | 24.852 | -81.537 | 1,232.64 |
| ocf_to_assets | 10,135 | 0.0150 | 0.0802 | -0.7583 | 3.236 |
| receivables_turnover | 10,096 | 112.18 | 3,124.36 | 0.00000 | 281,022 |
| accruals_to_assets | 10,073 | 0.0774 | 0.6846 | -11.336 | 47.737 |
| readability | 9,998 | 0.0093 | 0.0019 | 0.00100 | 0.0336 |
| sentiment_balance | 9,998 | 0.0888 | 0.0180 | 0.00000 | 0.1727 |
| uncertainty_ratio | 9,998 | 0.0058 | 0.0029 | 0.00000 | 0.0597 |

The financial features are right-skewed with heavy tails - for example `receivables_turnover` and `revenue_growth` reach extreme values - which is why the pipeline winsorises every feature at the 1st and 99th percentiles before standardisation. Two benchmark definitions are used throughout. The legacy definition follows Beneish (1999) literally and treats M > -1.78 as a risk flag; in this sample it flags 5,110 of 8,140 usable firm-years (62.8%), far above the single-digit incidence reported for Beneish's original US sample, so it is best read as a weak external reference rather than an event indicator. Because a benchmark that flags five firms in eight mechanically dilutes every enrichment ratio towards one, we also report a recalibrated definition that flags the top decile of the sample's own M-Score distribution (M > 16.52, 814 firm-years). The recalibrated benchmark is a relative ranking target, not an estimate of the fraud base rate; both definitions are reported side by side and neither ever enters model training.

Table 5.2. Spearman rank correlation between each anomaly ranking and the Beneish M-Score (n = 8,140).

| Model | Spearman rho | p-value |
| --- | --- | --- |
| Finance-only IF | 0.136 | < 0.001 |
| Text-only IF | -0.029 | 0.008 |
| Fused IF | 0.103 | < 0.001 |
| Fused autoencoder | 0.009 | 0.409 |

Table 5.3. Event rates and enrichment ratios at the review thresholds, under the legacy cut-off (M > -1.78) and the recalibrated benchmark (M top-10%).

| Model | k | Event rate (legacy) | Enrichment (legacy) | Event rate (recalibrated) | Enrichment (recalibrated) |
| --- | --- | --- | --- | --- | --- |
| Finance-only IF | 5% | 0.860 | 1.370 | 0.256 | 2.555 |
| Finance-only IF | 10% | 0.764 | 1.217 | 0.187 | 1.867 |
| Finance-only IF | 15% | 0.733 | 1.168 | 0.164 | 1.638 |
| Text-only IF | 5% | 0.531 | 0.845 | 0.091 | 0.909 |
| Text-only IF | 10% | 0.579 | 0.922 | 0.085 | 0.848 |
| Text-only IF | 15% | 0.587 | 0.935 | 0.089 | 0.893 |
| Fused IF | 5% | 0.845 | 1.346 | 0.273 | 2.727 |
| Fused IF | 10% | 0.752 | 1.198 | 0.184 | 1.843 |
| Fused IF | 15% | 0.713 | 1.135 | 0.153 | 1.532 |
| Fused autoencoder | 5% | 0.631 | 1.006 | 0.138 | 1.376 |
| Fused autoencoder | 10% | 0.624 | 0.994 | 0.125 | 1.253 |
| Fused autoencoder | 15% | 0.621 | 0.989 | 0.115 | 1.155 |

Under the legacy benchmark, the finance-only Isolation Forest shows a weak but highly significant positive rank agreement with the M-Score (rho = 0.136, p < 0.001), and its top-10% review list contains 1.22 times the sample-wide flag rate (1.37x at the top-5% threshold). The text-only ranking is essentially uncorrelated (rho = -0.029), and adding the three textual features does not improve the ranking (fused rho 0.103 against 0.136 for finance-only); the fused model's top-10% enrichment is 1.20. RQ1 is therefore answered in the negative at the literal cut-off: in this sample, MD&A tone and readability features do not add incremental value over structured financial features for flagging Beneish-style red flags.

The recalibrated benchmark does not overturn that answer, but it sharpens it. Because the top decile is defined on the M-Score itself, enrichment ratios rise for every model; the informative content is the ordering of the models rather than the level. The finance-only model reaches 1.87 at the top-10% and 2.56 at the top-5% threshold, the fused model reaches 1.84 and 2.73; the gap between the two is small relative to the spread across thresholds and should not be read as a stable advantage for either specification. The text-only ranking improves from 0.92 to 0.85, that is, from slightly worse than chance to slightly better than chance, but it remains far below the financial models. Taken together with the group contributions in §5.3, the evidence supports a narrow claim: textual features act as a weak, largely orthogonal signal that does not improve a financial screen for Beneish-type earnings-management risk, rather than as a substitute for it.

## 5.3 Group Contributions (RQ2: finance vs text)

On the fused model, the financial group accounts for 65.4% of the total absolute SHAP contribution and the textual group for 34.6%. The three most important global features are `ocf_to_assets` (0.322), `revenue_growth` (0.320), `readability` (0.317), so both groups contribute but the financial side dominates, consistent with RQ1.

The top-ranked firm-year is firm 000820 (2021, sub-industry C42), with a fused anomaly score of 0.759 and an M-Score of 1,077.5. Its largest local SHAP drivers are `receivables_turnover`, `revenue_growth`, `accruals_to_assets`, indicating an unusual combination of receivables, revenue and operating cash flow relative to its subindustry-year peers.

## 5.4 Robustness (RQ3: ranking stability)

The top-10% overlap between the finance-only and fused rankings is 0.817 (they largely agree because the fused model is dominated by financial features), while the finance-only versus text-only overlap is only 0.111, so the two signal families order very different firms. The choice of benchmark changes the level of every enrichment ratio but not this ordering: under the recalibrated benchmark the finance-only and fused models remain within 0.02 of each other at the top-10% threshold, and the text-only model stays below both. The autoencoder reconstruction-error ranking does not replicate the main result at all: its correlation with the benchmark is 0.009 (p = 0.409) and its top-10% enrichment is 0.994 under the legacy cut-off (1.253 recalibrated), that is, indistinguishable from chance. The ordering is also stable year by year (finance-only rho by year: 2021: 0.103, 2022: 0.130, 2023: 0.173); the text-only correlation is negative in 3 of 3 years and the fused ranking trails the finance-only ranking in every year. The finding is therefore a property of the Isolation Forest specification combined with these features, not a model-free property of the data, and it should be read as a screening signal rather than a stable risk label.

## 5.5 Discussion and Limitations

The score is a review-priority ranking signal, not a verdict on fraud. Three limitations bound the interpretation. First, the benchmark is imperfect in this setting: the literal -1.78 cut-off flags 62.8% of the sample, and the recalibrated top-decile definition is a relative target rather than an estimate of the true base rate, so neither delivers a clean precision figure. Second, the textual measures remain approximations: the sentiment lexicon matches 111.3 terms per 1,000 MD&A tokens against 13.4 for the bootstrap version (8.3x), so the null result is not an artefact of a sparse dictionary; readability is a character-level proxy for processing cost, and scanned or unreadable reports are excluded. Third, the design is a three-year manufacturing sample, so the negative RQ1 result should be read as evidence about this period and industry rather than as a general law about Chinese disclosure text. These choices are disclosed in the reproducibility guide (§5), and every table in this section can be regenerated from the released scripts.

## 5.6 From the First to the Second Specification

The first version of this study measured MD&A text with a small bootstrap lexicon and evaluated every ranking against the literal Beneish cut-off. Two design weaknesses became apparent once the full sample was in place: the bootstrap list matched only a handful of terms per thousand words, so a null result could plausibly be dismissed as a measurement artefact, and the literal cut-off flagged well over half of the sample, so every enrichment ratio was mechanically pulled towards one. Rather than report a fragile null, we rebuilt both components and re-ran the complete pipeline on the same firm-years.

Table 5.4. First and second specifications: what changed and what it did to the results.

| Design choice | First specification (v0.1) | Second specification (v0.2) |
| --- | --- | --- |
| Sentiment lexicon | Bootstrap list of 38 positive / 33 negative terms | Yao et al. (2021): 3,585 positive / 1,633 negative terms |
| Lexicon matching | Substring counting on raw text | jieba token match with a 5,218-term user dictionary |
| Sentiment hits per 1,000 tokens | 13.4 | 111.3 (8.3x) |
| Uncertainty list | 23 terms | About 100 terms (Loughran-McDonald and Zeng et al.) |
| Beneish benchmark | Literal M > -1.78 only (flags 62.8% of the sample) | Literal M > -1.78 and sample top decile (M > 16.52, 10%) |
| Text-only / fused rank correlation | -0.030 / 0.103 | -0.029 / 0.103 |
| Autoencoder rank correlation (p) | 0.012 (0.272) | 0.009 (0.409) |
| Text-only top-10% enrichment (recalibrated) | 1.07 | 0.85 |
| Answer to RQ1 | Text adds no value | Unchanged: text adds no value |

Table 5.4 summarises the two specifications. The lexicon was replaced by the full Chinese financial sentiment list of Yao et al. (2021), uncertainty terms were expanded, substring counting was replaced by jieba token matching, and the single threshold was supplemented by a sample-calibrated top-decile definition: the sentiment measure matches 111.3 terms per 1,000 MD&A tokens against 13.4 in the first specification (8.3 times denser). The substantive answer does not move: the text-only rank correlation goes from -0.030 to -0.029, the fused correlation from 0.103 to 0.103, and the autoencoder from 0.012 (p = 0.272) to 0.009 (p = 0.409); under the recalibrated benchmark the text-only top-10% enrichment falls from 1.07 to 0.85. The improvement is therefore in the credibility of the null, not in its sign - the second specification removes the two most obvious measurement objections while leaving RQ1 answered negatively. Both specifications are retained: the frozen v0.1 lexicons, the cached MD&A text, and the archived result tables are stored in the repository, and scripts/compare_runs.py reproduces the comparison reported here.

## 5.7 External Validation Against Real Regulatory Outcomes

The Beneish M-Score is only a proxy for earnings manipulation, and the preceding subsections have shown it is a poor one in this sample. We therefore validate the scores against two real CSMAR outcomes: the audit opinion on the fiscal-year report (FIN_Audit) and exchange violation announcements (STK_Violation_Main). The narrow opinion label equals one for any opinion other than unqualified; the wide label also counts unqualified opinions with an explanatory paragraph. The violation label equals one when an announcement falls in t+1, either any violation or the disclosure-related subset (delayed disclosure, misstatement, material omission, fictitious profit or assets), which keeps that test forward-looking and extends the window to 2025.

Both outcomes cover all 8,140 firm-years, so this is an external validation rather than a subsample check. Modified opinions are rare: 188 (2.31%), or 327 (4.02%) counting explanatory paragraphs, at rates of 2021: 3.0%, 2022: 2.3%, 2023: 1.8% - the enforcement cycle rather than a firm property. Violations are common because they mix disclosure problems with trading and governance offences: 1,757 (21.58%) received some announcement in t+1 and 1,196 (14.69%) a disclosure-related one.

Table 5.5. Ranking quality against real outcomes: opinion = modified audit opinion, violation = disclosure-related announcement in t+1, lift = top-10% queue event rate over the base rate.

| Score | AUC: opinion | AUC: violation t+1 | Lift: opinion | Lift: violation |
| --- | --- | --- | --- | --- |
| finance-only IF | 0.640 | 0.549 | 2.18 | 1.27 |
| text-only IF | 0.524 | 0.500 | 1.06 | 0.93 |
| fused IF | 0.618 | 0.533 | 1.97 | 1.22 |
| fused AE | 0.471 | 0.484 | 0.90 | 0.94 |
| Beneish M-Score | 0.405 | 0.475 | 1.33 | 0.99 |

Table 5.5 reports ranking quality. The finance-only Isolation Forest transfers to the real outcome: AUC 0.640 [0.604, 0.677] for a modified opinion, with the top-10% queue at 2.18 times the base rate and covering 21.8% of modified opinions. Text alone is close to chance (0.524 [0.481, 0.568]), the fused score sits between (0.618 [0.576, 0.656]), and the autoencoder falls below chance (0.471 [0.427, 0.509]). Most striking is the benchmark: the Beneish M-Score orders modified-opinion firms below the rest of the sample (0.405 [0.351, 0.458]), so the proxy behind RQ1 points the wrong way relative to what auditors did. For forward violations every score is weaker (best 0.549 [0.532, 0.566]), as expected when the outcome mixes disclosure quality with regulator attention.

Table 5.6. Out-of-fold AUC under firm-grouped five-fold cross-validation, with the increment of the fused block over finance-only.

| Feature set | Model | AUC: opinion | ΔAUC vs finance | AUC: violation t+1 | ΔAUC vs finance |
| --- | --- | --- | --- | --- | --- |
| Finance only | Logit | 0.778 | - | 0.606 | - |
| Finance only | Gradient boosting | 0.746 | - | 0.642 | - |
| Text only | Logit | 0.685 | - | 0.569 | - |
| Text only | Gradient boosting | 0.590 | - | 0.533 | - |
| Fused | Logit | 0.799 | 0.020 | 0.620 | 0.014 |
| Fused | Gradient boosting | 0.772 | 0.026 | 0.649 | 0.006 |

Table 5.6 asks the complementary supervised question: given the labels, does the text block add rank information beyond the financial block? Text alone is weaker than finance alone (0.685 versus 0.778 for modified opinions), so the issue is complementarity. Under firm-grouped cross-validation the logistic model reaches 0.778 on financial features and 0.799 fused, an increment of +0.020 [-0.002, +0.043]; gradient boosting gives +0.026 [+0.002, +0.049], and the disclosure-violation label gives +0.014 [+0.003, +0.024] and +0.006 [-0.004, +0.019]. Across the 8 label-by-model combinations the increment is positive in 8 and its interval excludes zero in 5 - small but consistent, and opposite to the Beneish comparison in §5.2.

Two caveats keep this from being a clean positive headline. First, the audit opinion is contemporaneous with the fiscal year, so Table 5.5 measures identification of risky disclosures rather than forecasting; only the violation label is a genuine forecast, and there the scores are weak. Second, both labels are produced by auditors and regulators whose capacity varies over time and across firms, so the measurement error is not classical. The substantive reading is a construct mismatch: MD&A tone and readability say something about the disclosure process auditors police, but little about the accounting-manipulation construct the Beneish benchmark measures. RQ1's negative answer therefore stands for the Beneish target, while against real audit outcomes the text block carries a small but detectable increment - the more defensible claim.

## Suggested figures (paths from run_07)

1. outputs/figures/score_distribution_if_fused.png (main text)
2. outputs/figures/topk_enrichment.png
3. outputs/figures/group_contributions.png
4. outputs/figures/shap_importance.png
5. outputs/figures/ranking_overlap.png
