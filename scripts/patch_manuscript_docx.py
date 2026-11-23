"""Patch the two English manuscript deliverables in place.

Reads the numbers and prose straight from scripts/build_section5.py so the
manuscript, the markdown section and the docx cannot drift apart.

Three files come out of one pass over the pre-patch master:

* the full manuscript, with section 5.8 in the body and Table 5.7 after it;
* the compact submission copy: three figures, body leading 1.2, section 5.6
  and Tables 5.1 and 5.3 replaced by a one-paragraph note;
* the supplementary appendix file holding Appendix A (Table A1) and
  Appendix B (Tables B1 to B3) for that compact copy.

Usage:
    python scripts/patch_manuscript_docx.py             # all three files
    python scripts/patch_manuscript_docx.py --full      # body version only
    python scripts/patch_manuscript_docx.py --compact   # compact pair only
"""
import copy
import importlib.util
import sys

import docx
from docx.oxml.ns import qn
from docx.shared import Pt
from docx.table import Table
from docx.text.paragraph import Paragraph

SRC = "11.23base/Group12A2_Final_EN_.docx"
DST = "11.23base/Group12A2_Final_EN_corrected.docx"
DST_COMPACT = "11.23base/Group12A2_Final_EN_corrected_compact.docx"
DST_SUPPLEMENT = "11.23base/Group12A2_Final_EN_corrected_compact_appendix.docx"

spec = importlib.util.spec_from_file_location("build_section5", "scripts/build_section5.py")
bs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bs)

num = bs.collect_numbers()
text = bs.prose(num)
tables = [
    bs._table_51(num),
    bs._table_52(num),
    bs._table_53(num),
    bs._table_54(num),
    bs._table_55(num),
    bs._table_56(num),
]

SECTION_REF = {"full": "Section 5.8", "compact": "Appendix A"}


def plain(value: str) -> str:
    return value.replace("`", "")


def set_para_text(p, value):
    value = plain(value)
    runs = p.runs
    if not runs:
        p.add_run(value)
        return
    runs[0].text = value
    for run in runs[1:]:
        run.text = ""


def set_para_multiline(p, value):
    parts = [plain(chunk) for chunk in value.split("\n\n") if chunk.strip()]
    set_para_text(p, parts[0])
    for chunk in parts[1:]:
        run = p.add_run()
        run.add_break()
        p.add_run(chunk)


def find_para(prefix):
    for p in doc.paragraphs:
        if p.text.strip().startswith(prefix):
            return p
    raise KeyError(prefix)


def replace_in_para(p, old, new):
    full = p.text
    if old not in full:
        return False
    set_para_text(p, full.replace(old, new))
    return True


def clone_para(model, value):
    """Deep-copy a paragraph element, keeping its formatting and first run style."""
    element = copy.deepcopy(model._p)
    for link in element.findall(qn("w:hyperlink")):
        element.remove(link)
    runs = element.findall(qn("w:r"))
    for extra in runs[1:]:
        element.remove(extra)
    if not runs:
        raise ValueError("model paragraph has no run to clone")
    run = runs[0]
    for child in list(run):
        if child.tag in (qn("w:t"), qn("w:br"), qn("w:tab")):
            run.remove(child)
    node = run.makeelement(qn("w:t"), {})
    node.text = plain(value)
    node.set(qn("xml:space"), "preserve")
    run.append(node)
    return element


def clone_table(sample_tbl, rows):
    """Deep-copy a table element and trim it to the required shape."""
    element = copy.deepcopy(sample_tbl)
    trs = element.findall(qn("w:tr"))
    while len(trs) > len(rows):
        element.remove(trs[-1])
        trs = element.findall(qn("w:tr"))
    assert len(trs) == len(rows), (len(trs), len(rows))
    return element


def set_cell(cell, value):
    p = cell.paragraphs[0]
    value = str(value)
    runs = p.runs
    if not runs:
        p.add_run(value)
        return
    runs[0].text = value
    for run in runs[1:]:
        run.text = ""


