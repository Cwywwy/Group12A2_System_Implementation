const BODY = {
  horizontalAlign: 5,
  lineSpacing: 1.5,
  spacingRule: 0,
  spaceBelow: { v: 8 },
  textStyle: { ff: "Times New Roman", fs: 11 },
};
const HEAD = {
  horizontalAlign: 5,
  lineSpacing: 1.5,
  spacingRule: 0,
  spaceBelow: { v: 8 },
};

const S5_1 = "The sample frame contains 3,694 manufacturing firms and 10,172 firm-years (2021: 3,165; 2022: 3,404; 2023: 3,603). After merging the six financial features, the three textual features and the Beneish M-Score, 8,140 firm-years (80.0%) across 3,265 firms have complete data and enter the main analysis (2021: 2,430; 2022: 2,769; 2023: 2,941). MD&A text availability is high: 9,991 rows are of good quality, 7 are flagged as suspicious (scanned reports or fewer than 300 tokens) and 174 have no usable text; the yearly usable shares are 96.5% (2021), 99.0% (2022) and 99.0% (2023). The download audit verified 10,051 PDFs correct out of 10,172 (98.8%); the 121 missing files are mostly pre-listing OTC (NEEQ) years of Beijing Stock Exchange firms that CNINFO does not archive.";

const S5_2 = "Table 5.1 (descriptive statistics, in the accompanying data appendix) reports the raw distributions of the nine features; the financial features are right-skewed with heavy tails, which is why the pipeline winsorises each feature at the 1st and 99th percentiles before standardisation. The benchmark (Beneish M-Score above -1.78) marks 5,110 of the 8,140 usable firm-years (62.8%) as red flags, a much higher share than in Beneish's original US sample, so it is treated only as a weak external reference, never as a training label. Table 5.2 reports the Spearman rank correlation between each ranking and the M-Score: finance-only IF 0.136 (p < 0.001), text-only IF -0.030 (p = 0.008), fused IF 0.103 (p < 0.001) and fused autoencoder 0.012 (p = 0.272). Table 5.3 reports the top-k event rates and enrichment ratios: at the top-10% threshold the finance-only enrichment is 1.217 (1.370 at top-5%) and the fused enrichment is 1.176 (1.331 at top-5%), while the text-only enrichment is 0.914 and the autoencoder 0.996. The finance-only model therefore shows a weak but highly significant positive rank agreement with the benchmark, and adding the three textual features does not improve the ranking (fused rho 0.103 < finance-only 0.136). RQ1 is answered in the negative: in this sample, textual tone features do not add incremental value over the financial features for flagging Beneish-style red flags.";

const S5_3 = "On the fused model, the financial group accounts for 65.9% of the total absolute SHAP contribution and the textual group for 34.1%. The three most important global features are ocf_to_assets (0.324), revenue_growth (0.317) and readability (0.315), so the two groups both contribute but the financial side dominates, consistent with RQ1. The top-ranked firm-year is firm 000820 (2021, sub-industry C42), with a fused anomaly score of 0.767 and a very high M-Score of 1,077.5. Its largest local SHAP driver is receivables_turnover, followed by revenue_growth and ocf_to_assets, indicating an unusually large receivables/revenue combination relative to its subindustry-year peers.";

const S5_4 = "The top-10% overlap between the finance-only and fused rankings is 0.828 (they largely agree because the fused model is dominated by financial features), while the finance-only versus text-only overlap is only 0.120 (the two signals rank very different firms). The autoencoder reconstruction-error ranking does not replicate the main result: its correlation with the benchmark is 0.012 (p = 0.272) and its top-10% enrichment is 0.996 (no better than chance). The finding is therefore sensitive to the modelling choice and should be read as a screening signal, not a stable risk label.";

const S5_5 = "The score is a review-priority ranking signal, not a verdict on fraud. The benchmark itself is imperfect in this setting: the -1.78 cut-off flags 62.8% of the sample, so the enrichment ratios are diluted relative to a low-incidence benchmark. Known approximations include bootstrap-sized sentiment and uncertainty dictionaries, substring counting, exclusion of scanned or unreadable reports, sparse subindustry-year standardisation fallback, and the use of the M-Score as a proxy for disclosure risk. These are disclosed in the reproducibility guide.";

