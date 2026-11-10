# 3. Research Design and Methodology

File:     docs/manuscript_methodology_section.md
Author:   Group12A2 DSW Team
Purpose:  past-tense, actual-implementation rewrite of the proposal's §3 for the
          final manuscript. Every stated value matches src/config.py, the feature
          dictionary, and the pipeline scripts.

Revision History:
  2026-11-06  initial draft: tense shift + exact hyperparameters filled in.

---

## 3.1 Scope, Sample, and Data Sources

The unit of analysis was the firm-year. The sample covered Chinese A-share firms
classified as manufacturing (CAPCO `IndustryCodeD` prefix `C`) for fiscal years 2021,
2022, and 2023, with 2020 retained as the base year for growth and Beneish
first-differences. Manufacturing was chosen to improve cross-sectional comparability
while preserving firm-level variation. A firm-year entered the eligible set only when its
annual report was downloadable, its MD&A section was identifiable, and its core financial
inputs were present; missingness was reported rather than imputed silently.

Financial variables were taken from CSMAR consolidated statements (`FS_Combas`,
`FS_Comins`, `FS_Comscfd`). Annual-report PDFs and MD&A text were collected from the CNINFO
disclosure site. Every observation retained stock code, fiscal year, report source, and
extraction date so that each firm-year could be traced back to its documents. External
evaluation variables comprised a Beneish M-Score computed from the statements and, where
coverage allowed, modified audit opinions. None of these variables entered model fitting.

## 3.2 Feature Construction

The finance-only matrix used six indicators fixed in advance: return on assets, total
liabilities to total assets, revenue growth, operating cash flow to total assets, an
accounts-receivable-turnover measure, and total accruals to total assets. The text-only
matrix used three MD&A indicators: a Chinese readability measure based on document length
and complexity, a sentiment-balance score from positive and negative financial language,
and an uncertainty ratio from a Chinese financial-language dictionary. Formulae, source
fields, denominator treatment, and standardisation rules are recorded in
`docs/feature_dictionary.md`.

Numerical features were winsorised at the 1st and 99th percentiles and then standardised
within manufacturing subindustry-year groups; cells with fewer than 20 observations fell
back to full-sample standardisation. The finance-only, text-only, and fused nine-feature
matrices were built from the same eligible firm-years under identical preprocessing, so
that any difference between rankings isolates the effect of adding textual features.

## 3.3 Unsupervised Anomaly Screening

Isolation Forest was the primary model, chosen because it ranks unusual observations
without complete labels. It was run with 500 trees, a maximum subsample of 256
observations (the whole sample when smaller), and a fixed random seed of 42. The review
priority threshold was set to the top 10% in advance; top-5% and top-15% were used only as
sensitivity checks. The score direction was corrected so that a larger value always
indicated greater statistical abnormality, and no parameter was tuned against enforcement,
restatement, or audit outcomes.

The model was estimated separately on the finance-only, text-only, and fused matrices. The
output was a continuous anomaly score and rank rather than a normal-or-compliant label; a
high score only advanced an observation in the review queue.

## 3.4 Robustness Model and Explainability

An autoencoder supplied a second ranking from reconstruction error. It was implemented as a
symmetric multilayer perceptron (`sklearn` `MLPRegressor`) with hidden layers (16, 8, 16),
an 8-unit bottleneck, ReLU activation, the Adam optimiser, L2 regularisation `alpha = 1e-4`,
learning rate `1e-3`, batch size 256, at most 500 epochs, and early stopping after 20
iterations without improvement on a 10% validation split; the full configuration was
serialised to `outputs/reports/autoencoder_config.json`. Its purpose was to test whether the
main ranking patterns survived a different detection mechanism.

Isolation Forest scores were attributed with a SHAP-compatible explainer, with the explained
output oriented so that higher values consistently indicated greater abnormality. Global
importance and the relative contribution of the financial versus textual groups were
reported, and selected highly ranked firm-years were presented with their raw and
standardised values, textual measures, and feature contributions. SHAP described how the
model arrived at a score; it did not identify causal mechanisms.

## 3.5 Evaluation

The main continuous validation was the Spearman rank association between anomaly scores and
the Beneish M-Score, using benchmark flags as validation-only indicators: the legacy M > −1.78
rule and a sample-calibrated top-decile M-Score flag. For each
available binary benchmark the event rate and the enrichment ratio in the top 10% were
reported relative to the full eligible sample, with top-5% and top-15% sensitivity figures.
Robustness checks varied the review threshold, feature set, year, and manufacturing
subindustry, and compared Isolation Forest and autoencoder rankings by rank correlation and
top-k overlap. Findings were framed as associations with observable risk signals, not as
prediction accuracy for disclosure quality or misconduct.