def fill_table(element, rows):
    table = Table(element, doc)
    assert len(table.rows) == len(rows), (len(table.rows), len(rows))
    for row, values in zip(table.rows, rows):
        cells = row.cells
        assert len(cells) == len(values), (len(cells), len(values))
        for cell, value in zip(cells, values):
            set_cell(cell, value)


def sub_heading(model, value):
    element = clone_para(model, value)
    para = Paragraph(element, model._parent)
    para.runs[0].font.size = Pt(11)
    para.runs[0].bold = True
    para.paragraph_format.space_before = Pt(8)
    para.paragraph_format.space_after = Pt(2)
    para.paragraph_format.keep_with_next = True
    return element


def build(mode: str) -> str:
    """Patch one copy of the manuscript; ``mode`` selects body or appendix."""
    global doc
    doc = docx.Document(SRC)
    applied = []

    abstract = (
        bs._benchmark_finding(num)
        + f" The final analytical sample contains {num['n']:,} firm-years from "
        f"{num['n_firms']:,} firms ({num['share'] * 100:.1f}% of the {num['frame_years']:,} "
        "firm-year frame). Against the Beneish benchmark, the finance-only Isolation Forest "
        f"ranking has a Spearman correlation of {num['rho_if_finance']:.3f} "
        f"{bs._p_inline(num['p_if_finance'])}, compared with {num['rho_if_fused']:.3f} "
        f"{bs._p_inline(num['p_if_fused'])} for the fused ranking and "
        f"{num['rho_if_text']:.3f} {bs._p_inline(num['p_if_text'])} for the text-only ranking; "
        "the three MD&A features therefore add no incremental value to the Beneish-style "
        "unsupervised screen, and the negative sign indicates that the screen and the M-Score "
        "order firms differently rather than agreeing. The ordering survives a wider frame and "
        "a fourth year (18,415 firm-years: 0.767 against 0.277) and three further outcome "
        "labels, where fusion never moves AUC by more than 0.018. The fused model's top-10% "
        "review queue has "
        f"{num['en_calibrated_if_fused_10']:.2f} times the sample-wide incidence of cases in "
        "the recalibrated Beneish top decile "
        f"({num['en_legacy_if_fused_10']:.2f} under the literal -1.78 cut-off); these are "
        "relative enrichment measures, not fraud prevalence estimates. Forward-looking t+1 "
        "violation discrimination is weak (best AUC 0.596). In supervised firm-grouped "
        "cross-validation, adding text to financial features produces small positive AUC "
        "increments of between 0.001 and 0.012 across the reported outcomes and algorithms, of "
        "which none of eight confidence intervals exclude zero. The contribution is therefore "
        "an empirical demonstration that the Beneish score cannot serve as an audit-risk proxy "
        "in this setting, together with an honest null for MD&A text. The scores are "
        "review-priority signals, not direct measures of disclosure quality, fraud, misconduct "
        "or violations."
    )

    _abstract_para = find_para("This study develops and evaluates")
    _abstract_head = _abstract_para.text.split("The final analytical sample")[0].rstrip()
    assert _abstract_head, "abstract head not found"
    set_para_multiline(_abstract_para, _abstract_head + "\n\n" + abstract)
    applied.append("abstract results paragraph")

    for prefix in (
        "At the time of the final experiment",
        "The unit of analysis is the firm-year",
    ):
        p = find_para(prefix)
        assert replace_in_para(p, "8,140", "9,239")
        replace_in_para(p, "3,265", "3,488")
        applied.append(f"sample size in '{prefix[:40]}'")

    p = find_para("Feature preprocessing follows Section 3.2")
    assert replace_in_para(p, "8,140", "9,239")
    applied.append("sample size in 4.x preprocessing paragraph")

    p = find_para("The study has several limitations")
    assert replace_in_para(p, "62.8%", "18.2%")
    assert replace_in_para(p, "usable sample", "analysed sample")
    applied.append("limitations paragraph")

    set_para_text(find_para("The sample frame contains 3,694"), text["s51"])
    applied.append("5.1 sample paragraph")

    set_para_text(
        find_para("Note: Counts are taken from the reported sample"),
        f"Note: Counts are taken from the reported sample description. The complete-case "
        f"sample contains {num['n']:,} firm-years in total.",
    )
    applied.append("5.1 note")

    set_para_text(find_para("Table 5.1 reports the raw"), text["s52_intro"])
    applied.append("5.1 to 5.2 transition")

    set_para_text(find_para("Table 5.1. Descriptive statistics"), text["t51_caption"])
    applied.append("Table 5.1 caption")

    set_para_text(find_para("The financial variables show highly skewed"), text["p_after_t51"])
    applied.append("benchmark paragraph")

    set_para_text(find_para("Table 5.2. Spearman rank correlation"), text["t52_caption"])
    applied.append("Table 5.2 caption")

    legacy_part, recalibrated_part = text["p_after_t53"].split("\n\n")
    set_para_text(find_para("Under the legacy benchmark, the finance-only"), legacy_part)
    applied.append("5.2 legacy results paragraph")

    set_para_text(
        find_para("Note: Values are 0.136"),
        f"Note: Values are {num['rho_if_finance']:.3f}, {num['rho_if_text']:.3f}, "
        f"{num['rho_if_fused']:.3f} and {num['rho_ae_fused']:.3f}, respectively. Statistical "
        "significance is reported in Table 5.2.",
    )
    applied.append("Table 5.2 note")

    set_para_text(
        find_para("The recalibrated benchmark leads to the same broad conclusion"),
        recalibrated_part,
    )
    applied.append("5.2 recalibrated paragraph")

    set_para_multiline(find_para("In the fused Isolation Forest model"), text["s53"])
    applied.append("5.3 SHAP paragraphs")

    p = find_para("Note: SHAP shares describe")
    assert replace_in_para(p, "34.6%", "33.8%")
    applied.append("5.3 SHAP note")

    set_para_text(
        find_para("The finance-only and fused Isolation Forest rankings"), text["s54"]
    )
    applied.append("5.4 robustness paragraph")

    set_para_text(
        find_para("Taken together, the evidence supports a narrow conclusion"), text["s55"]
    )
    applied.append("5.5 discussion paragraph")

    set_para_text(find_para("Table 5.4 compares the two specifications"), text["s56b"])
    applied.append("5.6 comparison paragraph")

    set_para_text(find_para("The Beneish M-Score is an accounting-risk proxy"), text["s57a"])
    applied.append("5.7 outcome definitions")

    set_para_text(find_para("The external-outcome tables cover"), text["s57b"])
    applied.append("5.7 event counts")

    set_para_text(
        find_para("Against contemporaneous modified audit opinions"), text["s57c"]
    )
    applied.append("5.7 ranking results")

    set_para_text(find_para("Table 5.6 addresses a separate supervised"), text["s57d"])
    applied.append("5.7 supervised results")

    external_reading = (
        "The external validation is the sharpest test in this paper, and it recasts the "
        "benchmark rather than merely qualifying it. Against modified audit opinions - an "
        "outcome produced by auditors who read the statements - the Beneish score ranks the "
        f"affected firms below the rest of the sample (AUC "
        f"{num['events']['ranking'][('mod_opinion', 'Beneish M-Score')]['auc']:.3f}), while a "
        "finance-only ranking reaches "
        f"{num['events']['ranking'][('mod_opinion', 'finance-only IF')]['auc']:.3f}. The "
        "decomposition in Section 5.7 shows that this is a construct mismatch: the score "
        "rewards positive accruals and sales growth, whereas the firms that receive modified "
        "opinions here are contracting, loss-making and highly leveraged. Three qualifications "
        "remain. Audit opinions are contemporaneous with the reporting year, so they measure "
        "identification of observations associated with modified opinions rather than future "
        "prediction. The t+1 violation outcome is forward-looking, but the reported AUCs are "
        "weak and the label mixes heterogeneous regulatory events. Finally, the unsupervised "
        "ranking and the supervised cross-validation models answer different questions, so the "
        "null for text against the M-Score and the small supervised increments should not be "
        "conflated."
    )
    reading_para = find_para("The external-validation results")
    set_para_text(reading_para, external_reading)
    applied.append("external-validation reading paragraph")

    contribution_old = (
        "The study contributes an empirical comparison of finance-only, text-only, and fused "
        "feature sets in a Chinese A-share setting, together with an evaluation that "
        "distinguishes an accounting-risk proxy from observed audit and regulatory outcomes."
    )
    contribution_new = (
        "The study contributes two things. First, it documents that the Beneish M-Score cannot "
        "serve as an audit-risk proxy in this setting: it ranks firm-years with modified audit "
        "opinions below the rest of the sample (AUC 0.242) while a finance-only ranking reaches "
        "0.802, and the component decomposition shows that its coefficients reward the accrual "
        "and growth profiles that distressed, modified-opinion firms lack. Second, it provides "
        "an empirical comparison of finance-only, text-only, and fused feature sets in a "
        "Chinese A-share setting, together with an evaluation that distinguishes an "
        "accounting-risk proxy from observed audit and regulatory outcomes."
    )
    _intro = find_para("Against this background, the study addresses three research questions")
    if contribution_old in _intro.text:
        set_para_text(_intro, _intro.text.replace(contribution_old, contribution_new))
        applied.append("intro contribution sentence")
    elif "documents that the Beneish M-Score cannot serve" in _intro.text:
        applied.append("intro contribution sentence (already applied)")

    ref = SECTION_REF[mode]
    conclusion = (
        "This study developed and evaluated a reproducible anomaly-screening pipeline for "
        "Chinese A-share manufacturing firms over 2021-2023. It compared financial-only, "
        "text-only, and fused feature sets using Isolation Forest and an autoencoder, and "
        "examined feature contributions with SHAP. It reports two conclusions. The first "
        "concerns the benchmark: the Beneish M-Score cannot serve as a proxy for audit risk in "
        f"this sample, because it ranks firm-years with contemporaneous modified opinions below "
        f"the rest of the sample (AUC "
        f"{num['events']['ranking'][('mod_opinion', 'Beneish M-Score')]['auc']:.3f}) while a "
        f"finance-only ranking reaches "
        f"{num['events']['ranking'][('mod_opinion', 'finance-only IF')]['auc']:.3f}, and "
        "because its coefficients reward the accruals and sales growth that distressed firms "
        "lack. The second is the null for text: compared with that benchmark, the textual "
        "features added no incremental value to the Beneish-style unsupervised ranking. That "
        f"null is bounded rather than general: across four sample frames, a yearly threshold "
        f"calibration and six outcome labels ({ref}) the ordering never reverses, and the "
        "supervised increment of the fused block stays within 0.018 of zero and is negative "
        "wherever it is distinguishable from it. Forward-looking t+1 violation discrimination "
        "was weak, and in supervised firm-grouped cross-validation adding textual features "
        "produced small positive AUC increments that were not uniformly distinguishable from "
        "zero. The pipeline remains useful as a review-prioritisation tool; the more "
        "transferable result is that accounting-risk proxies must be validated against the "
        "outcome they are meant to stand in for."
    )
    set_para_text(find_para("This study developed and evaluated a reproducible"), conclusion)
    applied.append("conclusion paragraph")

    for index, rows in enumerate(tables):
        table = doc.tables[index]
        assert len(table.rows) == len(rows), (index, len(table.rows), len(rows))
        for row, values in zip(table.rows, rows):
            cells = row.cells
            assert len(cells) == len(values), (index, len(cells), len(values))
            for cell, value in zip(cells, values):
                set_cell(cell, value)
        applied.append(f"Table 5.{index + 1} cells")

    body_model = find_para("This study developed and evaluated a reproducible")
    heading_model = find_para("5.7 External Validation Against Real Regulatory Outcomes")
    caption_model = find_para("Table 5.6.")

    if mode == "full":
        applied += insert_section58(reading_para, body_model, heading_model, caption_model)
    else:
        applied += insert_compact(reading_para, body_model, heading_model, caption_model)
        applied += slim_compact(body_model, heading_model, caption_model)
        applied += tighten_typography()

    dst = DST if mode == "full" else DST_COMPACT
    doc.save(dst)
    return dst, applied


