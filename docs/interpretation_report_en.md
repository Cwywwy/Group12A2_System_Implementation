# Finding the firms that "might have a problem" in their annual reports: an interpretation guide for complete outsiders

> **What this document is**: a plain-language companion to the paper *Screening Financial Disclosure Risk through Textual–Financial Feature Fusion and Explainable Anomaly Detection: Evidence from Chinese A-share Manufacturing Firms, 2021–2023* (Group 12A2, Introduction to FinTech, 2026). It is not an abstract of the paper; it is a translation of the paper into ordinary language, with every step of the reasoning spelled out.
> **Who it is for**: an intelligent reader with no background in accounting, machine learning or Chinese capital markets. We assume you do not recognise a single term in advance, and we define each term before we rely on it.
> **How to read it**: if you only want the conclusions, read §0. If you want to know why the question is worth asking, read §1–§2. If you want to know what the data look like, read §3–§4. If you want to actually understand the models and the formulas, read §5–§9 — that block is a small handbook of methods and models. If you want to check the results, read §10. If you want to avoid misreading them, read §11.
> **Chinese version**: [`docs/interpretation_report_cn.md`](interpretation_report_cn.md) — the same document, section for section, plus a Chinese–English glossary.

---

## 0. Three-minute overview

| Question | Answer in one sentence |
| --- | --- |
| **What are we trying to solve?** | Manufacturing firms listed in China file annual reports every year, and those reports are numerous and long: ordinary people cannot read them all, and neither can regulators. We want to build an automatic **screener** that moves the dubious-looking firms to the front of the queue. |
| **What did we do?** | We turned each firm into **nine numbers** — six from its financial statements plus three from one stretch of plain prose inside the annual report (the Management Discussion and Analysis, or MD&A) — and then used an algorithm that needs no "right answers" (an **Isolation Forest**) to give every firm an "anomaly score", after which we pulled out the 10% with the highest scores. |
| **What do we test the screener against?** | Two real-world outcomes stand in for "the right answer": (1) the **modified audit opinion** an auditor issued (in plain words: the auditor wrote "I am not fully comfortable signing this off"); (2) whether the firm was **sanctioned or questioned by a regulator in the following year**. |
| **Headline finding 1** | Using the financial numbers alone, we can pick out the firms that will receive a modified audit opinion quite well: the hit rate is **4.95 times** that of random sampling, the top 10% captures **49.5%** of all modified opinions in the sample, and the statistical "ability to tell the two groups apart" (**AUC**) is **0.802** (1.0 would be perfect, 0.5 is a coin toss). For comparison, the most famous fraud model in accounting, the Beneish M-Score, manages only **0.242** on the same task — worse than a coin toss. |
| **Headline finding 2** | Adding the **words** of the annual report (tone, readability, hedging language) **adds essentially nothing** to the screening of modified opinions. The model does use the text features — in the explanation layer, text accounts for 33.8% of the weight — but the accuracy increment from adding text is statistically indistinguishable from zero (the best pairing is +0.012, 95% interval [−0.005, +0.027], which straddles zero). |
| **Headline finding 3** | Text does not help with the other target either (predicting "will this firm be caught in a financial-reporting-type irregularity"): the ranking implied by the text features is almost uncorrelated with the accounting-manipulation yardstick (rank correlation −0.026). In other words, **"read the tone" did not work in our setting** — an honest negative result, reported as such. |
| **The most important boundary** | We built a **screener**, not a **judge**. A high score means only "this firm does not look like most of its peers and is worth a human look". It does not mean the firm broke any law. We have also not demonstrated any causal relationship. |

If you have understood the table above, you already hold about 80% of the information in this paper. The rest of the document takes every phrase in that table apart and explains it properly.

---

## 1. Background: what this is really about

### 1.1 The "homework" every listed company must hand in each year

A company listed on China's A-share market must publish an **annual report** within a fixed deadline every year. A typical manufacturing firm's annual report runs to 150–300 pages and contains:

1. **Three financial statements.** The balance sheet (what the company owns and what it owes at a given instant), the income statement (how much it earned over the year), and the cash-flow statement (how much actual cash moved in and out over the year).
2. **Notes to the financial statements.** Explanations of every line in the three statements — usually ten times longer than the statements themselves.
3. **The audit report.** Issued by an independent accounting firm; effectively a third-party inspection certificate.
4. **The Management Discussion and Analysis (MD&A).** A stretch of plain prose, written by the company's own management, explaining "how business went this year, why it went well or badly, and what we intend to do next year". In a Chinese annual report this section is usually titled "Management Discussion and Analysis" or "Discussion and Analysis of Operations".

For a researcher these four blocks are four different kinds of signal: the statements are **numbers**, the notes are **explanation**, the audit report is a **third-party judgement**, and the MD&A is **the company's own account of itself**.

### 1.2 The two kinds of "bad news" we care about

Two things inside an annual report can serve as objective records that something went wrong.

**Type one: the modified audit opinion (non-standard audit opinion).**
After examining the books, the auditor must state a conclusion. The standard conclusion is an "unqualified opinion", which means "in our view these statements present the company's position fairly, in all material respects". If the auditor is uneasy, a different opinion is issued instead: an unqualified opinion with an emphasis-of-matter paragraph, a qualified opinion, a disclaimer of opinion, or an adverse opinion. All of these are called **modified** (or non-standard) opinions. In everyday language: **the auditor has written "I am not fully comfortable signing this"**.

Among our 9,239 firm-year observations, **204 (2.21%)** carry a clearly modified opinion; if we also count the milder "emphasis of matter" reminders, **355 (3.84%)** do. The paper calls these the **narrow** and **wide** definitions respectively.

**Type two: regulatory sanctions and enquiries.**
The stock exchanges and the securities regulator take action against disclosure irregularities, accounting fraud, misappropriation of funds and similar problems, and the CSMAR database collects these into an event table. We use, as our label, **violations that only occurred after the annual report was published** — an important detail, because only something that happens *afterwards* can test whether it was *predictable in advance*. Such labels cover **21.27%** of the sample (1,965 firm-years with any type of violation).

**Why can these two things serve as "the right answer"?** Because we did not invent them and they are not affected by our model. The model says "suspicious", and then the auditor or the regulator independently named the same firm — that is what "screens well" means. In statistical language, these two labels are **external evaluation benchmarks, independent of the features**.

### 1.3 The traditional toolkit: ratios, and one famous fraud model

Accounting has two standard ways of judging whether a firm's books might be problematic.

**(a) Ratio analysis.** Divide net profit by total assets to get the return on assets; divide liabilities by total assets to get the leverage ratio; then compare with firms of a similar size in the same industry. This is the simplest and most widely used approach, but it has two weaknesses: it looks at **one indicator at a time**, and when indicators disagree a human eye struggles to weigh them; and there is **no unified standard for "abnormal"** — how high is high, how low is low, depends heavily on experience.

**(b) The Beneish M-Score.** In 1999 the American scholar Messod Beneish published a model designed specifically to detect **earnings manipulation** (roughly: "using accounting tricks to make profit look better than it is"). It combines eight financial ratios into a single score; the higher the score, the more suspicious the firm. The model is very well known and is still cited today by auditors, short sellers and financial journalists. §5 takes it apart in detail.

**The M-Score is good, but it has limitations we cannot route around** (these are not its fault: it was designed for a different job):

- It was estimated on a **US** sample in the 1990s, so its choice of variables and the size of its coefficients carry the imprint of that decade and that market;
- It is a **supervised** model: it needs the right answer ("which firms actually manipulated earnings") in order to estimate coefficients, and in the Chinese market that right answer is hard to obtain cleanly;
- More importantly, it detects one particular kind of manipulation — **making profit look higher** — not "is the business as a whole in trouble". As we will see, that difference produces a strikingly dramatic result (§10.4).

### 1.4 A new idea: count the words as well

Financial numbers record only the **outcome**; the prose in the annual report records **how the company explains that outcome**. Two decades of academic work have found that words carry information the numbers do not:

