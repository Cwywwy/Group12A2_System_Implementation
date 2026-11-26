"""Section 5 prose for the 2021–2025 manuscript (v0.4 onwards).

File: src/reporting/manuscript_v04_section5.py
Author: DSW group 12A2
Purpose: hold the wording of section 5 so that the numbers can be refreshed from
         outputs/tables without rewriting sentences. Every figure that reaches
         the page comes from scripts.build_section5.collect_numbers(); this module
         only decides how to say it.
Module: reporting
"""

# Revision history
# 2026-11-26  initial version: section 5 blocks keyed to the docx paragraph slots.

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def _pct(value: float, digits: int = 1) -> str:
    return f"{value * 100:.{digits}f}%"


def _f(value: float, digits: int = 3) -> str:
    return f"{value:.{digits}f}"


def _years(mapping: Mapping[int, float], *, separator: str = "; ") -> str:
    return separator.join(f"{year}: {value:,}" for year, value in sorted(mapping.items()))


def _span(years: Sequence[int]) -> str:
    """Format a run of fiscal years as "2021–2023" or "2021 and 2023"."""
    ordered = sorted({int(year) for year in years})
    if not ordered:
        return "no fiscal year"
    if ordered == list(range(ordered[0], ordered[-1] + 1)):
        return f"{ordered[0]}–{ordered[-1]}"
    if len(ordered) == 1:
        return str(ordered[0])
    return ", ".join(str(year) for year in ordered[:-1]) + f" and {ordered[-1]}"


def _shares(mapping: Mapping[int, float]) -> str:
    return "; ".join(f"{year}: {value * 100:.1f}%" for year, value in sorted(mapping.items()))


def _ranking(num: Mapping[str, Any], outcome: str, label: str) -> Mapping[str, float]:
    return num["events"]["ranking"][(outcome, label)]


def _supervised(num: Mapping[str, Any], outcome: str, clf: str, arm: str) -> Mapping[str, float]:
    return num["events"]["supervised"][(outcome, clf, arm)]


def _auc(bundle: Mapping[str, float]) -> str:
    return f"{bundle['auc']:.3f} [{bundle['auc_lo']:.3f}, {bundle['auc_hi']:.3f}]"


def _p(value: float) -> str:
    """Format a p-value, reporting an inequality when it would round to zero."""
    return "< 0.001" if value < 0.001 else f"= {value:.3f}"