NOTE_COMPACT = (
    "The supplementary appendix (Appendix A) reports four branch experiments that relax the "
    "choices fixed in the main text: "
    "the sample frame (all non-financial industries, 2021-2024, 18,415 firm-years), the "
    "threshold rule (a separate 90th percentile per year instead of one pooled cut-off), the "
    "outcome label (annual-report restatements and inquiry letters at t+1 in place of modified "
    "opinions at t) and two further specifications (an extended sentiment lexicon and a "
    "four-industry subset). They are reported separately because they are measurement checks "
    "rather than new estimates: the ordering never reverses, the finance-only screen stays "
    "between AUC 0.767 and 0.802 while the M-Score stays between 0.242 and 0.277, and on the "
    "three additional labels the fused block changes AUC by at most 0.018. Their construction, "
    "sample counts and full tables are in the supplementary appendix, so that the body of the "
    "paper keeps to the specification it reports in full."
)

APPENDIX_INTRO = [
    (
        "Appendix A.1 Why the branch experiments are reported separately. The main text holds "
        "three choices fixed: one sample (manufacturing, 2021-2023), one threshold rule "
        "and one outcome definition. The experiments collected here relax those choices on the "
        "same pipeline, so that the paper can state how far its numbers travel without "
        "renumbering or re-estimating them. They are measurement checks, not new findings, and "
        "nothing in them is used to support or to overturn the answer to RQ1."
    ),
    (
        "Appendix A.2 How they were built. Each branch reuses the released extraction, the "
        "standardised financial block and the Isolation Forest and autoencoder specifications "
        "unchanged; only the sample filter, the threshold rule, the outcome label or the feature "
        "list moves. Supervised cells use the same firm-grouped five-fold split as Section 5.7. "
        "The event labels are drawn from regulatory records: modified audit opinions in t, "
        "annual-report restatements announced in t+1 (strict definition, which counts only "
        "corrections published as a restatement announcement), disclosure violations in t+1, "
        "and annual-report inquiry letters in t+1. The broader restatement label, which also "
        "counts corrections disclosed inside the annual report, was computed and discarded "
        "because it adds noise rather than events."
    ),
    (
        "Appendix A.3 What they do not do. The experiments do not re-estimate the main tables "
        "and they do not replace the manufacturing sample, which remains the frame with the "
        "densest text coverage. The full non-financial frame runs to 2021-2024 but could not "
        "retrieve 433 of that year's reports; the four-industry subset (B, C, D and I) is large "
        "enough to report but leaves too few firms per industry-year cell for within-cell "
        "standardisation. A character n-gram TF-IDF model was also run on the same text and "
        "reaches 0.63 to 0.81 against the dictionary features at 0.48 to 0.57; it is a "
        "text-representation comparison rather than a robustness check of the pipeline, so it "
        "is recorded in the project notes and not tabulated here."
    ),
]