- **Tone**: does management say "growth, breakthrough, leading" more often, or "decline, pressure, challenge"?
- **Readability**: are the sentences long and convoluted, or short and clear? Some studies find that **the more a company wants to bury bad news, the harder it makes the annual report to read** (because complex long sentences dilute the reader's attention).
- **Hedging language**: the more often "may, possibly, expected, subject to uncertainty" appears, the less confident management itself is.

In the academic literature, English-language work commonly uses the Loughran–McDonald financial sentiment dictionary. On the Chinese side, Yao Jiaquan et al. (2021) constructed a Chinese financial sentiment dictionary, and Zeng Qingsheng et al. (2018) studied the relationship between annual-report tone and insider trading. Our approach moves those dictionaries onto the Chinese MD&A: we segment the prose into words with a tokeniser and then count how many positive words, negative words and uncertainty words appear.

**And so our core idea emerges**:

> Put six financial features and three text features side by side, hand them to an **anomaly-detection algorithm that needs no right answers**, and let it find the firms that "do not look like the majority". Then check whether those "different" firms happen to be exactly the ones the auditors and regulators later named.

Note one crucial design decision here: **we do not train the model on "was it penalised or not"**. There are three reasons:

1. **Labels are too sparse**: of 9,239 observations only 204 carry a modified opinion — 2.2%. Training on labels that sparse makes it easy for a model to "memorise the answers" rather than "learn the pattern".
2. **The labels themselves are biased**: an audit opinion is a judgement an auditor reaches after weighing the client relationship and legal risk; it reflects "the auditor's decision", not purely "the firm's problem". Training on it would mean asking the model to imitate an auditor's preferences.
3. **It would contaminate the test**: if the label were used in training and then used again for evaluation, we would be marking our own homework.

This family of methods — "do not use right answers, just learn what the data themselves look like" — is called **unsupervised anomaly detection**. §6 describes the particular algorithm we use.

---

## 2. The three research questions (RQs)

The paper splits the work into three questions, and we follow the same order.

| ID | Question (academic wording) | Question (plain language) |
| --- | --- | --- |
| **RQ1** | Does adding MD&A text features to financial features provide **incremental** value in unsupervised anomaly screening, measured against the Beneish M-Score as benchmark? | Looking at the numbers alone already picks out "odd" firms. Does adding "read the annual-report prose" make the picking more accurate? |
| **RQ2** | Within the fused model, how much do the financial block and the text block each contribute? | If the model really does use the words, how does it use them, and how large is the text's influence? |
| **RQ3** | Does the conclusion hold when we change the benchmark, change the model, change the year, and switch to real regulatory outcomes? | Is our conclusion just an artefact of tuning? Does it survive being pushed around? |

The three questions correspond to three subsections of chapter 5 of the paper: 5.2 (RQ1), 5.3 (RQ2) and 5.4 (RQ3), with the external validation reported separately in 5.6.

---

## 3. The data: what we actually have in hand

### 3.1 Three sources

| Source | What it is | What we use it for |
| --- | --- | --- |
| **CSMAR financial statement database** | A commercial database of Chinese listed-company financial data, the one most used in academic work. We take the consolidated statements (not the parent-company statements) — balance sheet, income statement and cash-flow statement — for fiscal years 2020–2023 | Computing the six financial features and the Beneish M-Score |
| **CSMAR event database** (`FIN_Audit`, `STK_Violation_Main`) | Audit opinion types; violations and penalties | Serving as "the right answer" (evaluation labels); **never used in training** |
| **CNINFO annual-report PDFs** | The official disclosure platform for listed-company annual reports. We downloaded about **10,000** PDFs, **41 GB** in total | Extracting the MD&A text, then computing the three text features |

Why do we need 2020 data? Because most of our features are comparisons with "the previous year" (growth rates, changes in ratios), so a 2021 observation needs 2020 as its base period. That is why the sample frame is described as "2021–2023 observations, with 2020 as the base year".

### 3.2 How the sample shrank, step by step (this part matters)

**Step one: decide who is in scope.**
We took every company in CSMAR whose industry classification code begins with C — in the Chinese industry classification, C stands for **manufacturing**. Why manufacturing only? Because statement structures differ so much across industries (a bank has no "inventory"; an internet company has no "factory buildings") that mixing them would distort every comparison. Manufacturing has the largest number of firms, the most consistent statement structure, and it is the closest to the everyday intuition of "a business that makes things".

Result: **3,694 companies and 10,172 firm-year observations** (3,165 in 2021, 3,404 in 2022 and 3,603 in 2023). Of these, 202 companies (408 observations, 4.4%) are Beijing Stock Exchange listings.

**Step two: remove, one at a time, the observations for which features cannot be computed.**
This is Table B5 of the paper's appendix, and it is the question reviewers ask most often — "why did your sample shrink?" — so every step has to be accounted for:

| Step | Observations remaining | Lost at this step | Why they were lost |
| --- | --- | --- | --- |
| Starting sample frame | 10,172 | — | All A-share manufacturing firms, 2021–2023 |
| Remove those with no computable M-Score | 9,414 | −758 | The M-Score needs eight year-on-year ratios; where the previous year's data are missing or not comparable, it cannot be computed |
| Remove those missing one financial ratio | 9,413 | −1 | A single observation short of one required field |
| Remove those with no usable MD&A text | **9,239** | −174 | No MD&A section found in the PDF (scanned documents, malformed files, non-disclosure that year, and so on) |
| **Final analysis sample** | **9,239** | −933 in total | Retention rate **90.8%**, covering **3,488 companies** |

The final sample by year: 2,732 in 2021, 3,124 in 2022 and 3,383 in 2023.

**There is one design choice here that needs explaining.** We adopt a **complete-case** approach: the finance-only model, the text-only model and the fused model are all estimated on **the same 9,239 rows**. Why? Because only when it is "the same companies in the same years" are the three models' scores comparable, and only then can we talk about "whether adding text adds anything". If the finance model used 9,413 rows and the text model used 9,239, then the difference between them would have "different samples" mixed into it and the conclusion would no longer be clean. The price is that we lose 174 rows — but those 174 rows had no text available in the first place.

### 3.3 Cleaning: two moves that make numbers comparable

Raw financial data, used as they come, get dragged around by a handful of extreme values. We apply two steps (`src/features/standardise.py`):

**Move one: winsorising.**
For each feature, following its own distribution, we flatten the bottom 1% and the top 1% to the values at the 1st and 99th percentiles. **Why**: manufacturing occasionally throws up absurd values such as a receivables turnover of 1,764,970 (caused by a denominator close to zero), and a single such point can drag a whole model with it. Winsorising means "keep the observation but do not let it have more leverage than a normal-range one". Note that we do not delete extreme values; we **keep them but forbid them from over-influencing the result**.

**Move two: standardise within industry and year (z-scores).**
For each feature we subtract the mean of "the same sub-industry in the same year" and divide by the standard deviation, turning the number into "how many standard deviations above or below the peer average this firm is". **Why**: a leverage ratio of 60% is normal in an asset-heavy industry and dangerous in an asset-light one; "high growth" in 2021 and "high growth" in 2023 are not the same thing either. **Compared with peers is the only fair comparison.** Industry is grouped by the two-digit code of the securities-regulator classification crossed with year, giving 88 cells; where a cell contains too few firms (fewer than 20), the statistics are unreliable, so we fall back to the whole-sample mean and standard deviation (this happened in 19 cells, covering 2.5% of observations).

### 3.4 Turning PDFs into numbers: how the text features are computed

This is the most "engineering" part of the whole project, but the logic is simple: **download → locate → split into sentences → segment into words → count words → compute ratios.**

**(1) Locating the MD&A section.** In a 200-page PDF the MD&A is only one section. We wrote a set of rules (`src/features/textual.py`):

- first, look for headings such as "Management Discussion and Analysis", "Discussion and Analysis of Operations" or "Management Analysis and Discussion";
- require the heading to **occupy a line of its own**, and reject the table-of-contents format ("heading + a run of dots + page number");
- when several candidates are found mechanically, take **the longest passage** (some companies write "a note on the Management Discussion and Analysis section", which is a preamble, not the body);
- the section ends at the next "Section X" heading.

**(2) Splitting sentences and segmenting words.** We split sentences on the Chinese sentence-ending marks; we segment sentences into words with the open-source Chinese tokeniser **jieba**, loading a custom dictionary of **5,218 words** (because general-purpose tokenisers split terms such as "inventory write-down provision" or "operating cash flow" in the wrong place).

**(3) Counting words.** Three dictionaries:

- **3,585 positive words and 1,633 negative words** (the Chinese financial sentiment dictionary of Yao Jiaquan et al., 2021);
- **about 100 uncertainty words** ("may, possibly, expected, still uncertain" and so on, drawing on Loughran–McDonald and on Zeng Qingsheng et al., 2018);
- the matching rule is **exact token matching** (a segmented token counts only if it is identical to a dictionary entry), not "the string appears somewhere inside" — the latter would count the "growth" inside "no growth" as positive, which is exactly the error we want to avoid.

We also measured the hit density: on average there are **111.3 sentiment terms per 1,000 tokens**. That is a useful health check: the project's first version used a small hand-built dictionary of 38 positive plus 33 negative words, with a density of only 13.4 per 1,000 tokens — **8.3 times lower**. Replacing it with the formal dictionary showed that the first version's lexicon was so sparse it was barely measuring anything (§11.4 discusses what that did to the conclusions).

**(4) Data-quality checks.** We did not assume that "we downloaded 10,000 PDFs" means "we obtained 10,000 texts", so we checked:

- download check: **10,051 / 10,172 = 98.8%** of annual-report years matched their company; 121 were missing, the great majority being years **before** Beijing Stock Exchange companies listed (in those years they were still on the NEEQ market and CNINFO holds no matching report);
- text extraction: MD&A text was extracted successfully for **9,998** observations; **9,991** passed quality control; **7** were shorter than 300 tokens (kept but flagged); **174** had no usable text at all;
- extraction rate by year: 96.7% for 2021, 99.1% for 2022 and 99.0% for 2023 — 2021 is lower because PDF quality was historically patchier.

When extraction fails, the program **does not stop**: it records a `pdf_error` or `no_mda` status, skips that document and moves on. That is a basic requirement for any long-running pipeline (otherwise, if it crashes at document 7,000, all the earlier work is wasted).

---

## 4. We turned each company into nine numbers

This is the most important "translation" step in the whole report: **every model understands only numbers, so "a company" has to become one row of nine numbers.**

### 4.1 The nine features at a glance (formulas and intuition)

| # | Feature | How it is computed | In plain words | Why it might be connected with "something going wrong" |
| --- | --- | --- | --- | --- |
| 1 | `roa` — return on assets | net profit ÷ total assets | How many yuan of profit per 100 yuan of assets, per year | Earning power is the overall gauge of business health; persistently low or suddenly negative profitability is often the prelude to distress |
| 2 | `leverage` — liabilities-to-assets ratio | total liabilities ÷ total assets | Out of every 100 yuan of assets, how many are borrowed | The higher the leverage, the less room to absorb a shock; highly levered firms are more likely to receive a modified opinion |
| 3 | `revenue_growth` | (this year's revenue − last year's revenue) ÷ last year's revenue | Did the business get bigger or smaller | A sudden jump may be genuine expansion or may be "recognising revenue early"; a sudden contraction often travels with distress |
| 4 | `ocf_to_assets` — operating cash flow / total assets | net cash from operating activities ÷ total assets | How many yuan of real cash per 100 yuan of assets, per year | Profit can be "manufactured"; cash is much harder to manufacture. Good profit with poor cash flow is a classic alarm |
| 5 | `receivables_turnover` | revenue ÷ receivables | How many times a year the money owed to you is actually collected | A sudden fall means cash is not coming back, or that revenue was "sold on credit" |
| 6 | `accruals_to_assets` — accruals / total assets | (net profit − operating cash flow) ÷ total assets | Of the profit on the books, how much is "money not yet received" | **This is the most important and most classic manipulation signal among all six financial features** (accounting calls it the "accruals anomaly") |
| 7 | `readability` | 1 ÷ average sentence length (length measured in characters) | The shorter the sentences, the higher the score, the easier to read | Firms with something to hide tend to make the report harder to follow; though others argue that convoluted writing is simply a competence problem |
| 8 | `sentiment_balance` | (positive words − negative words) ÷ total tokens | How much more good news than bad news (as a proportion) | Excessively optimistic tone may be "reporting the good and burying the bad", or may be genuine confidence |
| 9 | `uncertainty_ratio` | uncertainty words ÷ total tokens | How many "may / expected / uncertain" words per 100 words | When management itself is unsure, its language becomes vague |

The first six are financial (computed in `src/features/*.py`), the last three textual (computed in `src/features/textual.py`). These nine numbers are each company's "full-body photograph" as far as the models are concerned.

### 4.2 What the raw features look like

Supplementary Table B1 of the paper gives the raw distribution of the nine features *before* winsorising and standardisation. Note that **the number of usable rows is not 10,172 for every feature** (some features need the previous year's data, some come from the PDF text), so the table keeps an `n` column:

| Feature | n | Mean | Standard deviation | Minimum | Maximum |
| --- | --- | --- | --- | --- | --- |
| `roa` | 10,172 | 0.0362 | 0.1120 | −2.491 | 6.365 |
| `leverage` | 10,172 | 0.3843 | 0.2131 | 0.0150 | 5.906 |
| `revenue_growth` | 9,442 | 0.3883 | 12.086 | −1.445 | 944.10 |
| `ocf_to_assets` | 10,172 | 0.0491 | 0.0793 | −1.788 | 0.8385 |
| `receivables_turnover` | 10,145 | 262.20 | 17,699 | −0.4716 | 1,764,970 |
| `accruals_to_assets` | 10,172 | −0.0128 | 0.1099 | −1.847 | 6.822 |
| `readability` | 9,998 | 0.0093 | 0.0019 | 0.0010 | 0.0336 |
| `sentiment_balance` | 9,998 | 0.0888 | 0.0180 | 0 | 0.1727 |
| `uncertainty_ratio` | 9,998 | 0.0058 | 0.0029 | 0 | 0.0597 |

A few details show why cleaning is unavoidable:

- a maximum `leverage` of 5.906 means "liabilities are 5.9 times total assets" — insolvent to the point where net assets are negative. Such firms really do exist in the sample, but their leverage on the model would be grotesquely large;
- a maximum `receivables_turnover` of 1,764,970 is the textbook "denominator close to zero" accident;
- a maximum `revenue_growth` of 944 times is usually a reverse-merger or restructuring event;
- the formula for `sentiment_balance` is "(positive words − negative words) ÷ total tokens" and involves **no truncation at all**, yet its minimum is **exactly 0** rather than a negative number. That means that across this sample of 10,000 annual reports, **not one company used more negative words than positive words** — the overall tone of Chinese manufacturing annual reports is overwhelmingly positive (an interesting phenomenon in its own right).

### 4.3 Why "nine indicators" is not a case of the more the merrier

You may wonder: an annual report contains hundreds of accounting captions and tens of thousands of words — why take only nine?

Three reasons:

1. **Sample size**: with 9,239 rows, stuffing in 100 features would leave each feature only about 90 observations to estimate its "normal range" from, and the model would become extremely unstable (the curse of dimensionality).
2. **Explainability**: we need to be able to tell a regulator or an investor "this firm was picked out because these three numbers look wrong". With nine features a human brain can repeat the story; with 100 it cannot.
3. **Avoiding duplication of information**: financial ratios are highly correlated with one another (`roa` and `accruals_to_assets` both contain net profit), so stacking 100 indicators does not deliver 100 units of information, only 100 units of noise. These nine were **hand-picked** along four dimensions — financial health, earnings quality, structural change and language style — and each corresponds to a strand of literature.

---

## 5. Ruler one: the Beneish M-Score in detail

§5–§9 form this report's **handbook of methods and models**. If you only want the conclusions, you can jump to §10.

### 5.1 What it is for

Beneish (1999) set out to answer one specific question: **which companies may have manipulated their earnings (made profit look better than it really was)?** His method was to collect companies with a suspicious profile — defined at the time using, among other things, US Securities and Exchange Commission enforcement records — compare their financial ratios with those of normal companies, and use a statistical model (a probit model) to estimate weights for eight ratios, which are then combined into one score.

### 5.2 The formula, and the eight variables one by one

$$
M = -4.84 + 0.920\cdot DSRI + 0.528\cdot GMI + 0.404\cdot AQI + 0.892\cdot SGI + 0.115\cdot DEPI - 0.172\cdot SGAI + 4.679\cdot TATA - 0.327\cdot LVGI
$$

| Variable | Full name | How it is computed | Coefficient | What the coefficient is saying |
| --- | --- | --- | --- | --- |
| DSRI | Days sales in receivables index | (this year's receivables / this year's revenue) ÷ (last year's receivables / last year's revenue) | +0.920 | Receivables taking a larger share of revenue → possibly "revenue sold on credit" (recognised early); more suspicious |
| GMI | Gross margin index | last year's gross margin ÷ this year's gross margin (gross margin = (revenue − cost of goods sold) ÷ revenue) | +0.528 | Gross margin sliding → operations deteriorating; more suspicious |
| AQI | Asset quality index | this year's "share of assets that are neither current nor fixed" ÷ the same item last year | +0.404 | More of the asset base becoming hard to pin down; more suspicious |
| SGI | Sales growth index | this year's revenue ÷ last year's revenue | +0.892 | **The faster the growth, the more suspicious** — because fast-growing firms have both the motive and the opportunity to "engineer the books" to keep growth going |
| DEPI | Depreciation index | last year's "depreciation / (depreciation + fixed assets)" ÷ the same this year | +0.115 | A falling depreciation rate (slower write-off) → profit pushed up; more suspicious |
| SGAI | Sales, general and administrative expenses index | this year's "(selling + administrative) expenses / revenue" ÷ the same last year | −0.172 | A rising expense ratio → less efficient, but the coefficient is negative, meaning the author treats it as slightly *reducing* suspicion |
| TATA | Total accruals to total assets | (net profit − operating cash flow) ÷ total assets | **+4.679** | **The largest weight in the model**: the higher the accruals, the more suspicious (little of the profit is cash) |
| LVGI | Leverage index | this year's liabilities-to-assets ratio ÷ last year's | −0.327 | Leverage rising → the coefficient is negative; the author's explanation draws on a literature arguing that firms in distress are more likely to restructure, and restructuring raises the incentive to manipulate |

The constant of −4.84 places the baseline score at −4.84 "when nothing is happening".

### 5.3 Two "threshold conventions", and why we report both

The M-Score is used by asking "does it exceed some cut-off, in which case the firm is judged suspicious". Two cut-offs are common in the literature:

- **−1.78**: one of the settings in Beneish's original paper. We call this the **legacy** convention ("following the literature's threshold");
- a threshold of −2.22 is also used by some. The more defensible approach is to set the cut-off **from the distribution of the current sample itself**: take the top 10% of scores as "suspicious".

On our 9,239 observations:

- with the legacy threshold (M > −1.78), **1,686 observations = 18.2%** are flagged;
- with the sample's own top-10% quantile (M > −1.44), **924** are flagged.

**Why is a flag rate of 18.2% so much higher than the single-digit rates in Beneish's original sample?** Because a threshold is a product of its year and its sample's distribution. Lifting it directly onto Chinese manufacturing in 2021–2023 means an entirely different population structure (the shares of loss-making firms and of high-growth firms in our sample are simply not the same). This is precisely why we report both conventions: **the conclusion must not capsize over the choice of threshold**. The main results table in §10 gives enrichment under both, and you will see that changing the threshold changes only the *level* of the numbers, not the *ordering* of firms — which is exactly what robustness means.

### 5.4 One modification we made, and the limitation we must state

**DEPI cannot be computed.** Computing DEPI requires a "depreciation expense" field, but the cash-flow statement we obtain from CSMAR is a **direct-method** statement, which has no separate "depreciation" line (depreciation and amortisation are folded into "other"). Our treatment is to **set DEPI to 1.0 (the neutral value)**, so that its contribution is a constant 0.115 and it takes no part in distinguishing one company from another.

**This must be stated plainly**: it means that what we compute is not a "word-for-word reproduction of the original M-Score" but a **modified variant** (we call it the legacy / modified convention). We say so in the paper, in the appendix and in the v0.3 revision, and we explain that it does not affect the main conclusion (the DEPI weight is only 0.115, and it is a constant for every company, so it cannot change the ranking).

**Another limitation that must be stated**: we do **not** winsorise the M-Score (the truncation in §3.3 applies only to the nine features). The reason is that this score is an evaluation **ruler**, not a model **input**, and we want to leave it as it is. The price is an extremely long tail: across the whole sample the range is **−387.1 to 9,182.9**, with **33 rows** where |M| > 20 (0.4%). These extremes make any "average by value" statistic meaningless, which is why we use only **rank correlation** (§9.1) for the M-Score and never linear correlation.

### 5.5 Why it must be "only a ruler, never a training signal"

This was mentioned in §1.4, but it is worth repeating, because many readers will be puzzled: "if you have such a good M-Score, why not let the model learn it?"

The answer is that **what we are testing is precisely whether the model can independently arrive at a judgement similar to the M-Score's**. If the M-Score went into the training objective, the model would be copying the answers, and we would then be evaluating it against the M-Score — a circular argument. So the design is:

- the M-Score appears **only on the evaluation side** (computing the Spearman correlation, computing the enrichment rate);
- the training side (Isolation Forest, autoencoder) **knows nothing about the existence of the M-Score**.

---

## 6. The main model: Isolation Forest in detail

### 6.1 One-sentence intuition

Imagine a pile of company cards spread on a table, each card carrying nine numbers. You need to find, quickly, the cards that look least like the rest. What do you do?

**Take a knife, pick a feature at random, pick a cut point at random, and split the cards into two piles; repeat until every card is isolated on its own.** What happens? Cards "growing in the corners" are usually isolated after two or three cuts, while "normal cards squeezed into the middle of the crowd" need many cuts before they separate.

**Measure "how odd" by the number of cuts (the path length)**: fewer cuts, odder firm. That is the entire core idea of the **Isolation Forest (IF)**, proposed by Liu, Ting and Zhou in 2008 and one of the most widely used anomaly-detection algorithms today.

Why is the method clever? It **does not need to know what "normal" is** (no "normal distribution" has to be estimated), and it needs no right answers — ordinary random splits are enough. It is also tolerant of the premise that "anomalies are a minority": it is good at finding "points far from the crowd".

### 6.2 The mathematical form (understanding the structure is enough)

For one random tree, the **path length** of a sample $x$ inside that tree is written $h(x)$ (the number of edges traversed from the root until the leaf where it is isolated). The anomaly score is defined as:

$$
s(x, n) = 2^{-\dfrac{\mathbb{E}[h(x)]}{c(n)}}, \qquad c(n) = 2H(n-1) - \frac{2(n-1)}{n}
$$

- $\mathbb{E}[h(x)]$: the average path length across **many** random trees (a single tree is too noisy; the average is what is stable);
- $c(n)$: the expected path length "under randomness" when there are $n$ samples — a normalising constant ($H$ is the harmonic number);
- so $s(x,n)$ means "how much shorter $\mathbb{E}[h(x)]$ is than the random baseline": **the shorter the path, the larger the exponential, the higher the anomaly score**, with values roughly in (0, 1].

### 6.3 Our exact settings (reproducible)

| Setting | Value | Why this value |
| --- | --- | --- |
| Number of trees | **500** | Stabilises $\mathbb{E}[h(x)]$; beyond that the gain is limited, and 500 is a common default |
| Sample size per tree, `max_samples` | **min(256, n)**; with 9,239 rows in this sample → **256** | The IF authors suggest around 256; a small subsample also spreads the splits out and makes overfitting less likely |
| Random seed | **42** | Reproducibility (anyone gets the same answer) |
| Implementation | `sklearn.ensemble.IsolationForest` with `n_jobs=-1` for parallelism | Engineering efficiency |
| **Score direction** | We **negate** `score_samples()` so that "bigger = more anomalous" | sklearn's `score_samples` is a "normality" score: higher means more normal. Negating it matches intuition and makes downstream top-k selection easy |
| **Primary review threshold** | the top **10%** of scores (top-10%, i.e. 924 observations) | see §6.4 |
| Sensitivity thresholds | top-5% (462 observations) and top-15% (1,386 observations) | see §9.2 |

**One easy misunderstanding**: the score the model outputs is **not a probability**, and it is not something between 0 and 1 where "closer to 1 means more likely to have broken the law". It is only a relative oddity converted from a path length. That is why we never say "this firm has a 70% probability of a violation"; we say only "it ranks 92nd out of 9,239".

### 6.4 Why use "top 10%" as the threshold

Because **the users of a screener — regulators, auditors, investors — have limited capacity**. You cannot ask a person to read 9,239 annual reports page by page, but you can ask them to read 924. So "top 10%" is a threshold with an **operational meaning**: what we promise is "we put the most suspicious 10% at the front", not "we determine who is guilty".

Using a quantile rather than a fixed score has two further benefits:

- **comparability across models**: Isolation Forest scores, autoencoder reconstruction errors and M-Score values have completely different units, but all of them can be compared at "each one's own top 10%";
- **comparability across years**: when scores drift as a whole from one year to the next, taking a quantile corrects for it automatically.

### 6.5 The limitations of Isolation Forest (you need to know them)

1. **It finds "different from the majority", not "bad".** An unusually excellent or unusually innovative company can also rise to the front for being "too different". This is why external labels (audit opinions, violation records) must be used to validate it, and why the score alone cannot be trusted.
2. **It assumes "anomalies are a minority and are separable".** If problem firms made up more than 30% of the sample and were mixed into the crowd, it would stop working.
3. **It is sensitive to the scale of features**, which is why we standardise in §3.3.
4. **It is random.** With a different seed, individual companies change places. This is why we fix seed 42 and also report "overlap rates" (§9.5) to measure whether different models pick out the same firms.

---

## 7. Model two: the autoencoder in detail

### 7.1 Why a second model at all

A conclusion that holds under only one algorithm is quite possibly a quirk of that algorithm. So we cross-check with a model built on a **completely different principle**: the Isolation Forest relies on "random slicing", the autoencoder on "compress and reconstruct".

### 7.2 Intuition: make the model memorise what a normal set of accounts looks like

Imagine asking a student to look only at the nine numbers of 9,239 normal companies and learn to "repeat them back". The learning method is: **compress** the nine numbers into fewer numbers (eight, say), then **restore** them to nine. Because the channel in the middle is narrow, the student has to learn to "grab the essentials" — to remember only the most stable structure shared across companies.

Once trained, a new company arrives and is also compressed and restored. **If the company is "normal", the restoration is accurate (small error); if it is "odd", compressing it loses something essential and the restoration is badly wrong (large error)**. The **reconstruction error** is the anomaly score.

This is the **autoencoder**: a neural network whose "input equals output", with a narrow **bottleneck layer** in the middle.

### 7.3 Architecture and the hyperparameters we used

This project implements the autoencoder with `sklearn.neural_network.MLPRegressor` (so that no deep-learning framework has to be introduced, which helps reproducibility). The architecture is:

```
input 9 dims  →  hidden 16  →  bottleneck 8  →  hidden 16  →  output 9 dims
                   (ReLU)         (ReLU)          (ReLU)
```

The training objective is to make the output as close as possible to the input (**the input and the target are the same X**).

| Hyperparameter | Value | Note |
| --- | --- | --- |
| Hidden-layer structure | **(16, 8, 16)** | The middle 8 dimensions are the bottleneck; 9→16 expands, 16→8 compresses |
| Activation function | **ReLU** | Standard, trains stably |
| Optimiser | **Adam** | Adaptive learning rate, fast convergence |
| L2 regularisation `alpha` | **1e-4** | Stops the network from memorising the training data (overfitting) |
| Batch size | **256** | Matched to the sample size |
| Learning rate | **1e-3** | The usual Adam value |
| Maximum iterations | **500** | Used together with early stopping |
| Early stopping | `early_stopping=True`, `n_iter_no_change=20`, `validation_fraction=0.1` | Hold back 10% for validation; stop if 20 consecutive epochs bring no improvement, to avoid overfitting |
| Convergence tolerance | **1e-6** | |
| Loss function | **squared error** | The standard choice for a regression task |
| Random seed | **42** | Fixed |

**How the anomaly score is computed**: for each row we compute the **mean squared error** across the nine features, `mean((x - x̂)²)`; the larger the error, the more anomalous. The direction is naturally correct (no negation is needed, unlike the IF).

**What labels were used in training?** None. X is both input and target; this is called "self-reconstruction" and is standard unsupervised training. This keeps it consistent with the Isolation Forest: **neither model knows which companies are "bad"**.

### 7.4 The result in advance, and what it means

The autoencoder's score has a rank correlation with the M-Score of only **−0.007 (p = 0.528)** — statistically indistinguishable from zero. Its enrichment is between 1.5 and 2.0 times chance (on the top-10% convention: **1.57** legacy, **1.96** calibrated), far below the Isolation Forest's finance-only version (2.4–2.5 times).

**How should this "unexciting" result be read?** It is not a failure but an important piece of robustness information:

> Our main result ("financial features screen modified opinions well") is **not magic unique to the Isolation Forest** — because a completely different principle, the autoencoder, also screens some out (1.5–2.0 times chance), though clearly more weakly.

We report honestly that "the stronger main model is the Isolation Forest", and equally honestly that "the autoencoder is weaker on this dataset", and we explain why: a scale of nine features and 9,239 rows is not friendly to a neural network (many parameters, few samples), whereas the Isolation Forest is precisely the kind of method that is more stable in a high-dimensional, small-sample setting. This is **evidence about method choice**, and it is the reason we place the autoencoder in the "robustness check" slot rather than the "main model" slot.

---

## 8. The explanation tool: SHAP in detail

### 8.1 The problem: the model says "this firm is odd" — on what grounds?

The Isolation Forest gives us a score but does not tell us why. A regulator cannot accept "the algorithm says it is odd" as a conclusion; it must be possible to answer: **which numbers make it look odd?** This is the problem of **explainability**.

### 8.2 The intuition of SHAP: share the credit fairly among the features

Imagine nine people (the nine features) jointly producing one outcome (the model's output). SHAP's approach comes from the **Shapley value** in game theory: **consider in turn "how much worse would the outcome be if this person were absent?", try every possible order in which people can join, and average**.

An example (simplified): a company's fused anomaly score is 0.704. The model first has a "base score" for an average company; then:

- replace this company's `receivables_turnover` with the average value → the score drops a lot → so this feature was pushing it up;
- replace `sentiment_balance` with the average value → the score barely changes → this feature contributes little;
- and so on.

The SHAP value is the precise allocation of that "push up / push down" amount, and it has a beautiful property: **all the features' SHAP values add up exactly to "this company's score minus the average company's score"** (additivity).

### 8.3 Our three uses

| Level | What is computed | What question it answers |
| --- | --- | --- |
| **Global** | the mean of \|SHAP\| over all samples, ranked by feature | which features does the model care about most overall? |
| **Group** | the sum of \|SHAP\| within a group ÷ the sum of all \|SHAP\| | finance block versus text block: which contributes more? |
| **Local** | for one company, the top features by descending \|SHAP\| | why was **this** company picked out? |

Technically we use `shap.TreeExplainer` to explain the Isolation Forest directly (tree models have an exact algorithm, so no "surrogate model" approximation is needed); when the sample exceeds 2,000 rows, a fixed-seed subsample controls the computational cost.

### 8.4 **A trap you must be warned about: the units of SHAP values**

This is a note added specifically in the v0.3 revision of the paper, and it is a trap that many readers fall into:

**The unit of a SHAP value is "the unit of the model's own output", not the 0–1 anomaly score.** Specifically, it explains the Isolation Forest's `score_samples` output (the quantity *before* we negated it). Therefore:

- the **direction** of a SHAP value can be read (positive = pushes the anomaly up, negative = pushes it down);
- the **absolute value** of a SHAP value must not be added to a 0–1 score such as 0.704;
- we checked this: recomputing and summing the SHAP values gives a correlation of **0.9972** with the model's raw output (so the allocation is correct), but "base value + sum of SHAP" deviates from the 0–1 anomaly score by as much as **15.69** (so the units are simply different).

**The correct way to read it**: do not say "text contributed 0.338 points"; say "text features account for 33.8% of the total feature influence".

### 8.5 A "per-feature" correction to the group shares (an easy misreading)

In the fused model, the finance block accounts for **66.2%** and the text block for **33.8%**. At first sight "finance is twice text". But consider: **finance has six features and text has only three**. If we compute the average contribution per feature:

- finance: 66.2% ÷ 6 = **11.0% per feature**
- text: 33.8% ÷ 3 = **11.3% per feature**

**They are almost level.** In other words: the model does not "prefer" finance; it gives roughly equal attention to each column of data. The text block's share is lower simply because it has fewer columns. This detail is the best illustration of "why you cannot stop at 66.2%", and the paper emphasises it specifically.

---

## 9. How we measure "accurate": the evaluation metrics in detail

The model produces scores; evaluation answers "is this score any use?". We use five groups of metrics, each answering a different question.

### 9.1 Spearman's rank correlation ρ: how similar are two rankings?

**What it is**: turn each of two rankings (our anomaly score and the Beneish M-Score) into "places", then compute the correlation between the places. Values run from −1 to +1, with 0 meaning "the two rankings have nothing to do with each other".

**Why not ordinary (Pearson) correlation**: the M-Score has an extremely long tail (−387 to 9,183), and a Pearson correlation would be completely hijacked by a few extreme values; a rank correlation looks only at "who is ahead of whom" and is immune to extremes.

**Results and how to read them**: finance block ρ = **−0.021** (p = 0.040), text block **−0.026** (p = 0.013), fused **−0.018** (p = 0.091), autoencoder **−0.007** (p = 0.528).

**What does the minus sign mean?** It does not mean "we computed it wrongly"; it means **the direction is opposite**:

> Firms that our statement-shape screener ranks highly are, on average, **slightly lower** on the "earnings manipulation" yardstick (not higher).

That sounds like "the model learned it backwards", but read it together with §10.4: **a high M-Score does not mean the firm will receive a modified opinion.** In fact the two groups of firms are almost disjoint — which is why, in the external validation below, our score's ability to separate modified opinions reaches 0.802 while the M-Score manages only 0.242 (worse than a coin toss). **"Disagreeing with the M-Score" is not a defect here; it is the key finding.**

### 9.2 Enrichment / lift: how much do you catch if you look at the top 10%?

**What it is**: suppose you can only afford to look at the 10% of firms with the highest scores. Within that 10%, what is the proportion of modified opinions? Divide that by the proportion across the whole sample and you get "**how many times better than random sampling**".

$$
\text{enrichment}_{k} = \frac{\text{modified-opinion rate in the top } k}{\text{modified-opinion rate in the whole sample}}
$$

- enrichment = 1: the same as picking at random (useless);
- enrichment = 2: twice as good;
- enrichment = 4.95 (our finance version at the top 10%): **look at 10% of firms and you catch 49.5% of all the modified opinions in the sample**.

**Why report three thresholds, 5% / 10% / 15%**: because "the top 10%" is a human choice, and if a conclusion held only at one particular threshold it would be "tuned". Reporting all three shows whether the trend is consistent — for our finance version, against modified opinions, the three values are **6.37 / 4.95 / 3.76**: the looser the threshold (the more you look at), the lower the multiple naturally is, but all three are far above 1, showing that the conclusion does not depend on one threshold.

### 9.3 AUC: the standard measure of discrimination

**What it is**: pick one firm that "has a problem" and one that "does not", at random; AUC is the probability that the model gives the problematic one a higher score. 0.5 = a coin toss, 1.0 = perfect, below 0.5 = systematically inverted.

**Why use it**: it is the common language of "ranking quality" and it does not depend on which threshold is chosen (unlike enrichment, which depends on top-k). Every AUC in the paper is accompanied by a **bootstrap 95% confidence interval** (resample the data with replacement many times and see how far the AUC moves).

**Our numbers**:

- finance Isolation Forest, against modified opinions: **0.802**, interval **[0.774, 0.833]** — very far from 0.5;
- text Isolation Forest: 0.520 (essentially a coin toss);
- fused: 0.769 (**lower** than the finance version);
- autoencoder: 0.690;
- Beneish M-Score: **0.242** — **much worse than a coin toss**, meaning it systematically ranks the firms that will receive modified opinions *lower* (the mechanism is in §10.4).

### 9.4 A technical limitation we have to admit: the intervals are too narrow

When bootstrapping, we resample "firm-years" independently. But observations of the same company in different years are clearly not independent (the same management, the same accounting habits). **The correct approach is to resample whole clusters of firms** (a cluster bootstrap). We did not do so, so the 95% intervals in the paper **may be too narrow** — that is, the true uncertainty is somewhat larger than reported.

We state this in the paper's limitations section. It is "honest disclosure", not a "fatal defect": because the effect sizes behind the main conclusions (0.802 versus 0.5) are very far from the boundary, doubling the width of the interval would not overturn them.

### 9.5 Ranking overlap: are two models picking the same firms?

**What it is**: |A ∩ B| ÷ |A| — that is, "of the firms A picked out, how many were also picked out by B". Note that this is **asymmetric** and is not the Jaccard coefficient (Jaccard is |A∩B| ÷ |A∪B|) — the paper flags the convention explicitly so that readers do not compute it the wrong way.

**Results**:

- finance versus fused: **0.797** — of the firms the fused model picks, eight in ten would have been picked by the finance model anyway, so **the fused model is anchored by the finance block**;
- finance versus text: **0.132** — the two families of signal pick **almost two entirely different sets of firms**.

That 0.132 is the key to understanding RQ1: text is not "signal-free"; rather, **its signal points in a different direction** (tone and accruals manipulation are almost unrelated). This also explains why simple equal-weight fusion slightly dilutes the financial signal.

### 9.6 The supervised control: what if we simply teach the model "who the bad firms are"?

This is part of RQ3 and an important complement to RQ1: our unsupervised model uses no labels — so **would using labels help a great deal?** We trained two supervised models (logistic regression and gradient boosting), with "modified opinion" and "t+1 disclosure violation" as labels.

**The key anti-leakage design**:

- **StratifiedGroupKFold, 5 folds, grouped by firm**: different years of the same company must fall in the same fold, otherwise the model would "memorise the company" rather than "learn the pattern";
- all preprocessing (winsorising, standardisation) is wrapped in a `Pipeline` and **fitted only on the training folds**, so that information from the validation fold cannot leak into training.

**Results**: modified-opinion AUC — finance logistic regression 0.865, gradient boosting 0.861; fused 0.866 / 0.873. Look at the increments: **+0.002 (interval [−0.013, +0.014])** and **+0.012 (interval [−0.005, +0.027])** — both straddle zero, meaning that **even in a supervised setting, adding text produces no statistically credible increment**.

**One interesting comparison**: the supervised models (0.865) are considerably better than the unsupervised one (0.802), which shows that "there is information in the labels"; but the incremental question (does text help?) gets the same answer under both settings: **no**. The conclusion does not depend on the modelling approach, which makes it far more credible than a single result.

---

## 10. Reading the results, table by table

### 10.1 RQ1: does text add anything? — No (Table 5.1 + supplementary Table B2)

Table 5.1 of the paper reports **only the rank correlations** (four numbers); the enrichment rates live in supplementary Table B2, and the top-10% bar chart is Figure 5.2. For convenience we merge the two tables into one here (both are on 9,239 observations):

| Model (9,239 rows) | Spearman ρ (Table 5.1) | p-value | legacy enrichment (5%/10%/15%, Table B2) | calibrated enrichment (5%/10%/15%, Table B2) |
| --- | --- | --- | --- | --- |
| Finance-only Isolation Forest | −0.021 | 0.040 | 1.506 / 1.690 / 1.712 | 2.229 / 2.446 / 2.337 |
| Text-only Isolation Forest | −0.026 | 0.013 | 0.866 / 0.836 / 0.905 | 1.104 / 0.909 / 0.974 |
| Fused Isolation Forest | −0.018 | 0.091 | 1.483 / 1.560 / 1.653 | 2.143 / 2.099 / 2.157 |
| Fused autoencoder | −0.007 | 0.528 | 1.696 / 1.572 / 1.487 | 2.229 / 1.959 / 1.782 |

**Three conclusions, read one at a time**:

1. **All three ρ values are small negative numbers and two of them are statistically "significant"** (p < 0.05). Do not be fooled by "significant": with 9,239 observations, a "significant" ρ of around −0.02 means "it is genuinely not zero, but it is too small to matter in practice". **Statistical significance is not practical importance** — this is one methodological lesson we would like readers to take away.
2. **The text model has essentially no discriminating power**: under the legacy convention the enrichment is 0.84–0.91 (**below 1, worse than random**); under the calibrated convention it is 0.91–1.10 (**hugging 1**). The finance model, by contrast, is at 2.1–2.4 under the calibrated convention. The gap is an order of magnitude.
3. **Fusion is slightly worse than finance alone, not slightly better**: calibrated top-10% enrichment 2.099 versus 2.446. In other words, adding text with equal weight **dilutes** the financial signal. This fits the "ranking overlap of 0.132" explanation — text brings a different set of firms, and equal-weight mixing pushes some of the firms finance had correctly ranked to the front back down a little.

**The answer to RQ1 is no.** Put more precisely: **for this particular target — the Beneish-style earnings-manipulation ordering — the MD&A text features provide no increment.**

### 10.2 RQ2: how much do the two blocks each contribute in the fused model (SHAP results)

- finance block **66.2%**, text block **33.8%** (SHAP group contributions);
- but averaged per feature: **11.0% versus 11.3%**, almost equal;
- the three globally most important features: `accruals_to_assets` (0.314), `revenue_growth` (0.312), `sentiment_balance` (0.304) — **note that the third is a text feature, and it ranks third**;
- the distribution of feature importance is very **flat**: highest 0.3138, lowest 0.2535, **with no single dominant feature**. This means the model does not decide on the basis of one number; it "looks at everything together".

**How to read that 33.8%?** In one sentence: **the model really is using the words, but using the words does not make it screen any better.** This is a textbook case of **explainability separating from effectiveness** — SHAP tells us what happens inside the model, not whether the approach is useful. Only external labels (§10.4) can answer the latter.

### 10.3 RQ3: change the benchmark, change the model, change the year (robustness)

| Check | What was done | Result | What it shows |
| --- | --- | --- | --- |
| Change the threshold | legacy (−1.78) versus calibrated (top 10%) | the "finance > fused" pattern is unchanged after the switch (calibrated top-10% is 0.35 higher) | the conclusion does not rest on a particular threshold |
| Change the model | Isolation Forest → autoencoder | autoencoder: ρ −0.007 (p 0.528), enrichment 1.5–2.0 times | the main result is not a quirk of one algorithm, but the autoencoder is clearly weaker |
| Year by year | computed separately for 2021 / 2022 / 2023 | finance ρ: −0.004 / −0.003 / −0.031; text weakly negative in all three years; the fused-versus-finance difference ≤ 0.01 | not carried by any single year |
| Change the label | M-Score → modified opinion → t+1 violation | see §10.4 | **the most persuasive check** |
| Lexicon control | recomputed on the same 9,239 rows with the first version's old dictionary | fused ρ −0.021 → −0.018; text −0.048 → −0.026; readability completely identical | the first version's "sign flip" came from the financial data repair, **not from changing the dictionary** (see §11.4) |

### 10.4 External validation: the brightest result of this study (Table 5.2)

This section is the **only place in the whole project that genuinely answers "is it useful"**, and it is what we most want readers to remember.

**Labels**: modified audit opinions (narrow 204 / wide 355), t+1 violations (any 1,965, disclosure-type 1,337).

**To prevent "time travel", we added a strict gate**: the announcement date of the violation must be **later** than the annual report's disclosure date, otherwise the observation is removed (because "knowing about the penalty first and then looking for clues in the report" is cheating). This gate removed **21.5%** of violation observations (1,965 → 1,543, that is 422 removed) and **22.2%** of disclosure-type ones (1,337 → 1,040, that is 297 removed) — a sizeable share, which shows that without this gate a batch of observations whose "fact" happened *after* the prediction would have been mistaken for labels.

**Main results**:

| Ranking | Modified-opinion AUC | Modified-opinion top-10% lift | t+1 disclosure-violation AUC | t+1 disclosure-violation lift |
| --- | --- | --- | --- | --- |
| **Finance-only Isolation Forest** | **0.802** [0.774, 0.833] | **4.95** (captures 49.5%) | **0.596** (0.600 after the strict gate) | **2.01** |
| Text-only Isolation Forest | 0.520 | 0.98 | 0.503 | 0.93 |
| Fused Isolation Forest | 0.769 | 4.56 | 0.582 | 1.89 |
| Fused autoencoder | 0.690 | 3.43 | 0.557 | 1.56 |
| Beneish M-Score | **0.242** [0.200, 0.281] | 0.64 | 0.407 | 0.85 |

**How to read this table**:

1. **Financial features plus Isolation Forest are very strong on modified opinions**: AUC 0.802, lift 4.95. In plain words: **looking only at 10% of firms, we cover nearly half of all the modified opinions in the sample.** For a completely unsupervised method with no label information at all, that is a good result.
2. **Text carries almost no information**: AUC 0.520 (a coin toss), lift 0.98.
3. **Fusion is slightly below finance alone** (0.769 versus 0.802) — confirming once again that "adding text with equal weight dilutes the signal". Under the strict-gate definition this becomes even clearer: finance 0.600, fused 0.590, and the text block still contributes nothing.
4. **The M-Score is inverted (0.242)** — this is the most counter-intuitive and most important finding. **Why?**

**Why is the M-Score "inverted"?** Look at the financial profiles of the two groups:

| | Firms receiving a modified opinion | Everyone else |
| --- | --- | --- |
| Accruals / total assets | **−0.11** | −0.01 |
| Sales growth index | **0.88** (shrinking) | 1.08 |
| Leverage index | **1.10** (taking on more leverage) | 1.02 |
| Return on assets | **−8.6%** | 4.0% |
| Liabilities-to-assets ratio | **60.3%** | 37.8% |

**The typical profile of a firm receiving a modified opinion is "shrinking, loss-making, with rising leverage".** Now look at the coefficient structure of the M-Score: **it rewards positive accruals (+4.679), rewards growth (+0.892) and punishes a rise in leverage (−0.327)**. So this profile is **systematically marked down** by it.

In one sentence: **the Beneish M-Score is built to catch manipulation that "makes profit look higher", not to catch "the business getting into trouble".** In the Chinese manufacturing sample these two groups of firms barely overlap (indeed they point in opposite directions). Our model has not gone backwards; rather, the M-Score has been used somewhere it should not be.

**What this finding means**:

- for practice: if you use the M-Score as a "risk-screening" tool on a Chinese manufacturing sample, you will **systematically miss** the very firms that most deserve attention;
- for academia: it shows that the popular practice of "using the M-Score as a proxy for risk" needs qualifying conditions;
- for ourselves: it explains why our scores are negatively correlated with the M-Score in §10.1 — **we are not wrong; the two targets are different**.

### 10.5 Details of the supervised control (Table 5.3)

Results of 5-fold cross-validation grouped by company (corresponding to Table 5.3 of the paper; the t+1 disclosure-violation figures use the calendar-year definition, and the strict-gate figures follow in the paragraph after the table):

| Label | Model | Finance AUC | Text AUC | Fused AUC | Fused increment ΔAUC [95% CI] |
| --- | --- | --- | --- | --- | --- |
| Modified opinion | Logistic regression | 0.865 | 0.680 | 0.866 | +0.002 [−0.013, +0.014] |
| Modified opinion | Gradient boosting | 0.861 | 0.613 | 0.873 | +0.012 [−0.005, +0.027] |
| t+1 disclosure violation | Logistic regression | 0.672 | 0.570 | 0.673 | +0.001 |
| t+1 disclosure violation | Gradient boosting | 0.671 | 0.526 | 0.679 | +0.008 |

**What happens with strict-gate labels?** The increment's sign flips straight to negative: logistic regression **−0.002 [−0.011, +0.005]**, gradient boosting **−0.001 [−0.011, +0.009]** — both intervals comfortably contain 0. In other words, under the "cleanest" version of the label, the text block does not even have that negligible positive increment. The paper's main text also summarises: **across the eight "label × model" combinations, the fused increment is positive in 6, and the 95% interval excludes 0 in 0.**

**The 16-cell paired test** (Table B4 of the paper): the 16 cells are the 8 calendar-year label cells plus the 8 strict-gate label cells. The fused increment is **positive in 8 out of 8** calendar-year cells and **positive in 6 out of 8** strict-gate cells, yet **not one cell's 95% interval judges it significantly different from 0**; while **the text block on its own is negative in all 16 of 16** (−0.068 to −0.248) — meaning that using the text features alone for supervised prediction is *worse* than not using them. That result sounds harsh, but it is what the data say, and we report it as it is.

### 10.6 A case: 600870 (2021)

We took the single highest-scoring observation and looked at it, because a reviewer will ask "what exactly did you screen out?":

- **600870, 2021, sub-industry C39**;
- fused anomaly score **0.704** (extremely high in the full sample);
- M-Score **14.3** (far beyond either threshold — the M-Score flags it too);
- the top three local SHAP factors pushing it up: `receivables_turnover`, `revenue_growth`, `leverage`;
- the company has a **disclosure-type violation on record in year t+1**.

**Why does this case matter?** Because before the v0.3 revision the paper had described it as "a counter-example where the benchmark and the model disagree"; on checking, **the M-Score in fact flags it as well (14.3)**, so it is a **strong positive case: both tools hit it, and a violation duly followed**. This is an example of an honest correction — and the reason the v0.3 revision specifically amended that sentence.

### 10.7 What the tables in appendices A and B are doing

- **Appendix A (branch experiments, Table A1)**: widen the sample to "all non-financial firms, 2021–2024" and see whether the conclusion changes. Result: finance AUC 0.767–0.802, M-Score 0.242–0.277, **the direction of the main conclusion is unchanged**. Appendix A's own wording is restrained: **it is a measurement check only, and it neither supports nor overturns RQ1** (because RQ1 is about the text increment, which appendix A does not address).
- **Appendix B1**: raw feature distributions (the table in §4.2 comes from here).
- **Appendix B2**: the full enrichment table under the two benchmarks (the legacy threshold versus the within-sample top 10%); the enrichment columns in §10.1 come from here.
- **Appendix B3**: the first version → second version comparison of dictionaries and conventions, and why the conclusion did not move (§11.4).
- **Appendix B4/B5/B6** (added in v0.3): B4 is the 16-cell paired increment, B5 is the sample attrition chain (§3.2), and B6 is the definitions and counts of the four label types.

---

## 11. Conclusions, boundaries and common misreadings

### 11.1 Three sentences we have the right to say

1. **On Chinese A-share manufacturing in 2021–2023, six financial features plus an Isolation Forest can effectively screen out the firms that will receive a modified audit opinion** (AUC 0.802, top-10% lift 4.95), and this ability is consistent in direction across different years, different thresholds and different algorithms.
2. **On this task, the tone, readability and hedging language of the MD&A bring no increment** (whether the yardstick is the Beneish ordering, the modified-opinion label or the t+1 violation label; and whether the setting is unsupervised or supervised).
3. **The Beneish M-Score cannot serve as a general-purpose screener for "financial disclosure risk"**: on this sample its ability to discriminate modified opinions is only 0.242, because what it detects is "making profit look higher", not "the business being in trouble".

### 11.2 Three sentences we have no right to say

1. **"This company committed accounting fraud"** — our model says only "it does not look like most companies". Establishing the conclusion requires a chain of evidence, not an anomaly score.
2. **"Text features are useless"** — we have shown only that "these three text features, on this data, for these targets, bring no increment". With a different text representation (large-model embeddings, sentence-level sentiment, question-answering extraction), a different target (for example the topic of a regulatory enquiry letter), or a different market, the conclusion could differ. The paper's wording is strictly confined to "in this setting".
3. **"An AUC of 0.802 means 80% accuracy"** — AUC is not accuracy; it is ranking quality. The actual "accuracy" depends on which threshold you choose, and we deliberately choose no "verdict threshold".

### 11.3 Known limitations (section 5.5 of the paper lists some; this is the fuller list)

| Limitation | What exactly it is | Impact |
| --- | --- | --- |
| Incomplete sample | 121 annual reports could not be downloaded (mostly Beijing Stock Exchange years before listing); 174 observations have no MD&A; retention rate 90.8% | Small firms and newly listed firms may be missing; applicability to them is unknown |
| Small Beijing Stock Exchange share | 202 firms / 408 rows = 4.4% | Conclusions about the Beijing Stock Exchange are not robust |
| Sparse and biased labels | Modified opinions 2.21%, violations 21.27%; the labels themselves are auditors'/regulators' decisions | Affects the interpretability of "accuracy", but not the conclusion about "ranking quality" |
| Narrow confidence intervals | Bootstrap resamples firm-years rather than whole firm clusters | Uncertainty is understated |
| Structural breaks | 2021–2023 spans the post-pandemic cycle and changes in the regulatory regime (including the full implementation of the registration-based IPO system in 2023) | Cross-year comparability is limited; the larger ρ in 2023 (−0.031) may be related to this |
| Text = three aggregate numbers | Tone, readability and uncertainty are compressed into three numbers | Heavy information loss; quite possibly one reason why "text adds nothing" |
| Dictionary fit | The Yao Jiaquan et al. (2021) dictionary was designed for general financial text, and MD&A usage differs | The reliability of sentiment measurement is limited |
| Data not publicly distributable | CSMAR and CNINFO data are licence-restricted | Third-party reproduction requires applying for the data independently |
| Single market | Chinese A-share manufacturing only | Cannot be extrapolated to other markets |

### 11.4 An important "internal audit" story: how a data repair changed the conclusion

This passage matters for understanding how honest the project is.

The project's first version (v0.1) once reached the **opposite** conclusion: text was taken to add value, and the fused score was **positively** correlated with the M-Score (ρ = +0.103); even the finance-only score was positively correlated (+0.136). We then found a **serious engineering bug**:

- the first version merged the balance sheet, income statement and cash-flow statement **by row position** (`combine_first`) rather than aligning them on the "company + year" key;
- the consequence: in **73.4% of years the balance sheet was one year stale** — in other words, "this year's income statement was matched with last year's balance sheet".

After the repair, the sample grew from 8,140 to 9,239 and the conclusion flipped: the fused ρ went from **+0.103** to **−0.018**, finance-only from **+0.136** to **−0.021**, and text from **−0.030** to **−0.026** (weakly negative all along, only similar in size).

**Someone will ask: was it not your change of dictionary that flipped the conclusion?** We ran a dedicated control experiment (`scripts/run_08_lexicon_control.py`): on the **same 9,239 rows after the repair**, recomputed with the **first version's old dictionary** —

- fused ρ: −0.021 → −0.018
- text ρ: −0.048 → −0.026
- readability: **completely identical**

Conclusion: **the sign flip came from the financial data repair, not from the dictionary.** The old dictionary only made the numbers wobble slightly (−0.048 → −0.026); the direction did not change.

The value of this story is that **it shows how the negative result was forced out of the data** — we did not set out to prove that text is useless; after fixing the bug, that is what the data said, and we reported it as it is.

### 11.5 FAQ: common misreadings

**Q1: Are AUC 0.802 and Spearman −0.021 not contradictory?**
No, because they are **two different targets**. Spearman asks "does your ranking resemble the M-Score's ranking"; AUC asks "can your ranking separate the firms that receive a modified opinion from those that do not". These two targets are themselves opposed (§10.4), so one being negative and the other high is exactly what mutual confirmation looks like.

**Q2: Is a model score of 0.704 a "70.4% probability of a violation"?**
No. The score is only a conversion of "relative oddity", and its range is not a strict 0–1 probability. We use only its **rank** (the top 10%), never its absolute value.

**Q3: Why do you say text is useless when the model clearly used it (33.8%)?**
"Used" and "useful" are two different things. SHAP shows that the model **internally** does discriminate using the words; but the external validation shows that this discrimination **does not line up** with the outcomes we care about. It is like a student who works hard on the bonus question while the bonus question does not count towards the grade.

**Q4: Did you deliberately choose a setting in which text cannot work?**
No. We made a large number of attempts in the opposite direction: the two-dictionary control experiment (§11.4), two settings (unsupervised and supervised), four different labels, two different models, a year-by-year analysis, and widening the sample to all non-financial firms (appendix A). Every attempt pointed the same way.

**Q5: Why not simply use a large language model (LLM) to read the annual reports?**
Three practical reasons: (1) more than 9,000 PDFs × 200,000 tokens each is not feasible in cost or time; (2) reproducibility is poor (models are updated and outputs are unstable); (3) the goal of this course project is "an explainable, reproducible statistical pipeline", not "the best possible performance". This is a scope choice, not a technical judgement.

**Q6: Why manufacturing only?**
Statement structures differ too much across industries (financial firms have no inventory; internet firms have no factory buildings), and mixing them would distort every comparison. Manufacturing has the largest sample and the most consistent structure, so it is the cleanest starting point. The price is that the conclusions cannot be extrapolated to other industries.

**Q7: Why are there two different test counts, 114 and 172?**
The paper reports the 114 tests at the time of hand-over (which did indeed all pass); a code refactoring afterwards increased the suite to 172 tests, which also all pass. Both numbers are correct; they refer to different points in time. The paper's main text keeps 114 to stay consistent with the hand-over date, while the README and CHANGELOG record the latest state.

**Q8: What is the biggest contribution of this project?**
In our view, three things: (1) a reproducible "text + financial" unsupervised screening pipeline (including the data-quality checks); (2) an honest negative result (text brings no increment for this class of target); (3) a counter-intuitive but important finding (on a Chinese manufacturing sample the Beneish M-Score's ability to discriminate modified opinions is 0.242 — the direction is reversed).

---

## 12. Engineering and reproduction

### 12.1 What the pipeline looks like (eight stages)

```
sample frame → parse the three statements → download audit of the PDFs → MD&A extraction → text QC
   → feature table (6 financial + 3 text) → descriptive statistics → modelling / evaluation / reporting
```

These correspond to the series of scripts from `scripts/run_00` to `run_16`, and the whole chain is strung together in `scripts/run_99_full_pipeline.py` (run everything with one command).

### 12.2 A few points of engineering care

- **Resumable**: the text extraction writes its progress to disk every 25 PDFs, so a crash can be resumed from the breakpoint;
- **Non-blocking**: a single unreadable PDF (`pdf_error`) or a missing MD&A (`no_mda`) only records a status and is skipped, so the batch does not die;
- **Controlled randomness**: every random seed is fixed at 42, and all hyperparameters are centralised in `src/config.py`;
- **Traceable results**: every table is written out to `outputs/tables/*.csv`, and every number in the paper can be traced to a CSV;
- **Delivery self-check**: `scripts/run_16_verify_manuscript.py` rebuilds the paper from the current artefacts and compares it paragraph by paragraph and table by table with the delivered docx, confirming that "the final manuscript equals the current pipeline output".

### 12.3 Tests

- the paper's main text reports, as of the hand-over date: **114/114 automated tests passing**;
- after the refactoring (CHANGELOG, 2026-11-24): **172/172 passing**;
- how to run them: from the project root, `.venv\Scripts\python.exe -m pytest -q`.

### 12.4 Code map (for those who want to dig in)

| Directory | Contents |
| --- | --- |
| `src/data_ingestion/` | CSMAR parsing, PDF download, MD&A extraction |
| `src/features/` | the six financial features, Beneish, the text features, standardisation / winsorising |
| `src/models/` | Isolation Forest, autoencoder, SHAP explanation |
| `src/evaluation/` | rank correlation, enrichment, AUC, bootstrap, cross-validation, temporal gate, lexicon control |
| `src/reporting/` | paper / PDF / table generation, revision reports |
| `scripts/` | numbered pipeline entry points (`run_00` … `run_16`) |
| `outputs/tables/` | all result tables (CSV) |
| `docs/` | feature dictionary, reproduction guide, project map, revision records |
| `data/` | raw and intermediate data (licence-restricted, not committed to the repository) |

### 12.5 If you want to reproduce it

1. Apply for a CSMAR account (the three statements plus the event tables) and access permission for CNINFO annual reports;
2. Python 3.12, then install `requirements.txt` (including pandas / numpy / scikit-learn / shap / pypdf / jieba / python-docx);
3. Follow the order given in `docs/reproducibility_guide.md` and `GUIDE.md`; the full pipeline takes several hours (most of the time goes on downloading and parsing the 10,000 PDFs);
4. If you only want the modelling part: `scripts/run_07_experiment.py` can run without repeating the data preparation.

---

## 13. Glossary

The Chinese companion of this report prints the same list as a Chinese–English two-column table. Because this file must contain no Chinese characters, the table below keeps the same 25 entries in the same order, with the English term and its one-sentence explanation, so that the two files can be read side by side.

| Term (English) | One-sentence explanation |
| --- | --- |
| annual report | The complete operating and financial report a listed company publishes every year |
| MD&A (Management Discussion and Analysis) | The section of the annual report in which management explains the year's performance in its own words |
| audit opinion | The independent accounting firm's third-party conclusion on the financial statements |
| modified / non-standard audit opinion | Any audit opinion other than an unqualified one — the auditor has reservations |
| earnings manipulation / fraud | Using accounting techniques to make profit look better than it is |
| accruals | The part of book profit that has not yet been received or paid in cash |
| anomaly detection | Finding the samples that differ from the majority |
| unsupervised | Training without using right answers (labels) |
| Isolation Forest | An algorithm that isolates samples by random slicing; shorter paths mean more anomalous |
| autoencoder | A neural network that compresses and reconstructs; large reconstruction error means anomalous |
| reconstruction error | The deviation when an autoencoder restores its input |
| explainability | Being able to say why the model judged as it did |
| SHAP value | A number that fairly allocates the model output across the features |
| path length | The number of edges a sample traverses in a random tree before being isolated |
| hyperparameter | A setting fixed by the researcher before training (such as the number of trees) |
| winsorising | Compressing extreme values to percentile cut-offs so that they matter less |
| standardisation / z-score | Subtract the mean, divide by the standard deviation, giving a score relative to peers |
| Spearman rank correlation | A measure of how similar two rankings are |
| AUC (area under the ROC curve) | Discriminating ability; 0.5 is a coin toss, 1 is perfect |
| enrichment / lift | The event rate in the top k% divided by the event rate in the whole sample |
| confidence interval | The range of uncertainty around an estimate |
| cross-validation | Splitting the data into folds and validating in turn, to prevent overfitting |
| data leakage | Accidentally using future or validation-set information while training |
| structural break | A sudden change in institutions or environment during the sample period |
| label | The "right answer" used for evaluation |

---

## 14. Where to read more

| If you want to know | Go to |
| --- | --- |
| The full paper | `outputs/manuscript/Group12A2_Final_EN_v0.3.docx` / `.pdf` (the only final version still maintained, 22 pages) |
| The precise definition of each feature | `docs/feature_dictionary.md` |
| How to reproduce the work | `docs/reproducibility_guide.md`, `GUIDE.md` |
| The project file map | `docs/project_layout.md` |
| What the v0.3 revision changed, and why | `docs/revision/v0.3_consistency_revision.md` |
| All result tables | `outputs/tables/*.csv` |
| The change history | `CHANGELOG.md` |
| The Chinese version of this guide | `docs/interpretation_report_cn.md` |

---

*This report was written after checking every statement against the paper and the code; every number can be traced to `outputs/tables/` or to the paper's appendices. If anything here disagrees with the paper, the final manuscript (v0.3) is authoritative.*

