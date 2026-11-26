# -*- coding: utf-8 -*-
"""
references_apa.py
Author: Group12A2 DSW Team
Purpose: Single source for the APA 7th reference list and the author-year
         citations that replace the numbered [n] style in the manuscript.
Module: src.reporting

The manuscript moves from a mixed GB/T 7714 + APA numbered list to one uniform
management-style list, so the entries, their order, and every in-text form are
defined here and nowhere else. Ordering is alphabetical by first author, as APA
requires; two works by the same author are ordered by year. The legacy number is
kept only as the key that maps an old in-text token to its author-year form.

Revision History
-----------------
2026-11-26  initial version; APA conversion for manuscript v0.4.
"""
from __future__ import annotations

from collections.abc import Iterable

REFERENCES_APA: tuple[str, ...] = (
    "Beneish, M. D. (1999). The detection of earnings manipulation. Financial Analysts Journal, 55(5), 24-36. https://doi.org/10.2469/faj.v55.n5.2296",
    "Chandola, V., Banerjee, A., & Kumar, V. (2009). Anomaly detection: A survey. ACM Computing Surveys, 41(3), Article 15. https://doi.org/10.1145/1541880.1541882",
    "Courtis, J. K. (1998). Annual report readability variability: Tests of the obfuscation hypothesis. Accounting, Auditing & Accountability Journal, 11(4), 459-472. https://doi.org/10.1108/09513579810231457",
    "Dechow, P. M., Ge, W., & Schrand, C. (2010). Understanding earnings quality: A review of the proxies, their determinants and their consequences. Journal of Accounting and Economics, 50(2-3), 344-401. https://doi.org/10.1016/j.jacceco.2010.09.001",
    "Dechow, P. M., Ge, W., Larson, C. R., & Sloan, R. G. (2011). Predicting material accounting misstatements. Contemporary Accounting Research, 28(1), 17-82.",
    "Ertugrul, M., Lei, J., Qiu, J., & Wan, C. (2017). Annual report readability, tone ambiguity, and the cost of borrowing. Journal of Financial and Quantitative Analysis, 52(2), 811-836.",
    "Healy, P. M., & Palepu, K. G. (2001). Information asymmetry, corporate disclosure, and the capital markets: A review of the empirical disclosure literature. Journal of Accounting and Economics, 31(1-3), 405-440. https://doi.org/10.1016/S0165-4101(01)00018-0",
    "Hemachandran, K. (2026). Exploring explainable AI (XAI): Implications for transparency in financial decision-making. In Foundations of artificial intelligence in finance (pp. 22-30). Chapman and Hall/CRC.",
    "Karpoff, J. M., Lee, D. S., & Martin, G. S. (2008). The cost to firms of cooking the books. Journal of Financial and Quantitative Analysis, 43(3), 581-611.",
    "Lehavy, R., Li, F., & Merkley, K. (2011). The effect of annual report readability on analyst following and the properties of their earnings forecasts. The Accounting Review, 86(3), 1087-1115. https://doi.org/10.2308/accr.00000043",
    "Li, F. (2008). Annual report readability, current earnings, and earnings persistence. Journal of Accounting and Economics, 45(2-3), 221-247. https://doi.org/10.1016/j.jacceco.2008.02.003",
    "Liu, F. T., Ting, K. M., & Zhou, Z.-H. (2008). Isolation forest. In Proceedings of the Eighth IEEE International Conference on Data Mining (pp. 413-422). IEEE Computer Society. https://doi.org/10.1109/ICDM.2008.17",
    "Liu, F. T., Ting, K. M., & Zhou, Z.-H. (2012). Isolation-based anomaly detection. ACM Transactions on Knowledge Discovery from Data, 6(1), 1-39.",
    "Loughran, T., & McDonald, B. (2011). When is a liability not a liability? Textual analysis, dictionaries, and 10-Ks. The Journal of Finance, 66(1), 35-65.",
    "Loughran, T., & McDonald, B. (2014). Measuring readability in financial disclosures. The Journal of Finance, 69(4), 1643-1671. https://doi.org/10.1111/jofi.12162",
    "Lundberg, S. M., & Lee, S.-I. (2017). A unified approach to interpreting model predictions. In Advances in Neural Information Processing Systems 30 (pp. 4765-4774). Curran Associates.",
    "Repousis, S. (2016). Using Beneish model to detect corporate financial statement fraud in Greece. Journal of Financial Crime, 23(4), 1063-1073.",
    "Sakurada, M., & Yairi, T. (2014). Anomaly detection using autoencoders with nonlinear dimensionality reduction. In Proceedings of the MLSDA 2014 2nd Workshop on Machine Learning for Sensory Data Analysis (pp. 4-11). ACM. https://doi.org/10.1145/2689746.2689747",
    "Xu, W., Yao, Z., & Chen, D. (2019). Chinese annual report readability: Measurement and test. China Journal of Accounting Studies, 7(3), 407-437. https://doi.org/10.1080/21697213.2019.1701259",
    "Yang, F., David, J. M., & Chang, C.-C. (2023). Detecting financial statement fraud through multidimensional analysis of text readability. Journal of Forensic Accounting Research, 8(1), 74-96. https://doi.org/10.2308/JFAR-2021-019",
    "Yao, J., Feng, X., Wang, Z., Ji, R., & Zhang, W. (2021). Tone, sentiment and market impact: Based on a financial sentiment dictionary. Journal of Management Sciences in China, 24(5), 26-46. [in Chinese]",
    "Zeng, Q., Zhou, B., Zhang, C., & Chen, X. (2018). Annual report tone and insider trading: \"Consistent\" or \"insincere\"? Management World, (9), 143-160. [in Chinese]",
    "Zhou, C., & Paffenroth, R. C. (2017). Anomaly detection with robust deep autoencoders. In Proceedings of the 23rd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining (pp. 665-674). ACM.",
    "Zhou, Y., & Phan, D. H. T. (2026). Digital-related disclosure intensity and short-term financial performance in the FTSE 100: A context-dependent view. Pacific-Basin Finance Journal, 100, 103302.",
)