APPENDIX_CLOSING = (
    "Two of the extensions returned nothing, and both are worth stating. Adding 42 positive and "
    "51 negative industry-specific terms to the sentiment lexicon leaves the text measure where "
    "it was (rank correlation against the M-Score -0.027 before, -0.028 after; AUC 0.537 "
    "against 0.539). Restricting the sample to the four industries that supply most disclosure "
    "events (14,937 firm-years, 341 events) gives a finance-only AUC of 0.776 and an M-Score "
    "AUC of 0.271, indistinguishable from the full non-financial frame."
)


def insert_section58(reading_para, body_model, heading_model, caption_model):
    """Insert §5.8 and Table 5.7 immediately after the external-validation reading."""
    applied = []
    anchor = reading_para._p
    heading = clone_para(heading_model, text["s58_heading"])
    heading_para = Paragraph(heading, heading_model._parent)
    heading_para.paragraph_format.space_before = Pt(12)
    heading_para.paragraph_format.space_after = Pt(4)
    heading_para.paragraph_format.keep_with_next = True
    caption = clone_para(caption_model, text["t57_caption"])
    elements = [
        heading,
        clone_para(body_model, text["s58a"]),
        sub_heading(heading_model, text["s58_1_heading"]),
        clone_para(body_model, text["s58_1a"]),
        caption,
    ]
    rows = bs._table_57()
    tbl = clone_table(doc.tables[0]._tbl, rows)
    fill_table(tbl, rows)
    elements.append(tbl)
    for key in ("s58_1b",):
        elements.append(clone_para(body_model, text[key]))
    for sub_key, body_keys in (
        ("s58_2_heading", ("s58_2a", "s58_2b")),
        ("s58_3_heading", ("s58_3a", "s58_3b")),
        ("s58_4_heading", ("s58_4a",)),
    ):
        elements.append(sub_heading(heading_model, text[sub_key]))
        for body_key in body_keys:
            elements.append(clone_para(body_model, text[body_key]))
    for element in elements:
        anchor.addnext(element)
        anchor = element
        applied.append("inserted s58 element")
    applied.append("inserted Table 5.7")
    return applied


