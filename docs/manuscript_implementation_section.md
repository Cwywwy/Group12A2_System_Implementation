# System Implementation and Model Development — Manuscript Draft

> Draft for the 10 Nov milestone (6 pages, ~1,600–1,900 words, double-spaced).
> Author: Group12A2 DSW Team. Language: English (manuscript). Status: DRAFT for
> the team to adapt into the Word manuscript — replace the proposal's future
> tense with the past tense, check every number against the pipeline outputs
> before submission, and delete this banner.

## 4. System Implementation and Model Development

This section describes the implemented screening system that operationalises the
research design in Section 3. All components are version-controlled Python
modules; the hyperparameters and preprocessing decisions below are the exact
values used to produce the results reported in Section 5.

### 4.1 Pipeline Architecture

The system is organised as five modules with clearly separated
responsibilities, so that every intermediate product can be inspected and
reproduced independently:

1. **Data ingestion** (`data_ingestion`): retrieves annual-report PDFs from the
   CNINFO public announcement interface and parses the three CSMAR financial
   statements into a common intermediate schema.
2. **Feature engineering** (`features`): computes the six financial features,
   the three textual features, and the Beneish M-Score validation benchmark.
3. **Modelling** (`models`): fits the Isolation Forest and autoencoder models
   and produces SHAP explanations.
4. **Evaluation** (`evaluation`): computes the Spearman correlation, event
   rates, enrichment ratios, and ranking-overlap statistics against the
   benchmark.
5. **Orchestration** (`scripts`): thin command-line drivers that run one stage
   at a time and write audit logs.

The flow is strictly one-directional: raw data → processed sample frame →
interim feature table → model outputs → evaluation tables. Benchmarks are
attached at the evaluation stage only and never enter the training inputs, which
prevents leakage between the validation variable and the models.

### 4.2 Data Acquisition and Sample Construction

The sample frame is built from the CSMAR *Listed Company Information Annual*
table, which provides company-level identifiers and industry classifications
for all A-share firms. Manufacturing firms are selected using the China
Association for Public Companies (CAPCO) industry code prefix "C" (the 2012
CSRC industry code is incomplete for fiscal 2023 in CSMAR and was therefore not
used). Firm-years are restricted to fiscal years 2021–2023, which yields
3,694 unique manufacturing firms and 10,172 firm-year observations
(3,165 / 3,404 / 3,603 across the three years). The year 2020 serves as the
base year: it supplies the lagged balance-sheet values required by the
growth and accrual features and the Beneish M-Score, but it is not part of the
analysis sample.

Two further data sources are matched on the six-digit stock code and fiscal
year:

- **Financial statements.** The CSMAR consolidated balance sheet, income
  statement, and cash-flow statement files cover fiscal years 2020–2023. A
  tolerant parser locates the header row anywhere in each sheet, maps Chinese
  field names to a canonical schema through an alias table, keeps consolidated
  statements only, and normalises the three date formats found in CSMAR
  exports. The three statements are merged firm-year-wise into one
  intermediate table with 17 columns.
- **Annual-report text.** The Chinese-language PDF annual reports for
  2021–2023 are downloaded programmatically from the CNINFO public
  announcement interface. The client resolves each firm's organisation ID,
  searches for annual reports by publication window (January–June of the
  following year), and selects the matching report while excluding summaries,
  English versions, semi-annual reports, and revised or cancelled filings.
  Downloading is incremental: an existing non-empty file is treated as cached,
  and every outcome is appended to a per-year CSV log.

### 4.3 Feature Engineering

**Financial features.** Six features are computed per firm-year from the
intermediate statement table, using the previous year's balance-sheet values
where a ratio involves a stock item:

| Feature | Formula |
| --- | --- |
| Return on assets | net income / average total assets |
| Liabilities-to-assets | total liabilities / total assets |
| Revenue growth | (revenue_t − revenue_{t−1}) / revenue_{t−1} |
| Operating cash flow-to-assets | OCF / total assets |
| Receivables turnover | revenue / average receivables |
| Total accruals-to-assets | (net income − OCF) / total assets |

**Textual features.** The MD&A section is sliced from each PDF's text layer by
locating the section heading and truncating at the next numbered section. The
locator deliberately prefers the longest heading candidate, so that the short
heading in the table of contents does not displace the body section, and it
accepts alternative phrasings of the heading. After jieba word segmentation
(keeping pure-Chinese tokens), three features are computed with a
Chinese financial sentiment dictionary and an uncertainty dictionary:

| Feature | Formula |
| --- | --- |
| Readability | 1 / mean sentence length in characters |
| Sentiment balance | (positive hits − negative hits) / token count |
| Uncertainty ratio | uncertainty hits / token count |

