"""Parse the государственный экзамен DOCX into questions.json.

This is the preferred parser: DOCX tables are first-class objects, so each
question cell arrives whole instead of fragmented across PDF layout boxes.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph


DOCX_PATH = Path(r"c:\Users\User\Desktop\fos_gia_vo_bak_09_03_02_rsob (2).docx")
OUT_DIR = Path(__file__).resolve().parent.parent / "data"
OUT_FILE = OUT_DIR / "questions.json"


DISC_RE = re.compile(r"^Дисциплина\s+(\d+)\s*:\s*(.+)$")
# Russian alphabet without Ё/Й/Ъ/Ы/Ь, used for option labels. PDF/DOCX
# occasionally have up to ~10 options in sequence-style questions.
CYR_OPT_CLASS = r"[АБВГДЕЖЗИКЛ]"
LATIN_OPT_CLASS = r"[A-IK-L]"  # A..L without J
OPTION_RE = re.compile(
    rf"(?:^|\n|\s)({CYR_OPT_CLASS}|{LATIN_OPT_CLASS})\s*\)\s*", re.MULTILINE,
)
PAIR_RE = re.compile(rf"(\d+)\s*[-–—]\s*({CYR_OPT_CLASS}|{LATIN_OPT_CLASS})")
# Reverse format: letter-number, e.g. "А-1, Б-2" (sometimes used in DOCX)
REVERSE_PAIR_RE = re.compile(rf"({CYR_OPT_CLASS}|{LATIN_OPT_CLASS})\s*[-–—]\s*(\d+)")
MATCHING_ANS_RE = re.compile(
    rf"\d+\s*[-–—]\s*(?:{CYR_OPT_CLASS}|{LATIN_OPT_CLASS})"
    rf"|(?:{CYR_OPT_CLASS}|{LATIN_OPT_CLASS})\s*[-–—]\s*\d+"
)
MULTI_HINT_RE = re.compile(r"правильн\w*\s+варианты", re.IGNORECASE)
SEQUENCE_HINT_RE = re.compile(
    r"последовательност|"
    r"\bустановите\s+приоритет|"
    r"\bупорядоч[ьи]те|"
    r"\bрасположите|"
    r"\bв\s+(?:правильн\w+\s+)?порядке|"
    r"\bв\s+следующем\s+порядке|"
    r"\bпо\s+приоритету|"
    r"\bв\s+порядке\s+(?:возрастания|убывания|следования)",
    re.IGNORECASE,
)

LATIN_TO_CYR = {
    "A": "А", "B": "Б", "C": "В", "D": "Г", "E": "Д",
    "F": "Е", "G": "Ж", "H": "З", "I": "И", "K": "К", "L": "Л",
}
CYR_ORDER = ["А", "Б", "В", "Г", "Д", "Е", "Ж", "З", "И", "К", "Л"]
PROMPT_PREFIX_RE = re.compile(
    r"^\s*Выберите\s+правильн(?:ый|ые)\s+вариант(?:ы)?\s+ответа\s*:?\s*",
    flags=re.IGNORECASE | re.DOTALL,
)


def iter_blocks(doc):
    body = doc.element.body
    for child in body.iterchildren():
        if child.tag == qn("w:p"):
            yield "p", Paragraph(child, doc)
        elif child.tag == qn("w:tbl"):
            yield "t", Table(child, doc)


def classify_section(p_text: str):
    s = p_text.lower()
    if "закрытого" in s:
        return "closed"
    if "последовательност" in s or "соответстви" in s:
        return "set"
    if "открытого" in s:
        return "open"
    return None


def strip_prompt(text: str) -> str:
    return PROMPT_PREFIX_RE.sub("", text, count=1).strip()


def squash(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def parse_options(text: str) -> dict:
    """Return {letter: option_text} parsed from a column like
    'А) one\nБ) two\nВ) three\nГ) four'. Handles latin 'A)' as Cyrillic 'А'.

    Discipline 4 (and possibly others) sometimes lists options without
    letter prefixes — just lines separated by '\n'. We fall back to numbering
    those lines А, Б, В, Г, ... in order.
    """
    matches = list(OPTION_RE.finditer(text))
    if matches:
        options = {}
        for i, m in enumerate(matches):
            key = LATIN_TO_CYR.get(m.group(1), m.group(1))
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            val = text[m.end():end]
            val = val.strip(" \n\t|;,")
            val = squash(val)
            if key not in options:
                options[key] = val
            else:
                options[key] += " " + val
        return options

    # Fallback: no letter markers — split by newlines and label A..E in order.
    lines = [ln.strip(" \t|;,") for ln in text.splitlines() if ln.strip()]
    if 2 <= len(lines) <= len(CYR_ORDER):
        return {CYR_ORDER[i]: squash(ln) for i, ln in enumerate(lines)}
    return {}


def parse_left_right(text: str, answer_pairs: list):
    """Parse matching cell: '1. Foo\n2. Bar\nА) X\nБ) Y' (or with mixed punctuation).

    Returns (left_items, right_items) where each is a dict {key: text}.
    `answer_pairs` is the list of (num, letter) tuples we expect.

    Falls back gracefully when the left column has no numeric prefixes
    (common in discipline 4): in that case the text before the first
    lettered option is split by lines and labelled 1..N.
    """
    expected_left = sorted({n for n, _ in answer_pairs}, key=int) if answer_pairs else []
    expected_right = sorted({l for _, l in answer_pairs}) if answer_pairs else []

    left_re = re.compile(
        rf"(?:^|\n)\s*(\d+)\s*(?:\)|\.)\s*"
        rf"([^\n]+(?:\n(?!\s*\d+\s*(?:\)|\.)|\s*(?:{CYR_OPT_CLASS}|{LATIN_OPT_CLASS})\s*[\.\)])[^\n]+)*)",
        re.MULTILINE,
    )
    right_re = re.compile(
        rf"(?:^|\n)\s*({CYR_OPT_CLASS}|{LATIN_OPT_CLASS})\s*[\.\)]\s*"
        rf"([^\n]+(?:\n(?!\s*(?:{CYR_OPT_CLASS}|{LATIN_OPT_CLASS})\s*[\.\)]|\s*\d+\s*(?:\)|\.))[^\n]+)*)",
        re.MULTILINE,
    )

    left = {}
    for m in left_re.finditer(text):
        n = m.group(1)
        if n in left:
            continue
        left[n] = squash(m.group(2))

    right = {}
    for m in right_re.finditer(text):
        l = LATIN_TO_CYR.get(m.group(1), m.group(1))
        if l in right:
            continue
        right[l] = squash(m.group(2))

    # Fallback for left column without numeric prefixes (e.g. discipline 4).
    # We take everything before the first lettered item and split by lines.
    if not left and expected_left:
        first_right = right_re.search(text)
        if first_right:
            left_blob = text[: first_right.start()]
        else:
            left_blob = text
        lines = [ln.strip(" \t|;,") for ln in left_blob.splitlines() if ln.strip()]
        if len(lines) >= len(expected_left):
            for i, n in enumerate(expected_left):
                if i < len(lines):
                    left[n] = squash(lines[i])

    # If the right column also turned up empty but left/expected_right is known,
    # try to grab lines after the left block.
    if not right and expected_right and left:
        if first_right_match := right_re.search(text):
            tail = text[first_right_match.start():]
        else:
            # take whatever is after the last line we used for left
            tail = ""
        if tail:
            for m in right_re.finditer(tail):
                l = LATIN_TO_CYR.get(m.group(1), m.group(1))
                if l in right:
                    continue
                right[l] = squash(m.group(2))

    return left, right, expected_left, expected_right


def extract_answer_letters(text: str) -> list:
    """Return a list of Cyrillic option letters from the answer cell, in order."""
    found = re.findall(rf"{CYR_OPT_CLASS}|{LATIN_OPT_CLASS}", text.upper())
    return [LATIN_TO_CYR.get(c, c) for c in found]


def build_closed_or_seq(statement_raw, options_raw, answer_raw):
    """Parse a question from a row in the 'closed' or 'set' section."""
    answer_raw = answer_raw.strip()
    statement = strip_prompt(statement_raw)
    statement = squash(statement)

    if MATCHING_ANS_RE.search(answer_raw):
        # Try the normal "number-letter" pattern first, fall back to
        # reversed "letter-number" if needed.
        pairs = [(n, LATIN_TO_CYR.get(l, l)) for n, l in PAIR_RE.findall(answer_raw)]
        if not pairs:
            pairs = [(n, LATIN_TO_CYR.get(l, l)) for l, n in REVERSE_PAIR_RE.findall(answer_raw)]
        if not pairs:
            return None
        left, right, exp_left, exp_right = parse_left_right(options_raw, pairs)
        answer_map = {n: l for n, l in pairs}
        return {
            "type": "matching",
            "statement": statement,
            "left": [
                {"key": k, "text": left.get(k, "")}
                for k in (exp_left or sorted(left.keys(), key=int))
            ],
            "right": [
                {"key": k, "text": right.get(k, "")}
                for k in (exp_right or sorted(right.keys()))
            ],
            "answer": answer_map,
            "raw_options": options_raw,
            "raw_answer": answer_raw,
        }

    options = parse_options(options_raw)
    if not options:
        # No option markers — treat as open-style fallback (rare)
        return {
            "type": "open",
            "statement": statement,
            "answer": squash(answer_raw),
        }

    letters = extract_answer_letters(answer_raw)
    seen = set()
    letters_unique = []
    for c in letters:
        if c in options and c not in seen:
            letters_unique.append(c)
            seen.add(c)

    is_full_permutation = (
        len(letters_unique) >= 3
        and len(letters_unique) == len(options)
        and set(letters_unique) == set(options.keys())
    )
    has_seq_hint = bool(SEQUENCE_HINT_RE.search(statement))
    is_multi_hinted = bool(MULTI_HINT_RE.search(statement_raw))

    if is_full_permutation and (has_seq_hint or not is_multi_hinted):
        return {
            "type": "sequence",
            "statement": statement,
            "items": [
                {"key": k, "text": options[k]} for k in CYR_ORDER if k in options
            ],
            "answer": letters_unique,
            "raw_answer": answer_raw,
        }

    qtype = "multi" if (is_multi_hinted or len(letters_unique) > 1) else "single"
    return {
        "type": qtype,
        "statement": statement,
        "options": [
            {"key": k, "text": options[k]} for k in CYR_ORDER if k in options
        ],
        "answer": letters_unique,
        "raw_answer": answer_raw,
    }


def build_open(statement_raw, answer_raw):
    statement = strip_prompt(statement_raw).strip()
    # Preserve newlines for code blocks (JS questions)
    if "\n" in statement and re.search(r"[{};=()<>]", statement):
        statement = re.sub(r"[ \t]+", " ", statement)
        statement = re.sub(r"\n{2,}", "\n", statement).strip()
    else:
        statement = squash(statement)
    answer = squash(answer_raw)
    return {
        "type": "open",
        "statement": statement,
        "answer": answer,
    }


def main():
    print(f"Reading {DOCX_PATH} ...")
    doc = Document(str(DOCX_PATH))

    questions = []
    counters = {}
    discipline_num = 0
    discipline_name = ""
    section = None

    for kind, block in iter_blocks(doc):
        if kind == "p":
            txt = block.text.strip()
            if not txt:
                continue
            m = DISC_RE.match(txt)
            if m:
                discipline_num = int(m.group(1))
                discipline_name = m.group(2).strip()
                continue
            sec = classify_section(txt)
            if sec is not None:
                section = sec
        elif kind == "t":
            if section is None or discipline_num == 0:
                # Skip preamble tables (cover/metadata before the first
                # discipline header). Warn loudly if any non-trivial table
                # passes through here so we don't silently lose questions.
                if len(block.rows) > 3:
                    print(
                        f"[WARN] Skipped table with {len(block.rows)} rows "
                        f"(no discipline/section context yet)"
                    )
                continue
            rows = block.rows
            if len(rows) < 2:
                continue

            for row in rows[1:]:
                cells = [c.text.strip() for c in row.cells]
                if section == "open":
                    if len(cells) < 3:
                        continue
                    statement_raw = cells[1]
                    answer_raw = cells[2]
                    if not statement_raw or not answer_raw:
                        continue
                    q = build_open(statement_raw, answer_raw)
                else:
                    if len(cells) < 4:
                        continue
                    statement_raw = cells[1]
                    options_raw = cells[2]
                    answer_raw = cells[3]
                    if not statement_raw or not answer_raw:
                        continue
                    q = build_closed_or_seq(statement_raw, options_raw, answer_raw)
                if q is None:
                    continue

                counters[discipline_num] = counters.get(discipline_num, 0) + 1
                q["id"] = f"d{discipline_num}-{q['type']}-{counters[discipline_num]:03d}"
                q["discipline_num"] = discipline_num
                q["discipline_name"] = discipline_name
                questions.append(q)

    # Sanity check: every question must have a non-empty id and discipline.
    from collections import Counter as _C
    id_counts = _C(q.get("id") for q in questions)
    bad_id = [q.get("id") for q in questions if not q.get("id") or not q.get("discipline_num")]
    dup_ids = [i for i, n in id_counts.items() if i and n > 1]
    if bad_id:
        print(f"[WARN] {len(bad_id)} questions have empty id/discipline: {bad_id[:5]}")
    if dup_ids:
        print(f"[WARN] Duplicate ids generated: {dup_ids[:5]}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(
        json.dumps(questions, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"Parsed: {len(questions)} -> {OUT_FILE}")

    by_type = {}
    by_disc = {}
    for q in questions:
        by_type[q["type"]] = by_type.get(q["type"], 0) + 1
        key = (q["discipline_num"], q["discipline_name"])
        by_disc.setdefault(
            key, {"single": 0, "multi": 0, "matching": 0, "sequence": 0, "open": 0}
        )
        by_disc[key][q["type"]] += 1

    print("\nBy type:", by_type)
    print("\nBy discipline:")
    for (n, name), counts in sorted(by_disc.items()):
        total = sum(counts.values())
        print(f"  {n}. {name}: {total} total {counts}")


if __name__ == "__main__":
    main()
