# -*- coding: utf-8 -*-
"""
manuscript_v04_text.py
Author: Group12A2 DSW Team
Purpose: Replacement prose for Sections 3 and 4 of manuscript v0.4, kept in one
         place so the patch script and the word-count check read the same text.
Module: src.reporting

Section 3 keeps its four-part design but absorbs the evaluation design that
Section 4 used to repeat; Section 4 collapses from six subsections to three and
drops the implementation status block, whose content was either stale (test
counts) or a duplicate of the limitations section. Numbers that depend on the
sample live in Section 5 and are deliberately absent here.

Revision History
-----------------
2026-11-26  initial version; restructure for manuscript v0.4.
"""
from __future__ import annotations

SECTION_3_HEADING = "3. Research Design and Methodology"
SECTION_4_HEADING = "4. System Implementation and Reproducibility"

SECTION_3: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "3.1 Scope, Sample, and Data Sources",
        (
            "The unit of analysis is the firm-year. The sample covers Chinese A-share firms "
            "classified as manufacturing (CSMAR industry codes beginning with \"C\") for fiscal "
            "years 2021 to 2025, with fiscal 2020 retained as the base year for growth and for the "
            "components of the Beneish M-Score. Restricting the sample to one industry block keeps "
            "cross-sectional comparisons meaningful while preserving firm-level variation. A "
            "firm-year is eligible only when its annual report is retrievable, the MD&A section is "
            "identifiable, and the core financial inputs are complete; observations lost to an "
            "unavailable report, a failed extraction, or a missing core value are reported together, "
            "once, in Section 5.1.",
            "Financial variables and the sample frame come from CSMAR; the annual-report PDFs from "
            "which MD&A text is extracted come from CNINFO. Every observation keeps its stock code, "
            "fiscal year, report version, source location, and extraction date, so that each "
            "firm-year can be traced back to the document behind it. Three external benchmarks are "
            "used for evaluation only: a documented Beneish M-Score, CSMAR fiscal-year audit "
            "opinions, and exchange violation announcements aligned to the following year. None "
            "enters model fitting, and none is treated as complete ground truth for disclosure "
            "quality.",
        ),
    ),
    (
        "3.2 Textual and Financial Features",
        (
            "The finance-only matrix contains six indicators: return on assets, total liabilities to "
            "total assets, revenue growth, operating cash flow to total assets, a receivables "
            "turnover measure, and total accruals to total assets. The text-only matrix contains "
            "three MD&A indicators: a Chinese readability measure built from text length and "
            "complexity, a sentiment balance score, and an uncertainty ratio. Sentiment is scored "
            "with the Yao et al. (2021) financial sentiment lexicon and Jieba tokenisation; the "
            "uncertainty dictionary draws on Loughran and McDonald (2011) and Zeng et al. (2018). "
            "Feature definitions, source fields, accounting periods, and dictionary versions are "
            "documented in the project repository and applied unchanged in every reported experiment.",
            "Financial features are winsorised at the 1st and 99th percentiles and standardised "
            "within manufacturing subindustry-year groups, falling back to standardisation over the "
            "full eligible sample where a group holds fewer than 20 observations. The finance-only, "
            "text-only, and fused nine-feature matrices are built from the same eligible firm-years "
            "under identical preprocessing, so that differences in their rankings reflect the feature "
            "blocks rather than the sample.",
        ),
    ),
    (
        "3.3 Screening and Robustness Models",
        (
            "Isolation Forest is the primary model because it ranks statistically unusual "
            "observations without requiring labels. The specification uses 500 trees, a maximum "
            "subsample of 256 observations (or the full sample where it is smaller), and random seed "
            "42, and is estimated separately on the finance-only, text-only, and fused matrices. "
            "Scores are oriented so that higher values indicate greater abnormality; the top 10% of "
            "each ranking is the principal review-priority threshold, with top-5% and top-15% as "
            "sensitivity checks. Parameters are never tuned against audit or regulatory outcomes. The "
            "output is a continuous score and rank rather than an abnormal-or-compliant label: a high "
            "score moves an observation forward in a human review queue and does not by itself "
            "establish poor disclosure, fraud, or a violation.",
            "An autoencoder provides a second ranking based on reconstruction error, with hidden "
            "layers of 16, 8, and 16 units, ReLU activation, the Adam optimiser, and random seed 42; "
            "it serves as a robustness comparison, not a second label source. SHAP attributions are "
            "computed on the Isolation Forest scores, with the explained output oriented so that "
            "higher values again indicate greater abnormality. Values are reported in the model's own "
            "units (Isolation Forest path-length deviations), so signs are interpretable while the "
            "magnitudes are not additive with the 0-1 scores in the tables; global and local results "
            "use fixed-seed subsampling on larger datasets. Attributions describe how a fitted model "
            "distributes its score and establish no causal effect.",
        ),
    ),
    (
        "3.4 Evaluation Design",
        (
            "The Beneish M-Score, computed from financial statements, serves as an accounting-risk "
            "proxy rather than a ground-truth fraud label. Its depreciation index is neutralised at "
            "1.0, and two event definitions are reported: the legacy M > -1.78 cut-off and a "
            "sample-calibrated top-decile threshold, the latter being a relative ranking benchmark "
            "rather than an estimate of manipulation incidence. The two external outcomes answer "
            "different questions. Audit opinions are contemporaneous with the fiscal-year report and "
            "therefore assess identification, whereas violation announcements aligned to t+1 provide "
            "the forward-looking test; both are affected by enforcement timing and heterogeneous "
            "violation types. Supervised logistic regression and gradient boosting models, evaluated "
            "with five-fold cross-validation grouped by firm identifier, ask a separate question: "
            "whether text adds ranking information once outcome labels are available. To test the "
            "extension out of sample, fiscal 2025 is scored by models fitted on 2021-2024 and "
            "reported separately from the in-sample years.",
        ),
    ),
)