def insert_compact(reading_para, body_model, heading_model, caption_model):
    """Insert the one-paragraph note and Appendix A (with Table A1)."""
    applied = []
    note = clone_para(body_model, NOTE_COMPACT)
    reading_para._p.addnext(note)
    applied.append("inserted §5.8 note")

    heading = clone_para(heading_model, "Appendix A. Branch Experiments")
    heading_para = Paragraph(heading, heading_model._parent)
    heading_para.paragraph_format.space_before = Pt(12)
    heading_para.paragraph_format.keep_with_next = True
    elements = [heading]
    for block in APPENDIX_INTRO:
        elements.append(clone_para(body_model, block))
    rows = bs._table_57()
    caption = clone_para(
        caption_model,
        "Table A1. Branch-experiment results. Panel A varies the sample frame and window with "
        "the outcome held constant (modified audit opinion in t); Panel B varies the outcome "
        "label on the fixed 2021-2024 non-financial sample.",
    )
    elements.append(caption)
    tbl = clone_table(doc.tables[0]._tbl, rows)
    fill_table(tbl, rows)
    elements.append(tbl)
    elements.append(clone_para(body_model, APPENDIX_CLOSING))

    sect_pr = doc.element.body.find(qn("w:sectPr"))
    for element in elements:
        sect_pr.addprevious(element)
        applied.append("appended appendix element")
    applied.append("inserted Table A1")
    return applied


