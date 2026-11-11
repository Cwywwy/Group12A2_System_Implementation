# 6. Conclusion

File:     docs/manuscript_conclusion_section.md
Author:   Group12A2 DSW Team
Purpose:  conclusion section for the final manuscript (Option 2); headline result
          filled from the v0.2 run (full lexicon + dual benchmark).

Revision History:
  2026-11-06  initial draft.
  2026-11-11  headline result filled with the v0.2 (full-lexicon, dual-benchmark) run.

---

This study built a reproducible, explainable screening framework that combines six
structured financial indicators with three Chinese MD&A textual indicators, and used it
to rank firm-year observations across Chinese A-share manufacturing firms over 2021–2023.
Isolation Forest served as the primary unsupervised detector and an autoencoder provided a
robustness ranking; SHAP attribution showed, at the global and firm-year levels, whether
each score was driven by the financial or the textual group.

The headline result is negative for fusion and positive, if weakly, for the financial block.
Across 8,140 usable firm-years from 3,265 firms, the finance-only ranking correlates with the
Beneish M-Score at Spearman rho = 0.136 (p < 0.001), the fused ranking at 0.103, the text-only
ranking at -0.029, and the autoencoder at 0.009 (p = 0.409). In the top-10% review queue the
finance-only model lifts the M-Score event rate to 1.22 times the sample base rate under the
literal Beneish -1.78 cut-off (1.87 under the recalibrated sample top-decile definition), while
the fused model reaches 1.20 (1.84) and the text-only model 0.92 (0.85). The negative result is
not an artefact of a thin dictionary: the full Yao et al. (2021) lexicon matches 111.3 sentiment
terms per 1,000 MD&A tokens against 13.4 for the earlier bootstrap list, an 8.3-fold increase,
and the conclusion is unchanged.

Three conclusions follow. First, the fused textual-financial representation did not add
incremental screening value over the finance-only representation (rho 0.103 versus 0.136), which
answers RQ1 negatively for Chinese MD&A text measured as readability, sentiment balance, and
uncertainty. Second, SHAP decomposition showed that the financial group contributed the larger
share of absolute importance (65.4% versus 34.6%), indicating where a reviewer's attention is
best directed (RQ2). Third, the top-10% ranking was partially stable: finance-only and fused
queues overlap strongly (Jaccard 0.817), but the text-only queue barely overlaps either (0.111),
the autoencoder does not reproduce the Isolation Forest order (rho 0.009), and the finance-only
correlation is positive in all three years (0.103, 0.130, 0.173) while the text-only correlation
is negative in all three - so the queue is usable as a screening signal but not as a stable risk
label (RQ3).

A fourth result emerged once the benchmark stopped being a proxy. Validated against modified
audit opinions in CSMAR (188 firm-years, 2.31%), the finance-only ranking reaches an AUC of
0.640 with a 2.18x enrichment in the top-10% review queue, whereas the Beneish M-Score ranks
those same firms below chance (AUC 0.405). The proxy the first specification relied on does not
merely add noise; it points the wrong way relative to what auditors actually concluded. Under
firm-grouped cross-validation the text block adds a small but consistent increment to the
financial block (+0.007 to +0.026 AUC across eight label-by-model combinations, five of them
excluding zero), so the honest summary is a construct mismatch rather than a null result for
text as such: MD&A tone and readability carry a little information about the disclosure process
auditors police, and almost none about the accounting-manipulation construct that the Beneish
benchmark measures.

The main limitations are inherent to the design and are reported rather than hidden. The
sample is confined to manufacturing and to a three-year window; the external outcomes
(Beneish M-Score, modified audit opinions and exchange violations) are imperfect labels -
the audit opinion is contemporaneous with the fiscal year and both labels are produced by
auditors and regulators whose capacity varies over time - and text extraction from
heterogeneous annual-report PDFs can introduce measurement error. As a
result, every company-level output is labelled a review-priority signal, not a statement of
disclosure quality, fraud, or misconduct.

For future work, the same framework could be extended to non-manufacturing sectors, to a
longer panel, and to richer external outcomes once enforcement and restatement records
mature. The modular pipeline (sample frame → feature construction → anomaly screening →
evaluation → narration) is released with fixed seeds, recorded hyperparameters, and
layer-by-layer CSVs, so the results can be reproduced and audited.
