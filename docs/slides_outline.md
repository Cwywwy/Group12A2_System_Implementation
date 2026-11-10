# 演示大纲（15 Dec，Option 2：12 页 / 12 分钟）

> 状态：骨架稿。真实数字到位后替换所有 `{占位}`。
> 12 页成品已由 `scripts/build_slides.py` 生成（`outputs/slides/Group12A2_Deck.pptx`），本文件用于讲解分工与叙述顺序。
> 分工建议：每页 1 人讲解 1 分钟；附录页不计入 12 页。

## 第 1 页 标题页
- 题目：Screening Financial Disclosure Risk through Textual-Financial Feature Fusion and Explainable Anomaly Detection: Evidence from Chinese A-share Manufacturing Firms, 2021–2023
- 组员四人姓名/学号、课程（Intro FinTech）、日期

## 第 2 页 动机与问题（对应 RQ 引入）
- 披露质量是监管审查的关键输入；人工审查成本高
- 三类 RQ：{占位：RQ1 文本增量价值 / RQ2 特征组贡献 / RQ3 排序稳定性}

## 第 3 页 数据（10 秒讲清规模）
- CSMAR 三表（2020–2023，合并口径） + 巨潮年报 MD&A（2021–2023）
- 样本：3,694 家制造业 / 10,172 firm-year；{占位：最终覆盖统计}

## 第 4 页 方法总览（管线图）
- 5 模块单向流：数据接入 → 特征 → 建模 → 评估 → 成文（配 pipeline 架构图）

## 第 5 页 特征（一页公式表）
- 6 金融特征 + 3 文本特征 + 标准化（组内 z，稀疏 fallback）
- {占位：特征描述统计简表}

## 第 6 页 模型与阈值
- Isolation Forest（500 树、max_samples=256、SEED=42）+ autoencoder 稳健性
- 审查阈值 top-10%（5%/15% 敏感性）

## 第 7 页 主结果（RQ1）
- {占位：Spearman ρ 表格}、{占位：top-10% 事件率与富集率柱图}

## 第 8 页 SHAP 解释（RQ2）
- {占位：特征组贡献图}、{占位：全局重要性图}

## 第 9 页 稳健性（RQ3 + AE）
- {占位：四路排名重叠热力图}、{占位：AE 结果}

## 第 10 页 局限与边界
- 词典为公开金融情感词表（姚加权等 2021 正式版）、扫描件标记、M-Score 仅作基准（legacy −1.78 与样本 top-10% 双口径）、只作排序信号不自动定性

## 第 11 页 可复现性
- SEED=42、requirements.txt 冻结、增量日志、复现指南 docs/reproducibility_guide.md

## 第 12 页 结论与分工
- 结论一句话：{占位}
- 分工表：{占位：四人各自贡献}

## 附录（不计入 12 页）
- 失败案例 QC 清单、审计结果、CSMAR/巨潮版权声明页