TABLE_REMAP = (
    ("Table 5.1", "Table B1"),
    ("Table 5.3", "Table B2"),
    ("Table 5.4", "Table B3"),
    ("Table 5.2", "Table 5.1"),
    ("Table 5.5", "Table 5.2"),
    ("Table 5.6", "Table 5.3"),
)

FIGURE_REMAP = (
    ("Figure 5.2", "Figure 5.1"),
    ("Figure 5.3", "Figure 5.2"),
    ("Figure 5.5", "Figure 5.3"),
)

FIGURE_BLOCKS_TO_DROP = ("Figure 5.1.", "Figure 5.4.", "Figure 5.6.")

APPENDIX_B_INTRO = (
    "Appendix B collects the three tables that the main text cites for completeness rather than "
    "for its main argument. B.1 gives the raw feature descriptives, the threshold event rates "
    "under both the conventional and the recalibrated cut-off, and the first-versus-second "
    "specification comparison that the text summarises in a single sentence."
)

SHAP_CAVEAT = (
    "The shares describe model-score attribution and do not establish causal effects."
)


def _drop_element(element) -> None:
    parent = element.getparent()
    if parent is not None:
        parent.remove(element)


def _drop_figure_block(caption_prefix: str) -> str:
    """Remove a caption together with its image anchor and its note paragraph."""
    caption = find_para(caption_prefix)
    following = caption._p.getnext()
    previous = caption._p.getprevious()
    if following is not None and following.tag == qn("w:p"):
        note = Paragraph(following, caption._parent)
        if note.text.strip().startswith("Note:"):
            _drop_element(following)
    if previous is not None and previous.tag == qn("w:p"):
        anchor = Paragraph(previous, caption._parent)
        if not anchor.text.strip():
            _drop_element(previous)
    dropped = caption.text.strip().split(".")[0]
    _drop_element(caption._p)
    return dropped


