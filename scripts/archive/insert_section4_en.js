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

const paras = [
  ["h1", "4. System Implementation and/or Model Development"],
  ["h2", "4.1 Pipeline Overview and Reproducibility"],
  ["b", "Section 3 describes what we plan to do; this section describes what has actually been built so far and how it works. The whole study is implemented as an ordered set of Python scripts rather than a single large program. Each script has one clear job: it reads one input file, performs one step, and writes one output file. This makes the system easy to check, easy to debug, and easy for another person to run again. The scripts are organised into folders for data ingestion, feature construction, models, and reporting, so the responsibilities are separated in an obvious way."],
  ["b", "The pipeline runs through eight main stages in a fixed order. First, the sample is constructed from the CSMAR basic-information table. Second, the three financial statements are parsed into one intermediate table. Third, the downloaded annual-report files are checked against the sample list. Fourth, the MD&A text is extracted from each PDF. Fifth, a quality-control report flags missing or unusual records. Sixth, the finance and text features are combined into one feature table. Seventh, descriptive statistics summarise the sample. Eighth, the models are run and the results are narrated into a readable report. A single script can run this whole chain, and each stage can also be run on its own when only part of the pipeline needs to be repeated."],
  ["b", "Reproducibility is treated as a first-class requirement rather than an afterthought. Every random process uses the same fixed seed (42), so repeating a run on the same data gives the same numbers. All parameter choices are written in one configuration file, and all intermediate results are saved as plain CSV files that can be inspected directly. The code is covered by automated tests, which currently number more than seventy and all pass."],
  ["h2", "4.2 Data Acquisition and Quality Control"],
  ["b", "The sample is built from the CSMAR listed-company basic-information annual table. We keep only manufacturing firms, which we identify with the industry code that starts with the letter \u201cC\u201d, and we keep the study years 2021, 2022 and 2023. The year 2020 is also kept as a base year because some features, such as revenue growth and the Beneish M-Score, need the previous year's numbers. After filtering, the sample contains about 3,700 firms and roughly 10,000 firm-year observations."],
  ["b", "The financial data are taken from three CSMAR consolidated statements: the balance sheet, the income statement, and the cash-flow statement. Only the fields needed by the six financial features are read, which keeps the memory use manageable even though the original files are several hundred megabytes. The annual-report texts are obtained from the CNINFO disclosure website. For each firm-year we download the annual report PDF for the correct disclosure year."],
  ["b", "Downloading thousands of PDFs is where most practical problems appear, so we added a download audit step. After downloading, every file is checked against the sample list, and the outcome is recorded as either usable, missing, or mismatched. The audit for the current run recorded 10,051 usable firm-year files and 121 missing ones. Most of the missing cases are firms that were not yet listed, or had already been delisted, in that year, so they are a data-availability boundary rather than a software failure."],
  ["b", "The text step extracts the management discussion and analysis (MD&A) section from each PDF using the pypdf library. Real-world PDFs are messy: some are scanned, some are damaged, and some have unusual internal structure. The extraction is therefore written to be tolerant. A file that cannot be read is recorded with the status \u201cpdf_error\u201d and skipped, and the batch simply continues with the next file instead of stopping. Progress is saved every 25 files, so if the machine is interrupted the job can resume from its last checkpoint rather than starting from the beginning. All three study years completed extraction with this design."],
  ["h2", "4.3 Feature Engineering"],
  ["b", "The six financial features are return on assets, the liabilities-to-assets ratio, revenue growth, operating cash flow divided by total assets, a receivables-turnover measure, and total accruals divided by total assets. These are common indicators of profitability, leverage, growth, cash-flow quality, and earnings quality. The three text features are computed from the MD&A text: a Chinese readability measure, a sentiment balance measure, and an uncertainty ratio. The sentiment and uncertainty measures are based on a small word list prepared for the Chinese financial context, which we describe as a bootstrap dictionary because of its limited size."],
  ["b", "Before modelling, two pre-processing rules are applied so that a few extreme numbers do not dominate the results. First, values are winsorised at the 1% and 99% levels, which means the most extreme values are pulled back to those boundaries. Second, each feature is standardised within its manufacturing sub-industry and year group, so a firm is compared with similar firms in the same year. When a group has fewer than 20 observations, we fall back to standardising over the whole sample. The same eligible observations are used to build three matrices: a finance-only matrix, a text-only matrix, and a fused matrix with all nine features. Using the same observations keeps the comparison fair."],
  ["h2", "4.4 Model Development"],
  ["b", "The primary model is Isolation Forest. The idea is simple: unusual observations are easier to separate from the rest of the data, so an observation that can be isolated with few splits receives a higher anomaly score. We set the number of trees to 500, the number of samples used to build each tree to 256, and the random seed to 42. The decision rule is fixed in advance: an observation is flagged when its score falls in the top 10% of the sample. We also check the top 5% and top 15% so that the main conclusion does not depend on one particular threshold."],
  ["b", "As a robustness model we train an autoencoder, which is a network that compresses the features into a small middle layer and then tries to rebuild the original features. The reconstruction error, that is the difference between the rebuilt and the original values, is used as an alternative anomaly score: an observation that the model cannot rebuild well is more unusual. The autoencoder uses hidden layers of 16, 8 and 16 units, the ReLU activation function, and the Adam optimiser, and it is trained with the same fixed seed as the main model."],
  ["b", "To explain the rankings we use SHAP, a widely used method that assigns each feature a contribution to the final score. We report three things: the overall importance of each feature, the combined importance of the financial group versus the text group, and a local explanation for the highest-ranked observations. This step is important because the output is meant to support a human reviewer, and a reviewer needs to know why a particular firm-year was ranked as unusual. The explanation only describes the model's reasoning; it does not by itself prove that any firm has misbehaved."],
  ["h2", "4.5 Evaluation Implementation"],
  ["b", "The evaluation is kept strictly separate from model training so that the benchmark cannot leak into the model. We compute the Beneish M-Score, a well-known accounting-based indicator of possible earnings manipulation, from the financial statements, and use it only as an external benchmark. We then measure how closely the anomaly scores agree with the M-Score using Spearman rank correlation. We also compute the event rate and the enrichment ratio for the top 10% queue: the event rate is how often a high-M-Score case appears in the queue, and the enrichment ratio compares that rate with the rate in the whole sample."],
  ["b", "For the third research question, we compare the top-ranked lists produced by the finance-only, text-only, fused and autoencoder models, and by different thresholds, and measure how much they overlap. A high overlap means the ranking is stable; a low overlap means the result is sensitive to small design choices. This comparison is computed from the same feature table, so differences come from the models rather than from different data."],
  ["h2", "4.6 Current Implementation Status and Limitations"],
  ["b", "At the time of writing, the sample construction, the download audit, the MD&A extraction for all three years, the quality-control report, and the descriptive-statistics script are complete and verified by automated tests (more than seventy tests, all passing). The one remaining input dependency is the income statement and the cash-flow statement from CSMAR, which have not yet been placed in the data folder. Once these two files are available, the financial feature table and the full experiment can be run, and the results can be written into the experiment section. The implementation described in this section will not need to change."],
  ["b", "The main limitations are the following. First, the Chinese text dictionary is a small bootstrap version, so the sentiment and uncertainty measures are coarser than a full academic dictionary. Second, PDF extraction introduces some noise, because scanned pages and unusual layouts cannot always be read perfectly. Third, the sample is limited to manufacturing firms over three years, so the results should not be generalised to other industries or periods. Because of these limits, the pipeline should be read as a tool for ordering firms for human review, not as a proof that any specific firm has committed fraud or low-quality disclosure."],
];