def section5(num: Mapping[str, Any]) -> dict[str, str]:
    """Return the paragraphs of section 5, keyed by their slot in the document."""
    first_year = min(num["by_year"])
    last_year = max(num["by_year"])
    span = f"{first_year}–{last_year}"
    opinion = _ranking(num, "mod_opinion", "finance-only IF")
    opinion_beneish = _ranking(num, "mod_opinion", "Beneish M-Score")
    opinion_fused = _ranking(num, "mod_opinion", "fused IF")
    opinion_text = _ranking(num, "mod_opinion", "text-only IF")
    opinion_auto = _ranking(num, "mod_opinion", "fused AE")
    violation = _ranking(num, "violation_disclosure_t1", "finance-only IF")
    violation_beneish = _ranking(num, "violation_disclosure_t1", "Beneish M-Score")
    audit = num["audit"]
    gate = audit["gate"]
    sup_logit = _supervised(num, "mod_opinion", "logit", "fused")
    sup_logit_fin = _supervised(num, "mod_opinion", "logit", "finance")
    sup_logit_text = _supervised(num, "mod_opinion", "logit", "text")
    delta_logit = _supervised(num, "mod_opinion", "logit", "delta_fused_vs_finance")
    sup_gbm_text = _supervised(num, "mod_opinion", "hgb", "text")
    delta_gbm = _supervised(num, "mod_opinion", "hgb", "delta_fused_vs_finance")
    top1, top2, top3 = num["shap_top3"][0], num["shap_top3"][1], num["shap_top3"][2]

    blocks: dict[str, str] = {}

    blocks["s51"] = (
        f"The sample frame contains {num['frame_firms']:,} manufacturing firms and "
        f"{num['frame_years']:,} firm-years over {first_year}–{last_year} "
        f"({_years(num['frame_by_year'])}). Requiring the six financial indicators, the three "
        f"textual indicators and the Beneish inputs leaves {num['n']:,} firm-years from "
        f"{num['n_firms']:,} firms, or {_pct(num['share'])} of the frame "
        f"({_years(num['by_year'])}). The surviving panel is therefore close to the population "
        f"of A-share manufacturers rather than a convenience subsample; Appendix B.5 sets out "
        f"every attrition step between the two counts."
    )

    blocks["s52_intro"] = (
        "Table 5.1 opens the descriptive account with the rank correlation between each anomaly "
        "ranking and the Beneish M-Score, the benchmark every earlier study of Chinese "
        "manufacturing uses. Figure 5.1 shows the same coefficients, Figure 5.2 the event "
        "enrichment they imply, and Appendix B.1 the raw distributions of the nine inputs."
    )

    blocks["s52_skew"] = (
        "Two properties of those inputs shape the rest of the design. The financial ratios carry "
        "heavy right tails — receivables turnover and revenue growth in particular — which is why "
        "every feature is winsorised at the 1st and 99th percentiles and standardised within "
        "subindustry-year cells before it reaches a model. The textual indicators move far more "
        "narrowly, so a single standard deviation of sentiment balance is a much smaller shift in "
        "the underlying language than a single standard deviation of accruals is in the accounts."
    )

    blocks["t51_caption"] = (
        f"Table 5.1. Spearman rank correlation between each anomaly ranking and the Beneish "
        f"M-Score (n = {num['n']:,})."
    )

    blocks["s52_after"] = (
        f"All four correlations are close to zero. The finance-only Isolation Forest reaches "
        f"ρ = {_f(num['rho_if_finance'])} (p {_p(num['p_if_finance'])}) and the fused "
        f"autoencoder ρ = {_f(num['rho_ae_fused'])} (p {_p(num['p_ae_fused'])}), so whatever "
        f"the rankings measure, it is essentially independent of the score that dominates the "
        f"Chinese earnings-management literature. Figure 5.2 makes the practical consequence "
        f"concrete: at the top decile the finance-only ranking is "
        f"{_f(num['en_calibrated_if_finance_10'], 2)} times as likely to hold a firm-year that the "
        f"sample-calibrated Beneish rule flags, against "
        f"{_f(num['en_legacy_if_finance_10'], 2)} times under the legacy cut-off — the two "
        f"benchmarks disagree on which firms look risky, not merely on how many."
    )

    blocks["f51_caption"] = (
        "Figure 5.1. Spearman rank correlation between each anomaly ranking and the Beneish "
        "M-Score."
    )

    blocks["f51_note"] = (
        f"Note: finance-only {_f(num['rho_if_finance'])}; text-only {_f(num['rho_if_text'])}; "
        f"fused Isolation Forest {_f(num['rho_if_fused'])}; fused autoencoder "
        f"{_f(num['rho_ae_fused'])}. Stars mark the p < 0.05 threshold."
    )

    blocks["s52_interpret"] = (
        "The sign deserves care. A negative correlation does not mean the pipeline detects less "
        "manipulation than the M-Score; it means the two instruments order firms differently, and "
        "the external outcomes in section 5.6 decide which ordering tracks something a regulator "
        "actually acted on. The low correlation is also a substantive result about the benchmark: "
        "because the M-Score's coefficients were estimated on a much older sample, its ranking "
        "carries little information about where the anomaly detectors place a given firm-year."
    )

    blocks["f52_caption"] = (
        "Figure 5.2. Top-decile enrichment of flagged firm-years under the sample-calibrated "
        "Beneish benchmark."
    )

    blocks["f52_note"] = (
        "Note: enrichment is the event rate inside the top decile divided by the sample-wide "
        "event rate; 1.00× means no better than the base rate. Appendix B.2 repeats the exercise "
        "at the legacy cut-off and at the top 5% and 15%."
    )

    blocks["s53"] = (
        f"Reading a fused model requires knowing which block drives its decisions. On the fused "
        f"Isolation Forest the financial block accounts for {_pct(num['shap_finance'])} of the "
        f"total absolute SHAP mass and the textual block for {_pct(num['shap_text'])}, so the "
        f"text does not simply ride along — roughly one unit of influence in three originates in "
        f"MD&A language. Individually the largest contributors are "
        f"{top1[0].replace('_', ' ')} ({_f(top1[1], 2)}), "
        f"{top2[0].replace('_', ' ')} ({_f(top2[1], 2)}) and "
        f"{top3[0].replace('_', ' ')} ({_f(top3[1], 2)}), which is the group-level counterpart of "
        f"the design choice in section 3.2: one financial ratio and one sentiment measure weigh "
        f"about the same."
    )

    blocks["s54"] = (
        f"Three checks test whether the picture survives changes in specification. The top-decile "
        f"overlap between the finance-only and fused rankings is {_f(num['overlap_fin_fused'])}, "
        f"so fusion reorders a fifth of the queue rather than reproducing it; between the "
        f"finance-only and text-only rankings the overlap falls to {_f(num['overlap_fin_text'])}, "
        f"confirming that the two blocks rank different firms. Replacing the compact lexicon with a "
        f"full Chinese financial sentiment list leaves the correlations and the enrichment ratios "
        f"within sampling noise (Appendix B.3), and the paired increments over the finance block "
        f"stay distinguishable from zero only for the autoencoder (Appendix B.4)."
    )

    blocks["s54_year"] = (
        "The last check is temporal. Appendix B.2 recomputes the Beneish cut-off inside each "
        "fiscal year, and the threshold falls from year to year while the finance-only ranking "
        "keeps the same ordering against audit opinions; Figure 5.3 shows both movements side by "
        "side. A benchmark whose cut-off has to be recalibrated annually cannot support "
        "cross-sectional claims about which year was riskier."
    )

    blocks["s55"] = (
        "The evidence supports one negative and one positive claim. The negative claim is that the "
        "three MD&A indicators add little to a financial-ratio model on the proxy benchmark: the "
        "fused ranking correlates with the M-Score about as weakly as the finance-only ranking, and "
        "the enrichment ratios move by tenths, not multiples. The positive claim is narrower and "
        "more useful: the pipeline ranks firm-years that regulators later acted on far better than "
        "the M-Score does, and it does so without labels, which means it can be run on the "
        "population rather than on a hand-checked subsample."
    )

    blocks["s55_b"] = (
        "Three limitations bound that claim. The external outcomes are rare — "
        f"{num['events']['mod_opinion_count']:,} modified opinions in {num['n']:,} firm-years — so "
        "the confidence intervals on every AUC are wide, and a single year's regulatory campaign "
        "can move them. The textual block is measured on a single language and a single disclosure "
        "channel, so the design says nothing about whether the same signals survive in other "
        "markets or in the earnings-call transcripts some studies prefer. And the pipeline "
        "identifies firm-years worth an auditor's attention; it does not establish misconduct, "
        "which is why section 6 treats the output as a screening device rather than a verdict."
    )

    blocks["s56_a"] = (
        "The Beneish M-Score is a proxy, and the preceding subsections have shown that in this "
        "sample it is a weak one. Two CSMAR outcomes allow a sharper test: the audit opinion "
        "attached to the same annual report, and a disclosure-related regulatory announcement in "
        "the following calendar year. The first is contemporaneous — the auditor saw the same "
        "statements — and measures whether the ranking finds disclosures a professional already "
        "flagged. The second is forward-looking and measures whether the ranking anticipates "
        "trouble that had not yet surfaced."
    )

    blocks["s56_b"] = (
        f"The audit-opinion outcome covers all {num['n']:,} firm-years; the violation outcome only "
        f"the {num['violation_n']:,} firm-years of {_span(num['violation_years'])}, the fiscal years "
        f"whose t+1 window is settled in the vendor snapshot (October 2026). Later years would "
        f"enter with an incomplete forward window — the observed t+1 violation rate falls from "
        f"about 21% to 13.5% in 2024 and 1.0% in 2025 — so they are excluded rather than reported "
        f"as a weak result. The exclusion works against the benchmark rather than for the method: "
        f"scored across all five years the finance-only ranking falls to "
        f"{_f(gate['finance-only IF']['ungated'])} while the M-Score rises to "
        f"{_f(gate['Beneish M-Score']['ungated'])}, so a reader who distrusts the gate should read "
        f"the gap as narrower, not wider. Modified opinions are rare: "
        f"{num['events']['mod_opinion_count']:,} ({_pct(num['events']['mod_opinion_rate'], 2)}), or "
        f"{num['events']['mod_opinion_wide_count']:,} counting explanatory paragraphs, and the "
        f"annual variation in both event rates is reported in Appendix B.6."
    )

    blocks["t52_caption"] = (
        "Table 5.2. Ranking quality against real regulatory outcomes: AUC with 95% confidence "
        "intervals, and the top-decile lift over the base rate."
    )

    blocks["s56_c"] = (
        f"The finance-only Isolation Forest transfers to the audit outcome: AUC {_auc(opinion)}, "
        f"with the top decile holding {_f(opinion['lift_10pct'], 2)} times the base rate and "
        f"capturing {_pct(opinion['recall_10pct'])} of modified opinions. The fused model is "
        f"close behind at {_f(opinion_fused['auc'])}, the autoencoder at "
        f"{_f(opinion_auto['auc'])}, and the text-only ranking is indistinguishable from chance at "
        f"{_f(opinion_text['auc'])}. The Beneish M-Score ranks *below* chance at "
        f"{_f(opinion_beneish['auc'])} [{_f(opinion_beneish['auc_lo'])}, "
        f"{_f(opinion_beneish['auc_hi'])}]: firm-years it calls manipulative are slightly less "
        f"likely to carry a modified opinion. Against the forward-looking violation outcome the "
        f"same ordering holds, at a lower level ({_f(violation['auc'])} for the finance-only "
        f"ranking against {_f(violation_beneish['auc'])} for the M-Score), which is what one "
        f"expects when the outcome depends on enforcement timing as much as on reporting quality. "
        f"The intervals resample firm-years independently; because later years of the same firm "
        f"are correlated, resampling whole firms widens the primary interval from "
        f"[{_f(audit['row_interval'][0])}, {_f(audit['row_interval'][1])}] to "
        f"[{_f(audit['cluster_interval'][0])}, {_f(audit['cluster_interval'][1])}] without "
        f"changing any comparison above."
    )

    blocks["f53_caption"] = (
        "Figure 5.4. AUC of each anomaly ranking against the two external regulatory outcomes."
    )

    blocks["f53_note"] = (
        "Note: modified audit opinion is contemporaneous with the fiscal year; the t+1 violation "
        "label is forward-looking. The dashed line marks chance."
    )

    blocks["t53_caption"] = (
        "Table 5.3. Out-of-fold AUC under firm-grouped five-fold cross-validation, with the "
        "increment of the fused block over finance-only."
    )

    blocks["s56_d"] = (
        f"Table 5.3 asks the complementary supervised question: given the labels, does the text "
        f"block add rank information beyond the financial block? With a logistic classifier the "
        f"finance-only model reaches {_f(sup_logit_fin['auc'])} and the fused model "
        f"{_f(sup_logit['auc'])}, an increment of {_f(delta_logit['auc'])} "
        f"[{_f(delta_logit['lo'])}, {_f(delta_logit['hi'])}]; the gradient-boosted pair moves by "
        f"{_f(delta_gbm['auc'])} [{_f(delta_gbm['lo'])}, {_f(delta_gbm['hi'])}]. Both intervals "
        f"include zero. Text on its own is markedly weaker ({_f(sup_logit_text['auc'])} under the "
        f"logistic model, {_f(sup_gbm_text['auc'])} boosted), so the information in MD&A language "
        f"overlaps heavily with what the financial ratios already carry."
    )

    blocks["s56_e"] = (
        "Two caveats keep this from becoming a headline in favour of fusion. The audit opinion is "
        "contemporaneous, so the table measures identification of disclosures that were already "
        "flagged rather than forecasting; only the violation column is genuinely forward-looking, "
        "and there the gap between finance and fusion is smaller still. And the supervised arms use "
        "the labels that the unsupervised arms never see, which is why the unsupervised finance-only "
        "ranking remains the paper's primary result: it reaches most of the supervised AUC without "
        "being trained on the outcome."
    )

    blocks["appendix_pointer"] = (
        "Appendix A reports four branch experiments that relax the choices held fixed in the main "
        "specification: the industry boundary, the sample window, the text lexicon and the "
        "supervised baseline. Appendix B collects the descriptive and attrition tables."
    )

    holdout = num.get("holdout")
    if holdout:
        blocks["s56_holdout"] = (
            f"The {holdout['year']} fiscal year is held out entirely: both rankings are refitted on "
            f"{holdout['train_span']} and then scored on the {holdout['n']:,} firm-years whose "
            f"reports arrived after that window closed. The finance-only ranking reaches AUC "
            f"{_f(holdout['auc_finance'])} [{_f(holdout['auc_finance_lo'])}, "
            f"{_f(holdout['auc_finance_hi'])}] against "
            f"{holdout['events']:,} modified opinions, and the correlation with the M-Score is "
            f"ρ = {_f(holdout['rho'])}. The interval is wide — a year of this size cannot support "
            f"a precise estimate — but the ordering does not invert, which is the claim the design "
            f"actually needs."
        )

    return blocks