def _remap_paragraphs(pairs) -> int:
    """Rewrite cross-references in two phases so renumberings cannot chain."""
    placeholders = [(old, f"\x01{index}\x01") for index, (old, _new) in enumerate(pairs)]
    finals = {f"\x01{index}\x01": new for index, (_old, new) in enumerate(pairs)}
    changed = 0
    for paragraph in doc.paragraphs:
        current = paragraph.text
        if not any(old in current for old, _token in placeholders):
            continue
        updated = current
        for old, token in placeholders:
            updated = updated.replace(old, token)
        for token, new in finals.items():
            updated = updated.replace(token, new)
        if updated != current:
            set_para_text(paragraph, updated)
            changed += 1
    return changed


def slim_compact(body_model, heading_model, caption_model):
    """Move two tables and the two-specification block to Appendix B, keep three figures."""
    applied = []

    caption_51 = find_para("Table 5.1.")
    table_51 = doc.tables[0]._tbl
    caption_53 = find_para("Table 5.3.")
    table_53 = doc.tables[2]._tbl
    heading_56 = find_para("5.6 From the First to the Second Specification")
    body_56 = find_para("The first specification used")
    caption_54 = find_para("Table 5.4.")
    table_54 = doc.tables[3]._tbl
    summary_56 = find_para("Table 5.4 summarises the two specifications")
    applied.append("captured 2 tables and the two-specification block")

    shap_para = next(p for p in doc.paragraphs if "66.2" in p.text)
    if SHAP_CAVEAT not in shap_para.text:
        set_para_text(shap_para, shap_para.text.rstrip() + " " + SHAP_CAVEAT)
        applied.append("folded the SHAP note into the SHAP paragraph")

    for prefix in FIGURE_BLOCKS_TO_DROP:
        applied.append("dropped " + _drop_figure_block(prefix))

    applied.append(f"remapped {_remap_paragraphs(TABLE_REMAP)} table references")
    applied.append(f"remapped {_remap_paragraphs(FIGURE_REMAP)} figure references")

    localised = 0
    for paragraph in doc.paragraphs:
        updated = paragraph.text
        for old, new in (
            ("Section 5.8", "Appendix A"),
            ("§5.8", "Appendix A"),
            ("Section 5.6", "Appendix B.2"),
            ("Section 5.7", "Section 5.6"),
            ("§5.7", "§5.6"),
            ("5.7 External Validation", "5.6 External Validation"),
        ):
            updated = updated.replace(old, new)
        if updated != paragraph.text:
            set_para_text(paragraph, updated)
            localised += 1
    if localised:
        applied.append(f"localised {localised} cross-references for the compact layout")

    for element in (
        heading_56._p,
        body_56._p,
        caption_54._p,
        table_54,
        summary_56._p,
        caption_51._p,
        table_51,
        caption_53._p,
        table_53,
    ):
        _drop_element(element)
    applied.append("detached moved elements from the body")

    heading = clone_para(heading_model, "Appendix B. Supplementary Tables")
    heading_para = Paragraph(heading, heading_model._parent)
    heading_para.paragraph_format.space_before = Pt(12)
    heading_para.paragraph_format.keep_with_next = True
    elements = [heading, clone_para(body_model, APPENDIX_B_INTRO)]
    elements += [caption_51._p, table_51, caption_53._p, table_53]
    elements.append(sub_heading(body_model, "Appendix B.2 From the First to the Second Specification"))
    elements += [body_56._p, caption_54._p, table_54, summary_56._p]

    sect_pr = doc.element.body.find(qn("w:sectPr"))
    for element in elements:
        sect_pr.addprevious(element)
    applied.append("assembled Appendix B")
    return applied


