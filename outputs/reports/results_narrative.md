# Results (auto-narrated)

_Generated from outputs/tables; review, discuss, and delete this header for the final chapter._

## RQ1: Incremental value of textual features

| Model | Spearman rho (vs M-Score) | p-value |
| --- | --- | --- |
| Finance-only IF | 0.136 | 0.000 |
| Text-only IF | -0.029 | 0.008 |
| Fused IF | 0.103 | 0.000 |
| Fused autoencoder | 0.009 | 0.409 |

The finance-only score correlates with the M-Score at rho = 0.136, the text-only score at rho = -0.029, and the fused score at rho = 0.103. The fused score does not improve rank agreement with the accounting benchmark over the finance-only score in this sample.

## RQ2: Feature group contributions

| Group | Share of absolute SHAP | Features |
| --- | --- | --- |
| finance | 0.654 | 6 |
| text | 0.346 | 3 |

The largest global SHAP contributions come from ocf_to_assets (0.322), revenue_growth (0.320), readability (0.317).
For the top-ranked firm-year, the largest local drivers are 2.190 in absolute SHAP; the feature with the largest absolute value is receivables_turnover.

## RQ3: Ranking stability

| Pair | Top-10% overlap |
| --- | --- |
| if_finance vs if_text | 0.111 |
| if_finance vs if_fused | 0.817 |
| if_finance vs ae_fused | 0.373 |
| if_text vs if_finance | 0.111 |
| if_text vs if_fused | 0.256 |
| if_text vs ae_fused | 0.147 |
| if_fused vs if_finance | 0.817 |
| if_fused vs if_text | 0.256 |
| if_fused vs ae_fused | 0.362 |
| ae_fused vs if_finance | 0.373 |
| ae_fused vs if_text | 0.147 |
| ae_fused vs if_fused | 0.362 |

| Benchmark | Model | k | Event rate | Enrichment |
| --- | --- | --- | --- | --- |
| M > -1.78 | if_finance | 0.05 | 0.860 | 1.370 |
| M > -1.78 | if_finance | 0.1 | 0.764 | 1.217 |
| M > -1.78 | if_finance | 0.15 | 0.733 | 1.168 |
| M > -1.78 | if_text | 0.05 | 0.531 | 0.845 |
| M > -1.78 | if_text | 0.1 | 0.579 | 0.922 |
| M > -1.78 | if_text | 0.15 | 0.587 | 0.935 |
| M > -1.78 | if_fused | 0.05 | 0.845 | 1.346 |
| M > -1.78 | if_fused | 0.1 | 0.752 | 1.198 |
| M > -1.78 | if_fused | 0.15 | 0.713 | 1.135 |
| M > -1.78 | ae_fused | 0.05 | 0.631 | 1.006 |
| M > -1.78 | ae_fused | 0.1 | 0.624 | 0.994 |
| M > -1.78 | ae_fused | 0.15 | 0.621 | 0.989 |
| M top-10% | if_finance | 0.05 | 0.256 | 2.555 |
| M top-10% | if_finance | 0.1 | 0.187 | 1.867 |
| M top-10% | if_finance | 0.15 | 0.164 | 1.638 |
| M top-10% | if_text | 0.05 | 0.091 | 0.909 |
| M top-10% | if_text | 0.1 | 0.085 | 0.848 |
| M top-10% | if_text | 0.15 | 0.089 | 0.893 |
| M top-10% | if_fused | 0.05 | 0.273 | 2.727 |
| M top-10% | if_fused | 0.1 | 0.184 | 1.843 |
| M top-10% | if_fused | 0.15 | 0.153 | 1.532 |
| M top-10% | ae_fused | 0.05 | 0.138 | 1.376 |
| M top-10% | ae_fused | 0.1 | 0.125 | 1.253 |
| M top-10% | ae_fused | 0.15 | 0.115 | 1.155 |

At the top-10% review threshold the fused model flags 0.184 of the sample-calibrated benchmark (top-decile M-Score), i.e. 1.843x the 10% benchmark rate, which supports its use as a screening signal rather than a definitive risk label.

Sample descriptives: see descriptives_summary.md.
