# 实验摘要（自动生成）

- 生成时间：2026-11-11 01:45
- 有效样本：8140 个 firm-year（9 特征 + M-Score 完整）

## Spearman 秩相关（异常得分 vs Beneish M-Score）

| 模型 | ρ |
| --- | --- |
| if_finance | 0.1357 |
| if_text | -0.0295 |
| if_fused | 0.1028 |
| ae_fused | 0.0122 |

## top-10% 审查名单表现（样本校准基准：M-Score top-10%）

| 模型 | 事件率 | 富集率 |
| --- | --- | --- |
| if_finance | 0.1867 | 1.8673 |
| if_text | 0.1069 | 1.0688 |
| if_fused | 0.1904 | 1.9042 |
| ae_fused | 0.1253 | 1.2531 |

## top-10% 审查名单表现（legacy 基准：M > -1.78）

| 模型 | 事件率 | 富集率 |
| --- | --- | --- |
| if_finance | 0.7641 | 1.2172 |
| if_text | 0.5737 | 0.9139 |
| if_fused | 0.7383 | 1.1761 |
| ae_fused | 0.6253 | 0.9961 |

- IF-融合模型审查优先第 1 名：820

图件见 outputs/figures/，明细表见 outputs/tables/。