SECTION_4: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "4.1 Pipeline and Reproducibility",
        (
            "The pipeline is organised as a sequence of stages -- sample frame, statement parsing, "
            "PDF verification, MD&A extraction, quality control, feature assembly, descriptive "
            "statistics, and model evaluation -- each reading defined inputs and writing inspectable "
            "CSV artefacts, so that any stage can be rerun in isolation (Figure 4.1). Stochastic "
            "components take a single configured seed, model settings are centralised in one "
            "configuration file, and an orchestrated entry point runs the sequence end to end. A "
            "suite of 172 automated tests covers parsing, feature construction, scoring, evaluation, "
            "and reporting, so a change in one stage cannot silently alter another. Because the "
            "licensed CSMAR and CNINFO inputs cannot be redistributed, the repository ships "
            "acquisition instructions and the expected directory layout instead of the raw data; a "
            "third party with authorised access can therefore rebuild every number reported here.",
        ),
    ),
    (
        "4.2 Data Acquisition and Coverage",
        (
            "The sample frame comes from the CSMAR listed-company basic-information annual table, "
            "filtered on the manufacturing and fiscal-year criteria of Section 3.1; financial "
            "variables are constructed from the consolidated balance-sheet, income-statement, and "
            "cash-flow-statement exports. Annual-report PDFs are downloaded from CNINFO and verified "
            "against the frame one firm-year at a time, recording each file as usable, missing, or "
            "mismatched. Extraction of the MD&A section tolerates damaged or irregular files: a PDF "
            "that cannot be read is recorded with the status pdf_error and skipped, the batch "
            "continues, and progress is checkpointed so that an interrupted run resumes rather than "
            "restarts. Coverage rates and the resulting attrition from frame to analysis sample are "
            "reported once, in Section 5.1, rather than repeated here.",
        ),
    ),
    (
        "4.3 Model Runs and Evaluation Outputs",
        (
            "Each of the three feature matrices is scored by the Isolation Forest configuration in "
            "Section 3.3, by the autoencoder, and, where labels are required, by the grouped "
            "cross-validation routine, with reconstruction error and anomaly scores written to disk "
            "per firm-year. SHAP values are computed on a fixed-seed subsample capped at 2,000 rows, "
            "with global importances, group contributions, and local attributions for selected "
            "high-ranked firm-years saved as tables. Evaluation then joins these scores to the "
            "Beneish benchmark, audit opinions, and t+1 violation announcements, and reports Spearman "
            "correlations, top-k event rates and enrichment ratios, ranking overlap, and out-of-fold "
            "AUC with bootstrap confidence intervals. Figures and tables are generated from the same "
            "saved artefacts by script, so that every reported number can be traced to an "
            "intermediate file.",
        ),
    ),
)


def body_word_count(blocks: tuple[tuple[str, tuple[str, ...]], ...]) -> int:
    """Count words in the paragraph text only, ignoring subsection headings."""
    return sum(len(paragraph.split()) for _, paragraphs in blocks for paragraph in paragraphs)