const anchor = doc.findParagraphByText("4. Experimental Design, Evaluation, and Robustness");
if (!anchor) throw new Error("anchor paragraph not found");
const anchorIdx = anchor.getInfo().paragraphIndex;

for (let i = 0; i < paras.length; i++) {
  const [kind, text] = paras[i];
  const p = doc.insertParagraph(anchorIdx + i, text);
  const style = kind === "b" ? BODY : HEAD;
  const ok = p.setStyle(style);
  if (!ok) throw new Error("setStyle failed at inserted paragraph " + i);
}

// Renumber the two following sections.
const renames = [
  ["4. Experimental Design, Evaluation, and Robustness", "5. Experimental Design, Evaluation, and Robustness"],
  ["4.1 Common Comparison Design", "5.1 Common Comparison Design"],
  ["4.2 Evaluation Framework", "5.2 Evaluation Framework"],
  ["4.3 Robustness and Heterogeneity", "5.3 Robustness and Heterogeneity"],
  ["5. Expected Outputs, Limitations, and Ethical Boundary", "6. Expected Outputs, Limitations, and Ethical Boundary"],
];
for (const [from, to] of renames) {
  const p = doc.findParagraphByText(from);
  if (!p) throw new Error("rename target not found: " + from);
  const ok = p.setText(to);
  if (!ok) throw new Error("rename failed: " + from);
}

const total = doc.getParagraphs().length;
const head4 = doc.findParagraphByText("4. System Implementation and/or Model Development");
const head5 = doc.findParagraphByText("5. Experimental Design, Evaluation, and Robustness");
const head6 = doc.findParagraphByText("6. Expected Outputs, Limitations, and Ethical Boundary");
return JSON.stringify({
  totalParagraphs: total,
  newSection4: !!head4,
  renumbered5: !!head5,
  renumbered6: !!head6,
});
