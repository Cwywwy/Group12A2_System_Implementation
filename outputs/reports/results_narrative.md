# Results (auto-narrated)

_Generated from outputs/tables; review, discuss, and delete this header for the final chapter._

## RQ1: Incremental value of textual features

| Model | Spearman rho (vs M-Score) | p-value |
| --- | --- | --- |
| Finance-only IF | -0.021 | 0.040 |
| Text-only IF | -0.026 | 0.013 |
| Fused IF | -0.018 | 0.091 |
| Fused autoencoder | -0.007 | 0.528 |

The finance-only score correlates with the M-Score at rho = -0.021, the text-only score at rho = -0.026, and the fused score at rho = -0.018. Adding the three textual features raises rank agreement with the accounting benchmark, consistent with the expectation that disclosure tone carries incremental information.

## RQ2: Feature group contributions

| Group | Share of absolute SHAP | Features |
| --- | --- | --- |
| finance | 0.662 | 6 |
| text | 0.338 | 3 |

The largest global SHAP contributions come from accruals_to_assets (0.314), revenue_growth (0.312), sentiment_balance (0.304).
For the top-ranked firm-year, the largest local drivers are 2.352 in absolute SHAP; the feature with the largest absolute value is receivables_turnover.

## RQ3: Ranking stability

| Pair | Top-10% overlap |
| --- | --- |
| if_finance vs if_text | 0.132 |
| if_finance vs if_fused | 0.797 |
| if_finance vs ae_fused | 0.455 |
| if_text vs if_finance | 0.132 |
| if_text vs if_fused | 0.286 |
| if_text vs ae_fused | 0.119 |
| if_fused vs if_finance | 0.797 |
| if_fused vs if_text | 0.286 |
| if_fused vs ae_fused | 0.407 |
| ae_fused vs if_finance | 0.455 |
| ae_fused vs if_text | 0.119 |
| ae_fused vs if_fused | 0.407 |

| Benchmark | Model | k | Event rate | Enrichment |
| --- | --- | --- | --- | --- |
| M > -1.78 | if_finance | 0.05 | 0.275 | 1.506 |
| M > -1.78 | if_finance | 0.1 | 0.308 | 1.690 |
| M > -1.78 | if_finance | 0.15 | 0.312 | 1.712 |
| M > -1.78 | if_text | 0.05 | 0.158 | 0.866 |
| M > -1.78 | if_text | 0.1 | 0.153 | 0.836 |
| M > -1.78 | if_text | 0.15 | 0.165 | 0.905 |
| M > -1.78 | if_fused | 0.05 | 0.271 | 1.483 |
| M > -1.78 | if_fused | 0.1 | 0.285 | 1.560 |
| M > -1.78 | if_fused | 0.15 | 0.302 | 1.653 |
| M > -1.78 | ae_fused | 0.05 | 0.310 | 1.696 |
| M > -1.78 | ae_fused | 0.1 | 0.287 | 1.572 |
| M > -1.78 | ae_fused | 0.15 | 0.271 | 1.487 |
| M top-10% | if_finance | 0.05 | 0.223 | 2.229 |
| M top-10% | if_finance | 0.1 | 0.245 | 2.446 |
| M top-10% | if_finance | 0.15 | 0.234 | 2.337 |
| M top-10% | if_text | 0.05 | 0.110 | 1.104 |
| M top-10% | if_text | 0.1 | 0.091 | 0.909 |
| M top-10% | if_text | 0.15 | 0.097 | 0.974 |
| M top-10% | if_fused | 0.05 | 0.214 | 2.143 |
| M top-10% | if_fused | 0.1 | 0.210 | 2.099 |
| M top-10% | if_fused | 0.15 | 0.216 | 2.157 |
| M top-10% | ae_fused | 0.05 | 0.223 | 2.229 |
| M top-10% | ae_fused | 0.1 | 0.196 | 1.959 |
| M top-10% | ae_fused | 0.15 | 0.178 | 1.782 |

At the top-10% review threshold the fused model flags 0.210 of the sample-calibrated benchmark (top-decile M-Score), i.e. 2.099x the 10% benchmark rate, which supports its use as a screening signal rather than a definitive risk label.

Sample descriptives: see descriptives_summary.md.
