# 5. Experiment and Results

> Status: regenerated from `run_07` output by `scripts/build_section5.py`.
> Sample: n = 9,239 firm-years, 3,488 firms, 2021-2023.
> Delete this banner before merging into the Word manuscript.

## 5.1 Final Sample and Data Coverage

The sample frame contains 3,694 manufacturing firms and 10,172 firm-years (2021: 3,165; 2022: 3,404; 2023: 3,603). After merging the six financial features, the three textual features and the Beneish M-Score, 9,239 firm-years (90.8%) across 3,488 firms have complete data and enter the main analysis (2021: 2,732; 2022: 3,124; 2023: 3,383). MD&A text was extracted for 9,998 firm-years: 9,991 pass the quality screen and 7 fall below 300 tokens but are retained and flagged, while 174 have no usable text; the yearly extraction shares are 96.7% (2021), 99.1% (2022), 99.0% (2023). All seven flagged rows remain in the complete-case sample. The download audit verified 10,051 PDFs correct out of 10,172 (98.8%); the 121 missing files are mostly pre-listing OTC (NEEQ) years of Beijing Stock Exchange firms that CNINFO does not archive.

## 5.2 Descriptive Statistics and Main Results (RQ1)

Table 5.1 reports the raw distributions of the nine features, before winsorisation and standardisation, Table 5.2 the rank correlation between each anomaly ranking and the Beneish M-Score, and Table 5.3 the event rates and enrichment ratios at the top-5%, top-10% and top-15% review thresholds under both benchmark definitions.

Table 5.1. Descriptive statistics of the nine features in raw form, before winsorisation and standardisation (10,172 firm-years).

| Feature | n | mean | std | min | max |
| --- | --- | --- | --- | --- | --- |
| roa | 10,172 | 0.0362 | 0.1120 | -2.491 | 6.365 |
| leverage | 10,172 | 0.3843 | 0.2131 | 0.0150 | 5.906 |
| revenue_growth | 9,442 | 0.3883 | 12.086 | -1.445 | 944.10 |
| ocf_to_assets | 10,172 | 0.0491 | 0.0793 | -1.788 | 0.8385 |
| receivables_turnover | 10,145 | 262.20 | 17,699 | -0.4716 | 1,764,970 |
| accruals_to_assets | 10,172 | -0.0128 | 0.1099 | -1.847 | 6.822 |
| readability | 9,998 | 0.0093 | 0.0019 | 0.00100 | 0.0336 |
| sentiment_balance | 9,998 | 0.0888 | 0.0180 | 0.00000 | 0.1727 |
| uncertainty_ratio | 9,998 | 0.0058 | 0.0029 | 0.00000 | 0.0597 |

The financial features are right-skewed with heavy tails - for example `receivables_turnover` and `revenue_growth` reach extreme values - which is why the pipeline winsorises every feature at the 1st and 99th percentiles before standardisation. Two benchmark definitions are used throughout. The legacy definition follows Beneish (1999) literally and treats M > -1.78 as a risk flag; in this sample it flags 1,686 of 9,239 analysed firm-years (18.2%), far above the single-digit incidence reported for Beneish's original US sample, so it is best read as a weak external reference rather than an event indicator. Because a cut-off that flags 18% of the sample is far above the incidence the score was calibrated for, every enrichment ratio is mechanically diluted towards one, so we also report a recalibrated definition that flags the top decile of the sample's own M-Score distribution (M > -1.44, 924 firm-years). The recalibrated benchmark is a relative ranking target, not an estimate of the fraud base rate; both definitions are reported side by side and neither ever enters model training.

Table 5.2. Spearman rank correlation between each anomaly ranking and the Beneish M-Score (n = 9,239).

| Model | Spearman rho | p-value |
| --- | --- | --- |
| Finance-only IF | -0.021 | 0.040 |
| Text-only IF | -0.026 | 0.013 |
| Fused IF | -0.018 | 0.091 |
| Fused autoencoder | -0.007 | 0.528 |

Table 5.3. Event rates and enrichment ratios at the review thresholds, under the legacy cut-off (M > -1.78) and the recalibrated benchmark (M top-10%).