def abstract(num: Mapping[str, Any]) -> tuple[str, str]:
    """Return the two abstract paragraphs, refreshed against the current numbers."""
    first_year = min(num["by_year"])
    last_year = max(num["by_year"])
    opinion = _ranking(num, "mod_opinion", "finance-only IF")
    beneish = _ranking(num, "mod_opinion", "Beneish M-Score")
    deltas = [
        _supervised(num, "mod_opinion", clf, "delta_fused_vs_finance")["auc"]
        for clf in ("logit", "hgb")
    ]
    first = (
        f"This study develops and evaluates an explainable anomaly-screening framework for the "
        f"annual reports of Chinese A-share manufacturing firms between {first_year} and "
        f"{last_year}. Finance-only, text-only and fused feature matrices are compared on a common "
        f"sample and evaluation design: six financial indicators cover profitability, leverage, "
        f"growth, operating cash flow, receivables efficiency and accrual-related risk, and three "
        f"MD&A indicators cover readability, sentiment balance and uncertainty. Isolation Forest is "
        f"the primary ranking model and an autoencoder an alternative, with SHAP attribution at the "
        f"global and firm-year level. The rankings are evaluated first against the Beneish M-Score "
        f"as an accounting-risk proxy, then against audit opinions and regulatory violations."
    )
    second = (
        f"The most robust result concerns the benchmark rather than the text. Across {num['n']:,} "
        f"firm-years from {num['n_firms']:,} firms ({_pct(num['share'])} of the "
        f"{num['frame_years']:,}-row frame), the finance-only Isolation Forest separates firm-years "
        f"carrying a modified audit opinion at AUC {_f(opinion['auc'])}, whereas the Beneish "
        f"M-Score ranks the same firm-years below chance at AUC {_f(beneish['auc'])}. Against the "
        f"Beneish benchmark the finance-only correlation is ρ = {_f(num['rho_if_finance'])} "
        f"(p {_p(num['p_if_finance'])}) and the fused model reaches ρ = "
        f"{_f(num['rho_if_fused'])} (p {_p(num['p_if_fused'])}), so MD&A text adds no measurable "
        f"incremental value to a Beneish-style screen. Supervised increments from adding text range "
        f"from {_f(min(deltas))} to {_f(max(deltas))} and none excludes zero. The contribution is an "
        f"empirical demonstration that the Beneish score cannot serve as an audit-risk proxy in "
        f"this setting, together with an honest null for MD&A text; the scores are review-priority "
        f"signals, not measures of disclosure quality, fraud or misconduct."
    )
    return first, second