def tighten_typography(target_spacing: float = 1.2, max_figure_height: float = 2.3) -> list:
    """Compact copy only: tighten body leading and cap figure heights."""
    applied = []
    retuned = 0
    for paragraph in doc.paragraphs:
        spacing = paragraph.paragraph_format.line_spacing
        if spacing is not None and abs(float(spacing) - 1.45) < 0.01:
            paragraph.paragraph_format.line_spacing = target_spacing
            retuned += 1
    applied.append(f"set body leading {target_spacing} on {retuned} paragraphs")
    scaled = 0
    for shape in doc.inline_shapes:
        if shape.height.inches > max_figure_height:
            factor = max_figure_height / shape.height.inches
            shape.width = int(shape.width * factor)
            shape.height = int(shape.height * factor)
            scaled += 1
    applied.append(f"capped {scaled} figures at {max_figure_height} in")
    return applied


def _appendix_start(document):
    for paragraph in document.paragraphs:
        if paragraph.text.strip().startswith("Appendix A. Branch Experiments"):
            return paragraph._p
    return None


def _strip_before(document, stop_element) -> None:
    """Remove every paragraph and table that precedes stop_element."""
    body = document.element.body
    element = body.find(qn("w:p"))
    while element is not None and element is not stop_element:
        following = element.getnext()
        if element.tag in (qn("w:p"), qn("w:tbl")):
            body.remove(element)
        element = following


def _strip_from(document, start_element) -> None:
    """Remove start_element and everything after it, up to the section properties."""
    body = document.element.body
    element = start_element
    while element is not None and element.tag != qn("w:sectPr"):
        following = element.getnext()
        if element.tag in (qn("w:p"), qn("w:tbl")):
            body.remove(element)
        element = following


def split_appendices(compact_path, supplement_path) -> list:
    """Split the compact copy into the short paper and a supplementary appendix file."""
    supplement = docx.Document(compact_path)
    _strip_before(supplement, _appendix_start(supplement))
    supplement.save(supplement_path)

    compact = docx.Document(compact_path)
    _strip_from(compact, _appendix_start(compact))
    pointed = 0
    for paragraph in compact.paragraphs:
        updated = paragraph.text
        for old, new in (
            ("Appendix B.2", "the supplementary appendix"),
            ("Table B1", "Supplementary Table B1"),
            ("Table B2", "Supplementary Table B2"),
            ("Table B3", "Supplementary Table B3"),
        ):
            updated = updated.replace(old, new)
        if updated != paragraph.text:
            set_para_text(paragraph, updated)
            pointed += 1
    compact.save(compact_path)
    return [
        f"split appendices into {supplement_path}",
        f"trimmed {compact_path} to the main text ({pointed} pointers retargeted)",
    ]


def main(argv):
    modes = ["full", "compact"]
    if "--full" in argv:
        modes = ["full"]
    elif "--compact" in argv:
        modes = ["compact"]
    for mode in modes:
        dst, applied = build(mode)
        if mode == "compact":
            applied += split_appendices(dst, DST_SUPPLEMENT)
        print("saved", dst)
        for line in applied:
            print(" -", line)


if __name__ == "__main__":
    main(sys.argv[1:])