| Model | k | Event rate (legacy) | Enrichment (legacy) | Event rate (recalibrated) | Enrichment (recalibrated) |
| --- | --- | --- | --- | --- | --- |
| Finance-only IF | 5% | 0.275 | 1.506 | 0.223 | 2.229 |
| Finance-only IF | 10% | 0.308 | 1.690 | 0.245 | 2.446 |
| Finance-only IF | 15% | 0.312 | 1.712 | 0.234 | 2.337 |
| Text-only IF | 5% | 0.158 | 0.866 | 0.110 | 1.104 |
| Text-only IF | 10% | 0.153 | 0.836 | 0.091 | 0.909 |
| Text-only IF | 15% | 0.165 | 0.905 | 0.097 | 0.974 |
| Fused IF | 5% | 0.271 | 1.483 | 0.214 | 2.143 |
| Fused IF | 10% | 0.285 | 1.560 | 0.210 | 2.099 |
| Fused IF | 15% | 0.302 | 1.653 | 0.216 | 2.157 |
| Fused autoencoder | 5% | 0.310 | 1.696 | 0.223 | 2.229 |
| Fused autoencoder | 10% | 0.287 | 1.572 | 0.196 | 1.959 |
| Fused autoencoder | 15% | 0.271 | 1.487 | 0.178 | 1.782 |

Under the legacy benchmark the finance-only Isolation Forest is weakly and inversely rank-correlated with the M-Score (rho = -0.021, p = 0.040): the firm-years it ranks as most anomalous are, on average, slightly less likely to sit above the literal -1.78 cut-off. Its top-10% review list still contains 1.69 times the sample-wide flag rate (1.51x at the top-5% threshold). The text-only ranking is weakly negative and marginally significant (rho = -0.026, p = 0.013), and adding the three textual features leaves the fused ranking at -0.018, essentially the same as finance-only. RQ1 is therefore answered in the negative: in this sample, MD&A tone and readability features add no incremental value over structured financial features for reproducing the Beneish screen.

Two features of that comparison matter for interpretation. First, the negative sign means the two instruments do not merely fail to agree - they order firms differently, so a screen built on statement shape selects firm-years that the earnings-manipulation proxy tends to place below its cut-off. Second, because the recalibrated benchmark defines its top decile on the M-Score itself, enrichment ratios rise mechanically for every model, yet the ordering survives: finance-only reaches 2.45 at the top-10% and 2.23 at the top-5% threshold, the fused model 2.10 and 2.14, and the text-only model 0.91 and 1.10, that is, below chance at both thresholds. The finance-only lead over the fused model is small and threshold-dependent and should not be read as a stable advantage. Taken with the group contributions in §5.3 and the external tests in §5.7, the evidence supports a narrow claim: textual features behave as a largely orthogonal signal that does not improve - and, in an unweighted fusion, slightly dilutes - a financial screen for Beneish-type earnings-management risk.

## 5.3 Group Contributions (RQ2: finance vs text)

On the fused model, the financial group accounts for 66.2% of the total absolute SHAP contribution and the textual group for 33.8%. The three most important global features are `accruals_to_assets` (0.314), `revenue_growth` (0.312), `sentiment_balance` (0.304); because their contributions are this close, the profile is better read as a flat importance distribution than as a dominant variable, and both feature families appear among the top attributes.

The top-ranked firm-year is firm 600870 (2021, sub-industry C39), with a fused anomaly score of 0.704 and an M-Score of 14.3, that is, a firm the Beneish proxy does not flag. Its largest local SHAP drivers are `receivables_turnover`, `revenue_growth`, `leverage` — an unusual receivables turnover, revenue growth and leverage profile relative to its subindustry-year peers. The local explanation therefore illustrates the inverse relation documented in §5.2 rather than corroborating the benchmark: the Isolation Forest responds to statement shape, while the M-Score weights the same statements differently and, in this sample, ranks such firms lower.

## 5.4 Robustness (RQ3: ranking stability)

The top-10% overlap between the finance-only and fused rankings is 0.797 (they largely agree because the fused model is dominated by financial features), while the finance-only versus text-only overlap is only 0.132, so the two signal families order very different firms. The choice of benchmark changes the level of every enrichment ratio but not this ordering: under the recalibrated benchmark the finance-only model leads the fused model by 0.35 at the top-10% threshold, and the text-only model stays below both. The autoencoder reconstruction-error ranking does not reproduce the main result: its rank correlation with the benchmark is -0.007 (p = 0.528), and its top-10% enrichment is 1.57 under the legacy cut-off (1.96 recalibrated), barely above chance. The ordering is also stable year by year (finance-only rho by year: 2021: -0.004, 2022: -0.003, 2023: -0.031); the text-only correlation is weakly negative in 3 of 3 years and the fused correlation never departs from the finance-only value by more than 0.01. The conclusion is therefore a property of the Isolation Forest specification combined with these features, not a model-free property of the data, and it should be read as a screening signal rather than a stable risk label.

## 5.5 Discussion and Limitations