def conclusion(num: Mapping[str, Any]) -> str:
    """Return the closing paragraph, refreshed against the current numbers."""
    first_year = min(num["by_year"])
    last_year = max(num["by_year"])
    opinion = _ranking(num, "mod_opinion", "finance-only IF")
    beneish = _ranking(num, "mod_opinion", "Beneish M-Score")
    violation = _ranking(num, "violation_disclosure_t1", "finance-only IF")
    deltas = [
        abs(_supervised(num, outcome, clf, "delta_fused_vs_finance")["auc"])
        for outcome in ("mod_opinion", "violation_disclosure_t1")
        for clf in ("logit", "hgb")
    ]
    return (
        f"This study developed and evaluated a reproducible anomaly-screening pipeline for Chinese "
        f"A-share manufacturing firms over {first_year}–{last_year}. It compared finance-only, "
        f"text-only and fused feature sets under Isolation Forest and an autoencoder, and examined "
        f"feature contributions with SHAP. Two conclusions follow. The first concerns the benchmark: "
        f"the Beneish M-Score cannot stand in for audit risk in this sample, because it ranks "
        f"firm-years with contemporaneous modified opinions below the rest of the panel (AUC "
        f"{_f(beneish['auc'])}) while a finance-only ranking reaches {_f(opinion['auc'])}, and "
        f"because its coefficients reward the accruals and sales growth that distressed firms lack. "
        f"The second is the null for text: against that benchmark the three MD&A indicators add no "
        f"incremental value to a Beneish-style screen, and in supervised cross-validation the fused "
        f"increment never exceeds {_f(max(deltas))} in absolute value with every interval covering "
        f"zero. That null is bounded rather than general: across four sample frames, a per-year "
        f"threshold recalibration and six outcome labels (Appendix A) the ordering never reverses, "
        f"while the text block used on its own is consistently weaker than the financial block. "
        f"Forward-looking t+1 discrimination remains weak (AUC {_f(violation['auc'])}), which bounds "
        f"what a screen built on annual-report language can promise. The ethical boundary follows "
        f"from that reading: a score identifies a report worth a second look, and using it to "
        f"penalise a firm would turn a screening signal into an accusation the design cannot "
        f"support."
    )


