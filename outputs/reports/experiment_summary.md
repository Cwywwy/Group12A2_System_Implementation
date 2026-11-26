# 实验摘要（自动生成）

- 生成时间：2026-11-26 20:22
- 有效样本：16408 个 firm-year（9 特征 + M-Score 完整）

## Spearman 秩相关（异常得分 vs Beneish M-Score）

| 模型 | ρ |
| --- | --- |
| if_finance | -0.0332 |
| if_text | -0.0206 |
| if_fused | -0.0193 |
| ae_fused | -0.0256 |

## top-10% 审查名单表现（样本校准基准：M-Score top-10%）

| 模型 | 事件率 | 富集率 |
| --- | --- | --- |
| if_finance | 0.2541 | 2.5408 |
| if_text | 0.092 | 0.9201 |
| if_fused | 0.223 | 2.2301 |
| ae_fused | 0.2011 | 2.0107 |

## top-10% 审查名单表现（legacy 基准：M > -1.78）

| 模型 | 事件率 | 富集率 |
| --- | --- | --- |
| if_finance | 0.3023 | 2.0334 |
| if_text | 0.1347 | 0.906 |
| if_fused | 0.2718 | 1.8284 |
| ae_fused | 0.2559 | 1.7218 |

- IF-融合模型审查优先第 1 名：600870

图件见 outputs/figures/，明细表见 outputs/tables/。