The evidence supports two claims, one negative and one positive. The negative claim is that the three MD&A features do not improve the unsupervised ranking against the Beneish M-Score (rho -0.018 fused, -0.021 finance-only, against -0.026 for text alone). The positive claim concerns the benchmark itself. Across 9,239 firm-years from 3,488 firms, the finance-only Isolation Forest ranks firm-years with contemporaneous modified audit opinions well (AUC 0.802), whereas the Beneish M-Score ranks those same firms below chance (AUC 0.242). The inversion is therefore not a nuisance but a finding: the M-Score cannot serve as a proxy for audit risk in this setting, and a null RQ1 may reflect the target rather than the text. Three limitations bound the interpretation. First, the literal -1.78 cut-off flags 18.2% of the sample and the recalibrated top-decile definition is a relative target rather than an estimate of the true base rate, so neither delivers a clean precision figure; the external outcome is the sharper test precisely because it is not circular. Second, the textual measures remain approximations: the sentiment lexicon matches 111.3 terms per 1,000 MD&A tokens against 13.4 for the bootstrap version (8.3x), so the null result is not an artefact of a sparse dictionary; readability is a character-level proxy for processing cost, and scanned or unreadable reports are excluded. Third, the design is a three-year manufacturing sample, so the negative RQ1 result should be read as evidence about this period and industry rather than as a general law about Chinese disclosure text. These choices are disclosed in the reproducibility guide (§5), and every table in this section can be regenerated from the released scripts.

## 5.6 From the First to the Second Specification

The first version of this study measured MD&A text with a small bootstrap lexicon and evaluated every ranking against the literal Beneish cut-off. Two design weaknesses became apparent once the full sample was in place: the bootstrap list matched only a handful of terms per thousand words, so a null result could plausibly be dismissed as a measurement artefact, and the literal cut-off flagged well over half of the sample, so every enrichment ratio was mechanically pulled towards one. Rather than report a fragile null, we rebuilt both components and re-ran the complete pipeline on the same firm-years.

Table 5.4. First and second specifications: what changed and what it did to the results.

| Design choice | First specification (v0.1) | Second specification (v0.2) |
| --- | --- | --- |
| Sentiment lexicon | Bootstrap list of 38 positive / 33 negative terms | Yao et al. (2021): 3,585 positive / 1,633 negative terms |
| Lexicon matching | Substring counting on raw text | jieba token match with a 5,218-term user dictionary |
| Sentiment hits per 1,000 tokens | 13.4 | 111.3 (8.3x) |
| Uncertainty list | 23 terms | About 100 terms (Loughran-McDonald and Zeng et al.) |
| Beneish benchmark | Literal M > -1.78 only | Literal M > -1.78 and sample top decile (M > -1.44, 10%) |
| Text-only / fused rank correlation | -0.030 / 0.103 | -0.026 / -0.018 |
| Autoencoder rank correlation (p) | 0.012 (0.272) | -0.007 (0.528) |
| Text-only top-10% enrichment (recalibrated) | 1.07 | 0.91 |
| Answer to RQ1 | No incremental value for the Beneish screen | Unchanged for the Beneish screen; small positive but statistically indistinguishable increments in supervised models (Table 5.6) |

Table 5.4 summarises the two specifications. The lexicon was replaced by the full Chinese financial sentiment list of Yao et al. (2021), uncertainty terms were expanded, substring counting was replaced by jieba token matching, and the single threshold was supplemented by a sample-calibrated top-decile definition: the sentiment measure matches 111.3 terms per 1,000 MD&A tokens against 13.4 in the first specification (8.3 times denser). The substantive answer does not move: the text-only rank correlation goes from -0.030 to -0.026, the fused correlation from 0.103 to -0.018, and the autoencoder from 0.012 (p = 0.272) to -0.007 (p = 0.528); under the recalibrated benchmark the text-only top-10% enrichment falls from 1.07 to 0.91. One caveat applies to that comparison: the first specification was estimated on the earlier financial intermediate, in which the annual statement rows were merged positionally and therefore lagged or mixed firm-years (§5.1 describes the repair). Part of the movement in Table 5.4 - notably the fused correlation changing sign - reflects that data correction rather than the lexicon alone. With that caveat, the second specification removes the two most obvious measurement objections while leaving RQ1 answered negatively. Both specifications are retained: the frozen v0.1 lexicons, the cached MD&A text, and the archived result tables are stored in the repository, and scripts/compare_runs.py reproduces the comparison reported here.

## 5.7 External Validation Against Real Regulatory Outcomes

The Beneish M-Score is only a proxy for earnings manipulation, and the preceding subsections have shown it is a poor one in this sample. We therefore validate the scores against two real CSMAR outcomes: the audit opinion on the fiscal-year report (FIN_Audit) and exchange violation announcements (STK_Violation_Main). The narrow opinion label equals one for any opinion other than unqualified; the wide label also counts unqualified opinions with an explanatory paragraph. The violation label equals one when an announcement falls in t+1. Sample counts are reported for both all violations and the disclosure-related subset, whereas the ranking tests in Table 5.5 use the narrower subset (delayed disclosure, misstatement, material omission, fictitious profit or assets), which keeps that test forward-looking and extends the window to 2025.

