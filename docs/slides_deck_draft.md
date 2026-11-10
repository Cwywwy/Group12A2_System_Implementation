# Slides Deck — Working Draft (12 pages / 12 minutes, Option 2)

> Status: SUPERSEDED for the numbers — `scripts/build_slides.py` now generates the
> deliverable deck (`outputs/slides/Group12A2_Deck.pptx`, 12 pages) straight from
> `outputs/tables/`, so this file is kept only as the English wording source and
> speaker-note reference. Edit the wording here only if you also change the script.

## Slide 1 — Title

Screening Financial Disclosure Risk through Textual-Financial Feature Fusion and
Explainable Anomaly Detection: Evidence from Chinese A-share Manufacturing Firms, 2021–2023

Group 12A2 — Jinyu Wang (MC644879), Wenyuan Chen (MC644700), Mingxuan Wu (MC637835),
Kolawole Sunday O. (MC650023) · Intro FinTech · {DATE}

> Speaker: "We screen disclosure risk for Chinese manufacturing firms by fusing six
> financial features with three textual features from MD&A narratives, ranking firms
> with interpretable anomaly detection."

## Slide 2 — Motivation and Research Questions

- Disclosure quality drives regulatory review, but manual reading of thousands of
  annual reports does not scale.
- Prior work treats financial ratios and narrative tone in isolation; little
  evidence on whether text adds information beyond the numbers for Chinese A-share firms.
- RQ1: Does MD&A text add detection value over financial features alone?
- RQ2: Which feature group (finance vs text) drives the risk ranking?
- RQ3: Is the ranking stable across models and thresholds?

## Slide 3 — Data

- CSMAR financial statements, 2020–2023 consolidated (2020 as base year).
- CNINFO annual-report PDFs 2021–2023; MD&A section extracted and tokenised.
- Sample: 3,694 manufacturing firms / 10,172 firm-years
  {PLACEHOLDER: final coverage incl. QC exclusions}.
- Benchmark for evaluation only: Beneish M-Score (legacy M > −1.78; recalibrated sample top-10%), never in training.

## Slide 4 — Pipeline Overview

One-directional flow: data ingestion → features → modelling → evaluation → reporting.
{INSERT pipeline architecture figure from the manuscript 4.1}

## Slide 5 — Features

- Financial (6): ROA, liabilities-to-assets, revenue growth, OCF-to-assets,
  receivables turnover, total accruals-to-assets.
- Textual (3): Chinese readability (1 / mean sentence length), sentiment balance,
  uncertainty ratio — from 姚加权等 (2021) full financial sentiment lexicon + expanded uncertainty list.
- Pre-processing: 1%/99% winsorisation; subindustry-year z-scores with sparse-cell fallback.
{PLACEHOLDER: descriptive stats mini-table}

## Slide 6 — Models and Threshold

- Isolation Forest: 500 trees, max_samples 256, fixed seed 42; fused on all nine features.
- Ablations: finance-only and text-only matrices.
- Robustness: autoencoder reconstruction error (16-8-16, ReLU, Adam).
- Review threshold: top-10% most anomalous (5%/15% sensitivity).

## Slide 7 — Main Results (RQ1)

{PLACEHOLDER: Spearman ρ vs M-Score, four rankings — outputs/tables/model_metrics.csv}
{PLACEHOLDER: top-10% event rate + enrichment bar chart — outputs/figures/topk_enrichment.png}
> Speaker: report whether fused ranking beats finance-only and whether enrichment > 1.

## Slide 8 — Interpretation (RQ2)

{PLACEHOLDER: outputs/figures/group_contributions.png + shap_importance.png}
> Speaker: name the dominant group and one local example (top1_symbol).

## Slide 9 — Robustness (RQ3)

{PLACEHOLDER: outputs/figures/ranking_overlap.png; AE Spearman row from model_metrics.csv}
> Speaker: overlap of top-10% lists across the four rankings; AE agrees directionally.

## Slide 10 — Limitations

- Dictionary sentiment is a proxy, not a direct measure of misconduct.
- Scanned reports flagged and excluded (QC log).
- M-Score is an imperfect benchmark; scores rank review priority, they do not prove misconduct.

## Slide 11 — Reproducibility

- SEED = 42 everywhere; hyper-parameters centralised in src/config.py.
- requirements.txt frozen; incremental run logs; one-command rebuild (reproducibility guide).
- Data sources are public: CSMAR (campus licence) and CNINFO.

## Slide 12 — Conclusion and Division of Work

{PLACEHOLDER: one-sentence conclusion}
{PLACEHOLDER: four-member contribution table}

## Appendix (not counted)

- QC issue log, download audit results, CSMAR/CNINFO copyright statements.
