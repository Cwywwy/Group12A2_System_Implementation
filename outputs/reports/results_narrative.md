# Results (auto-narrated)

_Generated from outputs/tables; review, discuss, and delete this header for the final chapter._

## RQ1: Incremental value of textual features

| Model | Spearman rho (vs M-Score) | p-value |
| --- | --- | --- |
| Finance-only IF | 0.136 | 0.000 |
| Text-only IF | -0.030 | 0.008 |
| Fused IF | 0.103 | 0.000 |
| Fused autoencoder | 0.012 | 0.272 |

The finance-only score correlates with the M-Score at rho = 0.136, the text-only score at rho = -0.030, and the fused score at rho = 0.103. The fused score does not improve rank agreement with the accounting benchmark over the finance-only score in this sample.

## RQ2: Feature group contributions

| Group | Share of absolute SHAP | Features |
| --- | --- | --- |
| finance | 0.659 | 6 |
| text | 0.341 | 3 |

The largest global SHAP contributions come from ocf_to_assets (0.324), revenue_growth (0.317), readability (0.315).
For the top-ranked firm-year, the largest local drivers are 2.197 in absolute SHAP; the feature with the largest absolute value is receivables_turnover.

## RQ3: Ranking stability

| Pair | Top-10% overlap |
| --- | --- |
| if_finance vs if_text | 0.120 |
| if_finance vs if_fused | 0.828 |
| if_finance vs ae_fused | 0.369 |
| if_text vs if_finance | 0.120 |
| if_text vs if_fused | 0.264 |
| if_text vs ae_fused | 0.155 |
| if_fused vs if_finance | 0.828 |
| if_fused vs if_text | 0.264 |
| if_fused vs ae_fused | 0.367 |
| ae_fused vs if_finance | 0.369 |
| ae_fused vs if_text | 0.155 |
| ae_fused vs if_fused | 0.367 |

| Model | k | Event rate (M> -1.78) | Enrichment |
| --- | --- | --- | --- |
| if_finance | 0.05 | 0.860 | 1.370 |
| if_finance | 0.1 | 0.764 | 1.217 |
| if_finance | 0.15 | 0.733 | 1.168 |
| if_text | 0.05 | 0.563 | 0.896 |
| if_text | 0.1 | 0.574 | 0.914 |
| if_text | 0.15 | 0.591 | 0.942 |
| if_fused | 0.05 | 0.835 | 1.331 |
| if_fused | 0.1 | 0.738 | 1.176 |
| if_fused | 0.15 | 0.712 | 1.134 |
| ae_fused | 0.05 | 0.634 | 1.010 |
| ae_fused | 0.1 | 0.625 | 0.996 |
| ae_fused | 0.15 | 0.620 | 0.988 |

At the top-10% review threshold the fused model flags a flag rate of 0.738 against the M-Score benchmark, i.e. 1.176x the sample-wide benchmark rate, which supports its use as a screening signal rather than a definitive risk label.

Sample descriptives: see descriptives_summary.md.