# Legacy manuscript number -> author-year form used inside parentheses.
# Numbers follow the v0.3 list; they are keys for the conversion, not output.
CITATION_BY_NUMBER: dict[int, str] = {
    1: "Healy & Palepu, 2001",
    2: "Dechow et al., 2010",
    3: "Loughran & McDonald, 2014",
    4: "Courtis, 1998",
    5: "Li, 2008",
    6: "Lehavy et al., 2011",
    7: "Xu et al., 2019",
    8: "Chandola et al., 2009",
    9: "Liu et al., 2008",
    10: "Sakurada & Yairi, 2014",
    11: "Repousis, 2016",
    12: "Beneish, 1999",
    13: "Lundberg & Lee, 2017",
    14: "Zhou & Phan, 2026",
    15: "Ertugrul et al., 2017",
    16: "Yang et al., 2023",
    17: "Liu et al., 2012",
    18: "Zhou & Paffenroth, 2017",
    19: "Karpoff et al., 2008",
    20: "Dechow et al., 2011",
    21: "Hemachandran, 2026",
    22: "Yao et al., 2021",
    23: "Loughran & McDonald, 2011",
    24: "Zeng et al., 2018",
}


def format_citation(numbers: Iterable[int]) -> str:
    """Return '(A, 2001; B, 2010)' for a run of legacy numbers.

    APA orders several works inside one parenthetical alphabetically by first
    author, so the entries are sorted after mapping; the input order therefore
    does not decide the printed order.
    """
    parts = sorted(CITATION_BY_NUMBER[int(number)] for number in numbers)
    return "(" + "; ".join(parts) + ")"


def reference_order_check() -> list[str]:
    """Return the surnames in list order so a test can assert alphabetical order."""
    return [entry.split(",")[0] for entry in REFERENCES_APA]
