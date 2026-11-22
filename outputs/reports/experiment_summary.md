# 实验摘要（自动生成）

- 生成时间：2026-11-23 02:27
- 有效样本：9239 个 firm-year（9 特征 + M-Score 完整）

## Spearman 秩相关（异常得分 vs Beneish M-Score）

| 模型 | ρ |
| --- | --- |
| if_finance | -0.0214 |
| if_text | -0.0259 |
| if_fused | -0.0176 |
| ae_fused | -0.0066 |

## top-10% 审查名单表现（样本校准基准：M-Score top-10%）

| 模型 | 事件率 | 富集率 |
| --- | --- | --- |
| if_finance | 0.2446 | 2.4456 |
| if_text | 0.0909 | 0.909 |
| if_fused | 0.21 | 2.0993 |
| ae_fused | 0.1959 | 1.9587 |

## top-10% 审查名单表现（legacy 基准：M > -1.78）

| 模型 | 事件率 | 富集率 |
| --- | --- | --- |
| if_finance | 0.3084 | 1.6902 |
| if_text | 0.1526 | 0.8362 |
| if_fused | 0.2846 | 1.5597 |
| ae_fused | 0.2868 | 1.5716 |

- IF-融合模型审查优先第 1 名：600870

图件见 outputs/figures/，明细表见 outputs/tables/。