Dictionary hits are counted by exact token matching after jieba word
segmentation with a user dictionary that forces whole-word segmentation of the
multi-character financial terms. The sentiment dictionaries are the full
formal-register lexicon of Yao et al. (2021) (3,585 positive and 1,633
negative Chinese terms after filtering to pure-Chinese entries); the
uncertainty dictionary combines the Loughran–McDonald (2011) uncertain terms in
Chinese translation with the uncertainty terms of Zeng et al. (2018).

**Benchmark.** The Beneish M-Score is computed from the eight financial
statement ratios with the standard coefficients. Because the original −1.78
cut-off flags a majority of firm-years in this Chinese sample, benchmark
positivity is defined under two alternatives: (i) the legacy M > −1.78 rule,
and (ii) a sample-calibrated top-decile M-Score flag. The M-Score is used only
for validation and is excluded from all model inputs.

**Standardisation.** All features are winsorised at the 1st and 99th
percentiles and then standardised to z-scores *within* manufacturing
sub-industry–year groups (CAPCO code × fiscal year). A group with fewer than
20 observations falls back to the full-sample mean and standard deviation, a
documented exception that preserves numerical stability for sparse cells.

### 4.4 Model Development

**Primary model: Isolation Forest.** The screening signal is an Isolation
Forest ensemble with 500 trees and a maximum of 256 samples per tree (the full
sample is used when fewer observations are available), fit with a fixed random
seed. Because scikit-learn's `score_samples` returns *higher* values for
normal points, the anomaly score is defined as the negated score, so that
larger values indicate more anomalous disclosures. The review threshold is the
top 10% of anomaly scores; top-5% and top-15% thresholds are reported as
sensitivity analyses. Four variants are ranked: financial features only,
textual features only, fused features (the primary specification), and an
autoencoder baseline on fused features.

**Robustness model: autoencoder.** A symmetric multilayer-perceptron
autoencoder (16–8–16 hidden units, ReLU activation, L2 regularisation
1e-4, Adam with learning rate 1e-3, batch size 256, early stopping with
patience 20, validation fraction 0.1, maximum 500 epochs, fixed seed) is fit
on the same standardised inputs. Anomaly scores are the row-wise mean squared
reconstruction errors. The full configuration is recorded to a JSON file with
every model fit so the specification is auditable.

**Explainability: SHAP.** TreeExplainer SHAP values are computed for the
Isolation Forest. Global importance is the mean absolute SHAP value per
feature; group contributions aggregate the nine features into the financial
and textual groups to answer RQ2. Local explanations are produced for the
top-ranked firm-year to answer "why this firm was flagged" in a review
context. SHAP computation is subsampled to at most 2,000 observations with a
fixed seed for tractability, a documented approximation.

### 4.5 Evaluation Protocol

The evaluation answers the three research questions without using labels
inside the models:

- **RQ1 (incremental value of text).** Spearman rank correlation between each
  variant's anomaly scores and the Beneish M-Score, plus the top-10% event
  rate (share of benchmark-positive firm-years among flagged ones) and the
  enrichment ratio (flagged event rate divided by the full-sample event
  rate). The fused model is expected to dominate both single-group variants.
- **RQ2 (feature-group contribution).** SHAP group contributions on the fused
  model.
- **RQ3 (ranking stability).** Top-k overlap between the Isolation Forest
  rankings and the autoencoder rankings at k = 5%, 10%, and 15%.

### 4.6 Reproducibility Practices

Every stochastic component (Isolation Forest, autoencoder, SHAP subsampling)
is fixed to seed 42; all hyperparameters live in a single configuration
module; Python dependencies are pinned in `requirements.txt`; every
intermediate table and evaluation table is written to CSV; download and audit
logs are appended incrementally so a run can be resumed after interruption;
and a test suite of unit tests guards each module. The pipeline is exercised
end-to-end on a synthetic 80-firm panel with planted anomalies before any
conclusion is drawn from the real data.

---

### Status appendix (for the team, delete before submission)

| Component | Status |
| --- | --- |
| Sample frame (3,694 firms / 10,172 firm-years) | Done |
| CNINFO download client + batch download 2021–2023 | Done: 10,051 firm-years downloaded (coverage 98.8%); 121 missing = pre-listing NEEQ years + delisted/restructured (documented boundary) |
| CSMAR parser (three statements → intermediate table) | Done, unit-tested; awaiting team's FS_Comins/FS_Comscfd files |
| Textual/financial features + M-Score | Done, unit-tested; MD&A extraction running (~900/975/900 rows for 2021/22/23) |
| Isolation Forest / autoencoder / SHAP / metrics | Done, unit-tested; synthetic-data smoke test passed |
| Evaluation tables on real data | Blocked on MD&A extraction completion + CSMAR income/cashflow files |

Suggested figures: (1) pipeline architecture diagram; (2) SHAP global
importance bar chart; (3) SHAP group contribution chart; (4) sensitivity
table for the three review thresholds.