const ABSTRACT_ADD = " On the final sample of 8,140 firm-years, the fused ranking correlates weakly but significantly with the Beneish M-Score (Spearman rho 0.103, p < 0.001); the finance-only ranking correlates more strongly (0.136), and adding the three MD&A textual features does not improve the ranking, while the top-10% review list enriches Beneish flags by a factor of 1.18.";

const REF22 = "[22] YAO J, et al. Sentiment analysis of textual information disclosure in Chinese listed companies[J]. 2021. (in Chinese)";
const REF23 = "[23] LOUGHRAN T, MCDONALD B. When is a liability not a liability? Textual analysis, dictionaries, and 10-Ks[J]. Journal of Finance, 2011, 66(1): 35-65.";
const REF24 = "[24] ZENG Q, et al. Annual-report tone and uncertainty in Chinese listed firms. 2018. (in Chinese)";

function findIdxByPrefix(prefix) {
  const paras = doc.getParagraphs();
  for (let i = 0; i < paras.length; i++) {
    const t = paras[i].getText();
    if (t && t.indexOf(prefix) === 0) return i;
  }
  return -1;
}

const paras = doc.getParagraphs();
const s5Idx = findIdxByPrefix("5. Experimental Design, Evaluation, and Robustness");
const s6Idx = findIdxByPrefix("6. Expected Outputs, Limitations, and Ethical Boundary");
const lastRefIdx = findIdxByPrefix("[21]");
const abstractIdx = findIdxByPrefix("This proposal develops");
if (s5Idx < 0) throw new Error("§5 heading not found");
if (s6Idx < 0) throw new Error("§6 heading not found");
if (lastRefIdx < 0) throw new Error("[21] reference not found");
if (abstractIdx < 0) throw new Error("abstract body not found");

// 1. Replace §5 headings and bodies (setText keeps paragraph count stable).
paras[s5Idx].setText("5. Experiment and Results");
paras[s5Idx + 1].setText("5.1 Final Sample and Data Coverage");
paras[s5Idx + 2].setText(S5_1);
paras[s5Idx + 3].setText("5.2 Descriptive Statistics and Main Results (RQ1)");
paras[s5Idx + 4].setText(S5_2);
paras[s5Idx + 5].setText("5.3 Group Contributions (RQ2)");
paras[s5Idx + 6].setText(S5_3);

// 2. Append the result sentence to the abstract.
paras[abstractIdx].appendText(ABSTRACT_ADD);

// 3. Insert 5.4 and 5.5 before the §6 heading (4 paragraphs).
const p54h = doc.insertParagraph(s6Idx, "5.4 Robustness (RQ3)");
p54h.setStyle(HEAD);
const p54b = doc.insertParagraph(s6Idx + 1, S5_4);
p54b.setStyle(BODY);
const p55h = doc.insertParagraph(s6Idx + 2, "5.5 Discussion and Limitations");
p55h.setStyle(HEAD);
const p55b = doc.insertParagraph(s6Idx + 3, S5_5);
p55b.setStyle(BODY);

// 4. Insert three new references after [21] (which has now shifted by 4).
const shiftedLastRef = lastRefIdx + 4;
const r22 = doc.insertParagraph(shiftedLastRef + 1, REF22);
r22.setStyle(BODY);
const r23 = doc.insertParagraph(shiftedLastRef + 2, REF23);
r23.setStyle(BODY);
const r24 = doc.insertParagraph(shiftedLastRef + 3, REF24);
r24.setStyle(BODY);

const total = doc.getParagraphs().length;
const head5 = doc.findParagraphByText("5. Experiment and Results");
const head54 = doc.findParagraphByText("5.4 Robustness (RQ3)");
const head55 = doc.findParagraphByText("5.5 Discussion and Limitations");
const ref24 = doc.findParagraphByText(REF24);
return JSON.stringify({
  totalParagraphs: total,
  newSection5: !!head5,
  new54: !!head54,
  new55: !!head55,
  newRef24: !!ref24,
});
