# 6. Conclusion

File:     docs/manuscript_conclusion_section.md
Author:   Group12A2 DSW Team
Purpose:  conclusion section for the final manuscript (Option 2), draft with one
          placeholders for the headline result sentence.

Revision History:
  2026-11-06  initial draft.

---

This study built a reproducible, explainable screening framework that combines six
structured financial indicators with three Chinese MD&A textual indicators, and used it
to rank firm-year observations across Chinese A-share manufacturing firms over 2021–2023.
Isolation Forest served as the primary unsupervised detector and an autoencoder provided a
robustness ranking; SHAP attribution showed, at the global and firm-year levels, whether
each score was driven by the financial or the textual group.

[HEADLINE RESULT — replace after run_99/run_12: state whether the fused ranking showed a
stronger Spearman association with the Beneish M-Score than the finance-only ranking, and
give the top-10% event rate and enrichment ratio.]

Three conclusions follow. First, the fused textual-financial representation
[did / did not] add incremental screening value over the finance-only representation,
which answers RQ1 on the marginal information content of Chinese MD&A. Second, SHAP
decomposition showed that the [financial / textual] group contributed the larger share of
absolute importance (RQ2), indicating where a reviewer's attention is best directed.
Third, the top-10% ranking was [stable / unstable] across review thresholds, model
mechanisms, and sample years (RQ3), which bounds how confidently the queue can be used.

The main limitations are inherent to the design and are reported rather than hidden. The
sample is confined to manufacturing and to a three-year window; the external benchmarks
(Beneish M-Score and, where available, inquiry letters, enforcement actions, restatements,
and modified audit opinions) are incomplete and are not treated as ground-truth labels; and
text extraction from heterogeneous annual-report PDFs can introduce measurement error. As a
result, every company-level output is labelled a review-priority signal, not a statement of
disclosure quality, fraud, or misconduct.

For future work, the same framework could be extended to non-manufacturing sectors, to a
longer panel, and to richer external outcomes once enforcement and restatement records
mature. The modular pipeline (sample frame → feature construction → anomaly screening →
evaluation → narration) is released with fixed seeds, recorded hyperparameters, and
layer-by-layer CSVs, so the results can be reproduced and audited.