Both outcomes cover all 9,239 firm-years, so this is an external validation rather than a subsample check. Modified opinions are rare: 204 (2.21%), or 355 (3.84%) counting explanatory paragraphs, at rates of 2021: 2.8%, 2022: 2.2%, 2023: 1.8% - the enforcement cycle rather than a firm property. Violations are common because they mix disclosure problems with trading and governance offences: 1,965 (21.27%) received some announcement in t+1 and 1,337 (14.47%) a disclosure-related one.

Table 5.5. Ranking quality against real outcomes: opinion = modified audit opinion, violation = disclosure-related announcement in t+1, lift = top-10% queue event rate over the base rate.

| Score | AUC: opinion | AUC: disclosure violation t+1 | Lift: opinion | Lift: disclosure violation |
| --- | --- | --- | --- | --- |
| finance-only IF | 0.802 | 0.596 | 4.95 | 2.01 |
| text-only IF | 0.520 | 0.503 | 0.98 | 0.93 |
| fused IF | 0.769 | 0.582 | 4.56 | 1.89 |
| fused AE | 0.690 | 0.557 | 3.43 | 1.56 |
| Beneish M-Score | 0.242 | 0.407 | 0.64 | 0.85 |

Table 5.5 reports ranking quality. The finance-only Isolation Forest transfers to the real outcome: AUC 0.802 [0.774, 0.833] for a modified opinion, with the top-10% queue at 4.95 times the base rate and covering 49.5% of modified opinions. Text alone is close to chance (0.520 [0.478, 0.557]), the fused score sits between the two (0.769 [0.734, 0.801]), and the autoencoder is weaker still (0.690 [0.651, 0.735]). Most striking is the benchmark: the Beneish M-Score orders modified-opinion firms below the rest of the sample (0.242 [0.200, 0.281]), so the proxy behind RQ1 points the wrong way relative to what auditors did.  For forward violations every score is weaker (best 0.596 [0.580, 0.611]), as expected when the outcome mixes disclosure quality with regulator attention.

Table 5.6. Out-of-fold AUC under firm-grouped five-fold cross-validation, with the increment of the fused block over finance-only.

| Feature set | Model | AUC: opinion | ΔAUC vs finance | AUC: disclosure violation t+1 | ΔAUC vs finance |
| --- | --- | --- | --- | --- | --- |
| Finance only | Logit | 0.865 | - | 0.672 | - |
| Finance only | Gradient boosting | 0.861 | - | 0.671 | - |
| Text only | Logit | 0.680 | - | 0.570 | - |
| Text only | Gradient boosting | 0.613 | - | 0.526 | - |
| Fused | Logit | 0.866 | 0.002 | 0.673 | 0.001 |
| Fused | Gradient boosting | 0.873 | 0.012 | 0.679 | 0.008 |

Table 5.6 asks the complementary supervised question: given the labels, does the text block add rank information beyond the financial block? Text alone is weaker than finance alone (0.680 versus 0.865 for modified opinions), so the issue is complementarity. Under firm-grouped cross-validation the logistic model reaches 0.865 on financial features and 0.866 fused, an increment of +0.002 [-0.013, +0.014]; gradient boosting gives +0.012 [-0.005, +0.027], and the disclosure-violation label gives +0.001 [-0.005, +0.007] and +0.008 [-0.002, +0.016]. Across the 8 label-by-model combinations the increment is positive in 8 and its interval excludes zero in 0 - small and never statistically distinguishable from zero.

Two caveats keep this from being a clean positive headline. First, the audit opinion is contemporaneous with the fiscal year, so Table 5.5 measures identification of risky disclosures rather than forecasting; only the violation label is a genuine forecast, and there the scores are weak. Second, both labels are produced by auditors and regulators whose capacity varies over time and across firms, so the measurement error is not classical. The substantive reading is a construct mismatch: MD&A tone and readability say something about the disclosure process auditors police, but little about the accounting-manipulation construct the Beneish benchmark measures. RQ1's negative answer therefore stands for the Beneish target, while against real audit outcomes the fused block adds at most a small increment that is not statistically distinguishable from zero - consistent with, but not evidence of, complementarity.

## Suggested figures (paths from run_07)

1. outputs/figures/score_distribution_if_fused.png (main text)
2. outputs/figures/topk_enrichment.png
3. outputs/figures/group_contributions.png
4. outputs/figures/shap_importance.png
5. outputs/figures/ranking_overlap.png