def section5_tables(num: Mapping[str, Any]) -> dict[int, list[list[str]]]:
    """Return the three body tables of section 5 as plain string grids.

    The keys are the position of the table in ``Document.tables`` for the v0.4
    file: 0 is the correlation table, 1 the external-outcome table and 2 the
    supervised comparison.
    """
    correlations = [["Model", "Spearman rho", "p-value"]]
    for model, label in (
        ("if_finance", "Finance-only IF"),
        ("if_text", "Text-only IF"),
        ("if_fused", "Fused IF"),
        ("ae_fused", "Fused autoencoder"),
    ):
        correlations.append(
            [label, f"{num[f'rho_{model}']:.3f}",
             "< 0.001" if num[f"p_{model}"] < 0.001 else f"{num[f'p_{model}']:.3f}"]
        )

    external = [["Score", "AUC: opinion", "AUC: disclosure violation t+1",
                 "Lift: opinion", "Lift: disclosure violation"]]
    for label in ("finance-only IF", "text-only IF", "fused IF", "fused AE", "Beneish M-Score"):
        opinion = _ranking(num, "mod_opinion", label)
        violation = _ranking(num, "violation_disclosure_t1", label)
        external.append(
            [
                label,
                f"{opinion['auc']:.3f}",
                f"{violation['auc']:.3f}",
                f"{opinion['lift_10pct']:.2f}",
                f"{violation['lift_10pct']:.2f}",
            ]
        )

    supervised = [["Feature set", "Model", "AUC: opinion", "ΔAUC vs finance",
                   "AUC: disclosure violation t+1", "ΔAUC vs finance"]]
    for arm, arm_label in (("finance", "Finance only"), ("text", "Text only"), ("fused", "Fused")):
        for clf, clf_label in (("logit", "Logit"), ("hgb", "Gradient boosting")):
            opinion = _supervised(num, "mod_opinion", clf, arm)
            violation = _supervised(num, "violation_disclosure_t1", clf, arm)
            if arm == "fused":
                delta_opinion = _supervised(num, "mod_opinion", clf, "delta_fused_vs_finance")
                delta_violation = _supervised(
                    num, "violation_disclosure_t1", clf, "delta_fused_vs_finance"
                )
                d_opinion = f"{delta_opinion['auc']:.3f}"
                d_violation = f"{delta_violation['auc']:.3f}"
            else:
                d_opinion = "-"
                d_violation = "-"
            supervised.append(
                [
                    arm_label,
                    clf_label,
                    f"{opinion['auc']:.3f}",
                    d_opinion,
                    f"{violation['auc']:.3f}",
                    d_violation,
                ]
            )

    return {0: correlations, 1: external, 2: supervised}
