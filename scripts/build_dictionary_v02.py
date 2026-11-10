# -*- coding: utf-8 -*-
"""
build_dictionary_v02.py
Author: Group12A2 DSW Team
Purpose: Build the v0.2 financial sentiment dictionary from the full public
         Yao-Jiaquan et al. (2021) formal-text lexicon, replacing the v0.1
         bootstrap subset. Also emits a jieba user-dictionary so multi-character
         financial terms are tokenised as single units.

Usage: .venv/Scripts/python scripts/build_dictionary_v02.py

Revision History
----------------
2026-11-11  initial version: parse Yao2021_formal_sentiment_score.txt (word score),
            split positive/negative, keep pure-Chinese words, write pipeline files
            and a jieba user dictionary; back up the v0.1 files first.
"""
import re
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

DICT_DIR = PROJECT_ROOT / "data" / "external" / "dictionaries"
SRC = DICT_DIR / "yuanjiaguan_2021" / "Yao2021_formal_sentiment_score.txt"
BACKUP_DIR = DICT_DIR / "v0.1_bootstrap_backup"

POS_OUT = DICT_DIR / "financial_positive.txt"
NEG_OUT = DICT_DIR / "financial_negative.txt"
USERDICT_OUT = DICT_DIR / "jieba_userdict.txt"

PURE_CHINESE = re.compile(r"^[\u4e00-\u9fff]+$")


def parse_score_file(path: Path) -> tuple[list[str], list[str], list[str]]:
    positive: list[str] = []
    negative: list[str] = []
    other: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        parts = line.rsplit(None, 1)
        if len(parts) != 2:
            other.append(line)
            continue
        word, score_s = parts[0].strip(), parts[1].strip()
        try:
            score = int(score_s)
        except ValueError:
            other.append(line)
            continue
        if score > 0:
            positive.append(word)
        elif score < 0:
            negative.append(word)
        else:
            other.append(line)
    return positive, negative, other


def main() -> int:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    for name in ("financial_positive.txt", "financial_negative.txt", "uncertainty.txt"):
        src = DICT_DIR / name
        if src.exists() and not (BACKUP_DIR / name).exists():
            shutil.copy2(src, BACKUP_DIR / name)
            print(f"backed up v0.1 {name} -> {BACKUP_DIR / name}")

    positive, negative, other = parse_score_file(SRC)
    print(f"raw positive {len(positive)}, negative {len(negative)}, unparsed {len(other)}")

    pos_cn = [w for w in positive if PURE_CHINESE.match(w)]
    neg_cn = [w for w in negative if PURE_CHINESE.match(w)]
    dropped_pos = len(positive) - len(pos_cn)
    dropped_neg = len(negative) - len(neg_cn)
    print(f"pure-Chinese positive {len(pos_cn)} (dropped {dropped_pos}), "
          f"negative {len(neg_cn)} (dropped {dropped_neg})")

    pos_cn = sorted(set(pos_cn))
    neg_cn = sorted(set(neg_cn))
    overlap = set(pos_cn) & set(neg_cn)
    if overlap:
        print(f"WARNING overlap {len(overlap)} words in both lists: {sorted(overlap)[:10]}")
        pos_cn = [w for w in pos_cn if w not in overlap]
        neg_cn = [w for w in neg_cn if w not in overlap]
    print(f"final positive {len(pos_cn)}, negative {len(neg_cn)}")

    header = (
        "# 中文金融正向/负向情感词典（v0.2 全量正式文本版）\n"
        "# 来源：姚加权、冯绪、王赞钧、纪荣嵘、张维(2021)《语调、情绪及市场影响：基于金融情绪词典》，\n"
        "#       管理科学学报 24(5):26-46。取正式文本(formal)词典；数字/字母条目与正负重叠词已剔除。\n"
        "# 获取：https://github.com/DavionWu2018/Sentiment_dictionary（金融领域中文情绪词典_姚加权等(2021)）\n"
    )
    POS_OUT.write_text(header + "\n".join(pos_cn) + "\n", encoding="utf-8")
    NEG_OUT.write_text(header + "\n".join(neg_cn) + "\n", encoding="utf-8")

    # jieba user dictionary: all pure-Chinese words at a uniform high frequency
    # so multi-character financial terms survive segmentation as single tokens.
    userdict_lines = [f"{w} 1000" for w in sorted(set(pos_cn) | set(neg_cn))]
    USERDICT_OUT.write_text("\n".join(userdict_lines) + "\n", encoding="utf-8")
    print(f"wrote {POS_OUT} ({len(pos_cn)}), {NEG_OUT} ({len(neg_cn)}), "
          f"{USERDICT_OUT} ({len(userdict_lines)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
