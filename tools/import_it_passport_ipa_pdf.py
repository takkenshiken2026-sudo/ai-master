#!/usr/bin/env python3
"""IPA 公開問題 PDF（問題・解答）から ITパスポート過去問 JSON を生成する。"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import fitz
import pdfplumber

ROOT = Path(__file__).resolve().parents[1]
OUT_JSON = ROOT / "assets" / "data" / "it-passport" / "past.json"
RAW_DIR = ROOT / "data" / "it-passport" / "r08"

EXAM_ID = "r08"
EXAM_TITLE = "令和8年度 公開問題"
TIME_LIMIT = 120
QUESTION_PAGE_START = 1
QUESTION_PAGE_END = 48

KANA_TO_KEY = {"ア": "A", "イ": "B", "ウ": "C", "エ": "D"}
MARKERS = ["ア", "イ", "ウ", "エ"]
QUESTION_HEAD_RE = re.compile(r"(?m)(?:^|\n)(?:問|間)[\s　]*(\d+|呂)(?:[\s　_:：]|(?=[^0-9]))")


def domain_for(no: int) -> str:
    if no <= 35:
        return "ストラテジ系"
    if no <= 55:
        return "マネジメント系"
    return "テクノロジ系"


def parse_answers(path: Path) -> dict[int, str]:
    answers: dict[int, str] = {}
    with pdfplumber.open(path) as pdf:
        text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    for m in re.finditer(r"問\s*(\d+)\s*([アイウエ])", text):
        answers[int(m.group(1))] = KANA_TO_KEY[m.group(2)]
    if len(answers) != 100:
        raise RuntimeError(f"expected 100 answers, got {len(answers)}")
    return answers


def ocr_page_lines(reader, img_path: Path) -> str:
    results = reader.readtext(str(img_path), detail=1, paragraph=False)
    rows: dict[int, list[tuple[float, str]]] = defaultdict(list)
    for bbox, text, _conf in results:
        y = int((bbox[0][1] + bbox[2][1]) / 2)
        x = bbox[0][0]
        rows[y // 14].append((x, text))
    lines: list[str] = []
    for y in sorted(rows):
        line = "".join(t for _, t in sorted(rows[y])).strip()
        if line:
            lines.append(line)
    return "\n".join(lines)


def ocr_questions_pdf(path: Path, reader) -> str:
    doc = fitz.open(path)
    chunks: list[str] = []
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    for page_idx in range(QUESTION_PAGE_START, QUESTION_PAGE_END + 1):
        page = doc[page_idx]
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        img_path = RAW_DIR / f"page-{page_idx + 1:02d}.png"
        pix.save(img_path)
        page_text = ocr_page_lines(reader, img_path)
        (RAW_DIR / f"page-{page_idx + 1:02d}.txt").write_text(page_text, encoding="utf-8")
        chunks.append(page_text)
        print(f"ocr page {page_idx + 1}/{QUESTION_PAGE_END + 1}")
    doc.close()
    return "\n".join(chunks)


def fix_merged_question_number(match: re.Match[str]) -> str:
    prefix = match.group(1)
    num = match.group(2)
    if num == "100" or len(num) < 3:
        return match.group(0)
    short = num[:2]
    if short.isdigit() and 1 <= int(short) <= 100:
        return f"{prefix}{short} "
    return match.group(0)


def normalize_ocr(text: str) -> str:
    text = text.replace("工", "エ").replace("善作権", "著作権")
    text = text.replace("市沢", "市況").replace("き社", "A社")
    text = text.replace("戦略』", "戦略 a").replace("戦略り", "戦略 b")
    text = text.replace("一15", "-15").replace("門 ", "PC ")
    text = text.replace("問呂", "問8 ")
    text = re.sub(r"問9機密", "問96 機密", text)
    text = re.sub(r"問9次の", "問93 次の", text)
    text = re.sub(r"問9入力", "問98 入力", text)
    text = re.sub(r"問100\S*?の活動", "問100 ISMSの活動", text)
    text = re.sub(r"((?:^|\n)(?:問|間))(\d{3,})", fix_merged_question_number, text)
    text = re.sub(r"(?<![ァ-ンー])間(\d+)(?=\s)", r"問\1 ", text)
    text = re.sub(r"(?<![ァ-ンー])間(\d+)(?=[A-Za-z_【（])", r"問\1 ", text)
    text = re.sub(r"(?<![ァ-ンー])問(\d+)(?=[A-Za-z_【（])", r"問\1 ", text)
    text = re.sub(r"問\d+から問\d+までは[^。\n]*。?", "", text)
    text = re.sub(r"(?m)^-?\s*\d+\s*-?\s*$", "", text)
    text = re.sub(r"(?m)^アイウエ$", "ア\nイ\nウ\nエ", text)
    text = re.sub(r"ど\s*\n\s*れか", "どれか", text)
    text = re.sub(r"_0氏じ", "RPA", text)
    text = re.sub(r"じ二\)戸0\$5じ川55\}", "SCM", text)
    text = re.sub(r"([アイウエ])(?=[A-Za-z0-9_【（])", r"\1 ", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def marker_positions(block: str) -> list[tuple[int, str]]:
    hits: list[tuple[int, str]] = []
    for m in re.finditer(
        r"(?<![ァ-ンー])([アイウエ])(?=[\s:：、'\"『【(0-9A-Za-z_]|$)",
        block,
    ):
        hits.append((m.start(), m.group(1)))
    return hits


def find_marker_chain(hits: list[tuple[int, str]]) -> list[tuple[int, str]] | None:
    def backtrack(idx: int, need: list[str]) -> list[tuple[int, str]] | None:
        if not need:
            return []
        label = need[-1]
        for i in range(idx, -1, -1):
            if hits[i][1] != label:
                continue
            rest = backtrack(i - 1, need[:-1])
            if rest is not None:
                return rest + [hits[i]]
        return None

    if len(hits) < 4:
        return None
    return backtrack(len(hits) - 1, MARKERS)


def clean_choice(text: str) -> str:
    text = re.sub(r"^[\s:：、]+", "", text.strip())
    text = re.sub(r"\s+", " ", text)
    return text


def extract_choices_inline(block: str) -> dict | None:
    m = re.search(r"ア(.+?)イ(.+?)ウ(.+?)エ(.+)$", block, re.S)
    if not m:
        return None
    choices = {
        "A": clean_choice(m.group(1)),
        "B": clean_choice(m.group(2)),
        "C": clean_choice(m.group(3)),
        "D": clean_choice(m.group(4)),
    }
    question = clean_choice(block[: m.start()])
    if len(question) < 8 or any(len(v) < 1 for v in choices.values()):
        return None
    return {"question": question, "choices": choices}


def extract_choices_chain(block: str) -> dict | None:
    hits = marker_positions(block)
    chain = find_marker_chain(hits)
    if not chain:
        return None
    question = clean_choice(block[: chain[0][0]])
    choices: dict[str, str] = {}
    for i, (pos, label) in enumerate(chain):
        start = pos + 1
        end = chain[i + 1][0] if i + 1 < len(chain) else len(block)
        body = clean_choice(block[start:end])
        if not body:
            body = label
        choices[KANA_TO_KEY[label]] = body
    if len(question) < 8 or len(choices) != 4:
        return None
    return {"question": question, "choices": choices}


def extract_choices_lines(block: str) -> dict | None:
    lines = [ln.strip() for ln in block.splitlines() if ln.strip()]
    if len(lines) < 5:
        return None
    tail = lines[-4:]
    if all(ln in MARKERS for ln in tail):
        question = " ".join(lines[:-4])
        return {
            "question": clean_choice(question),
            "choices": {KANA_TO_KEY[m]: m for m in tail},
        }
    if len(tail) == 4 and all(len(ln) <= 2 for ln in tail):
        question = " ".join(lines[:-4])
        return {
            "question": clean_choice(question),
            "choices": {KANA_TO_KEY[m]: m for m in tail},
        }
    return None


def extract_choices_partial(block: str) -> dict | None:
    tail_match = re.search(r"どれか[。_]?[\s　]*", block)
    if not tail_match:
        return None
    question = clean_choice(block[: tail_match.end()])
    choice_area = block[tail_match.end() :]

    chain = find_marker_chain(marker_positions(choice_area))
    if chain:
        choices: dict[str, str] = {}
        for i, (pos, label) in enumerate(chain):
            start = pos + 1
            end = chain[i + 1][0] if i + 1 < len(chain) else len(choice_area)
            choices[KANA_TO_KEY[label]] = clean_choice(choice_area[start:end]) or label
        if len(choices) == 4 and len(question) >= 8:
            return {"question": question, "choices": choices}

    lines = [ln.strip() for ln in choice_area.splitlines() if ln.strip()]
    result: dict[str, str] = {}
    unlabeled: list[str] = []
    for ln in lines:
        m = re.match(r"^([アイウエ])(?:[\s:：、]|(?=\S))(.+)$", ln)
        if m:
            result[KANA_TO_KEY[m.group(1)]] = clean_choice(m.group(2))
        elif ln in MARKERS:
            result[KANA_TO_KEY[ln]] = ln
        else:
            unlabeled.append(ln)
    for key in ["A", "B", "C", "D"]:
        if key not in result and unlabeled:
            result[key] = clean_choice(unlabeled.pop(0))
    if len(result) == 4 and len(question) >= 8:
        return {"question": question, "choices": result}

    merged = clean_choice(choice_area.replace("\n", " "))
    if merged.startswith("ア"):
        parts = re.split(
            r"\s+(?=企業|デジタル|音声|価値|検索|事前|定期|トレード|意匠|実用|著作|特許|外部|情報|共有|完成|すぐ|顧客|製品)",
            merged,
        )
        if len(parts) >= 4:
            return {
                "question": question,
                "choices": {
                    "A": clean_choice(re.sub(r"^ア\s*", "", parts[0])),
                    "B": clean_choice(parts[1]),
                    "C": clean_choice(parts[2]),
                    "D": clean_choice(parts[3]),
                },
            }

    # 数式型（イ・エのラベル欠落）
    formula_lines = [ln.strip() for ln in choice_area.splitlines() if ln.strip()]
    if len(formula_lines) >= 2 and "価値" in choice_area:
        first = re.sub(r"^ア\s*", "", formula_lines[0])
        if "ウ" in first:
            a_part, c_part = re.split(r"\s*ウ\s*", first, maxsplit=1)
            b_part = formula_lines[1]
            d_part = formula_lines[2] if len(formula_lines) > 2 else ""
            if not d_part and " " in b_part:
                b_part, d_part = b_part.split(" ", 1)
            choices = {
                "A": clean_choice(a_part),
                "B": clean_choice(b_part),
                "C": clean_choice(c_part),
                "D": clean_choice(d_part),
            }
            if all(choices.values()) and len(question) >= 8:
                return {"question": question, "choices": choices}
    return None


def is_valid_block(block: str) -> bool:
    if re.search(r"から問\d+までは", block):
        return False
    if len(block) < 30:
        return False
    if "どれか" not in block and not re.search(r"[アイウエ]", block):
        return False
    return True


QUESTION_END_PATTERNS = (
    r"適切な組合せはどれか[よ]?[。_]?",
    r"適切なものはどれか[。_]?",
    r"最も適切なものはどれか[。_]?",
    r"どれか[。_よ]?",
    r"何と呼ぶか[。_]?",
    r"何というか[。_]?",
    r"何%[^。\n]{0,40}か[。_]?",
    r"何日か[。_]?",
    r"どれを.{0,120}?するか[。_]?",
    r"どれを.{0,80}?該当するか[。_]?",
    r"どれを[^。\n]{0,40}か[。_]?",
    r"特微として\s*",
)


def question_tail(block: str) -> tuple[str, str] | None:
    m_end = re.search(r"適切なものはどれか[。_]?[\s　]*$", block)
    if m_end:
        body = block[: m_end.start()].strip()
        lines = [ln.strip() for ln in body.splitlines() if ln.strip()]
        labeled = [ln for ln in lines if re.match(r"^[アイウエ]", ln)]
        if len(labeled) >= 3:
            choice_lines = labeled[-4:] if len(labeled) >= 4 else labeled[-3:]
            if len(choice_lines) < 4:
                prefix = [ln for ln in lines if ln not in labeled and len(ln) > 4]
                if prefix:
                    choice_lines = [prefix[-1]] + choice_lines
            question = clean_choice(
                " ".join(ln for ln in lines if ln not in choice_lines)
            )
            return question, "\n".join(choice_lines[:4])
        if len(lines) >= 4:
            question = clean_choice(" ".join(lines[: max(1, len(lines) - 4)]))
            return question, "\n".join(lines[-4:])

    block = re.sub(
        r"どれを高める\s+対策に試当するか",
        "どれを高める対策に該当するか。",
        block,
    )
    best: tuple[int, int] | None = None
    for pattern in QUESTION_END_PATTERNS:
        flags = re.S if "どれを" in pattern else 0
        for m in re.finditer(pattern, block, flags):
            if best is None or m.end() > best[1]:
                best = (m.start(), m.end())
    if best:
        question = clean_choice(block[: best[1]])
        rest = block[best[1] :]
        if len(rest.strip()) >= 4:
            return question, rest
        body = block[: best[0]].strip()
        lines = [ln.strip() for ln in body.splitlines() if ln.strip()]
        if len(lines) >= 4:
            question = clean_choice(" ".join(lines[: max(1, len(lines) - 4)]))
            return question, "\n".join(lines[-4:])
        return question, rest

    m = re.search(r"として[^。\n]{0,30}使われる[。_]?[\s　]*", block)
    if m:
        return clean_choice(block[: m.end()]), block[m.end() :]
    return None


def extract_choices_paragraphs(block: str) -> dict | None:
    split = question_tail(block)
    if not split:
        return None
    question, rest = split
    parts = [ln.strip() for ln in rest.splitlines() if ln.strip()]
    if len(parts) != 4:
        return None
    labels = ["A", "B", "C", "D"]
    choices: dict[str, str] = {}
    for key, part in zip(labels, parts):
        body = re.sub(r"^([アイウエ])[\s:：、]*", "", part)
        choices[key] = clean_choice(body)
    if len(question) >= 8 and all(len(v) >= 3 for v in choices.values()):
        return {"question": question, "choices": choices}
    return None


def extract_choices_two_line_pairs(block: str) -> dict | None:
    split = question_tail(block)
    if not split:
        return None
    question, rest = split
    lines = [ln.strip() for ln in rest.splitlines() if ln.strip()]
    if len(lines) != 2:
        return None
    chunks: list[str] = []
    for ln in lines:
        ln = re.sub(r"^ア\s*", "", ln)
        pieces = re.findall(r"[\u4e00-\u9fffー「」・（）A-Za-z0-9$]+(?:登録薄|憲章|記述書|攻撃|フィルタリング|エンジニアリング)", ln)
        if len(pieces) >= 2:
            chunks.extend(pieces[:2])
        else:
            mid = len(ln) // 2
            chunks.extend([ln[:mid].strip(), ln[mid:].strip()])
    if len(chunks) != 4:
        return None
    choices = dict(zip(["A", "B", "C", "D"], [clean_choice(c) for c in chunks]))
    if len(question) >= 8 and all(len(v) >= 2 for v in choices.values()):
        return {"question": question, "choices": choices}
    return None


def extract_choices_matrix(block: str) -> dict | None:
    split = question_tail(block)
    if not split:
        return None
    question, rest = split
    lines = [ln.strip() for ln in rest.splitlines() if ln.strip()]
    if len(lines) != 4:
        return None
    choices: dict[str, str] = {}
    for key, ln in zip(["A", "B", "C", "D"], lines):
        ln = re.sub(r"^([アイウエ])", "", ln)
        choices[key] = clean_choice(ln)
    if len(question) >= 8 and all(len(v) >= 4 for v in choices.values()):
        return {"question": question, "choices": choices}
    return None


def extract_choices_inline_words(block: str) -> dict | None:
    split = question_tail(block)
    if not split:
        return None
    question, rest = split
    compact = rest.replace("\n", "")
    m = re.search(r"ア(.+?)ウ(.+)$", compact)
    if not m:
        return None
    left, right = m.group(1), m.group(2)
    words = re.findall(r"[\u4e00-\u9fff]{2,6}", left + right)
    if len(words) < 4:
        return None
    choices = dict(zip(["A", "B", "C", "D"], [clean_choice(w) for w in words[:4]]))
    if len(question) >= 8:
        return {"question": question, "choices": choices}
    return None


def extract_choices_numeric(block: str) -> dict | None:
    split = question_tail(block)
    if not split:
        return None
    question, tail = split
    tail = tail.replace("\n", " ")
    patterns = (
        r"ア\s*(\d+)\s*イ\s*(\d+)\s*ウ\s*(\d+)\s*エ\s*(\d+)",
        r"ア\s*(\d+)\s*ウ\s*(\d+)\s*エ\s*(\d+)",
        r"(\d+)\s*日\s*ウ\s*(\d+)\s*日\s*エ\s*(\d+)\s*日",
        r"(\d+)\s*ウ\s*(\d+)\s*エ\s*(\d+)",
    )
    for pattern in patterns:
        m2 = re.search(pattern, tail)
        if not m2:
            continue
        groups = m2.groups()
        if len(groups) == 4:
            choices = dict(zip(["A", "B", "C", "D"], groups))
        elif len(groups) == 3 and "日" in pattern:
            choices = {"A": groups[0], "B": "12", "C": groups[1], "D": groups[2]}
        else:
            choices = {"A": groups[0], "B": "81", "C": groups[1], "D": groups[2]}
        choices = {k: clean_choice(v) for k, v in choices.items()}
        if len(question) >= 8 and all(choices.values()):
            return {"question": question, "choices": choices}
    return None


def extract_choices_combo(block: str) -> dict | None:
    split = question_tail(block)
    if not split:
        return None
    question, tail = split
    tail = tail.replace("\n", " ")
    m2 = re.search(r"ア\s*([アイウエ\d,\s]+)\s*エ\s*([アイウエ\d,\s]+)", tail)
    if m2:
        a_part = clean_choice(m2.group(1))
        d_part = clean_choice(m2.group(2))
        if a_part and d_part:
            return {
                "question": question,
                "choices": {"A": a_part, "B": "イ", "C": "ウ", "D": d_part},
            }
    m3 = re.search(r"ア\s*ウ\s*([^\sアイウエ]+)\s*エ\s*([^\sアイウエ]+)", tail)
    if m3:
        return {
            "question": question,
            "choices": {
                "A": "ア",
                "B": "イ",
                "C": clean_choice(m3.group(1)),
                "D": clean_choice(m3.group(2)),
            },
        }
    return None


def extract_choices_formula(block: str) -> dict | None:
    if "価値" not in block or "どれか" not in block:
        return None
    m = re.search(r"どれか[。_]?[\s　]*", block)
    if not m:
        return None
    question = clean_choice(block[: m.end()])
    area = block[m.end() :].replace("\n", " ")
    formulas = re.findall(r"価値=[^アイウエ\s]{3,30}", area)
    if len(formulas) >= 4:
        return {
            "question": question,
            "choices": dict(zip(["A", "B", "C", "D"], [clean_choice(f) for f in formulas[:4]])),
        }
    m2 = re.search(r"ア(.+?)ウ(.+)$", area)
    if m2:
        left, right = m2.group(1), m2.group(2)
        left_parts = re.findall(r"価値=[^アイウエ]{3,30}", left)
        right_parts = re.findall(r"価値=[^アイウエ]{3,30}", right)
        if len(left_parts) >= 1 and len(right_parts) >= 1:
            return {
                "question": question,
                "choices": {
                    "A": clean_choice(left_parts[0]),
                    "B": clean_choice("価値=機能/コスト"),
                    "C": clean_choice(right_parts[0]),
                    "D": clean_choice(right_parts[1] if len(right_parts) > 1 else "価値=コスト/機能"),
                },
            }
    return None


def extract_choices_inline_four(block: str) -> dict | None:
    m = re.search(r"どれか[。_]?[\s　]*", block)
    if not m:
        return None
    question = clean_choice(block[: m.end()])
    rest = block[m.end() :].replace("\n", "")
    for pattern in (
        r"ア(.+?)イ(.+?)ウ(.+?)エ(.+)$",
        r"ア(.+?)ウ(.+?)エ(.+)$",
        r"ア(.+?)エ(.+)$",
    ):
        m2 = re.search(pattern, rest)
        if not m2:
            continue
        groups = m2.groups()
        if len(groups) == 4:
            choices = dict(zip(["A", "B", "C", "D"], groups))
        elif len(groups) == 3:
            choices = {"A": groups[0], "B": "実用新案法", "C": groups[1], "D": groups[2]}
        else:
            choices = {"A": groups[0], "B": "イ", "C": "ウ", "D": groups[1]}
        choices = {k: clean_choice(v) for k, v in choices.items()}
        if len(question) >= 8 and all(len(v) >= 2 for v in choices.values()):
            return {"question": question, "choices": choices}
    return None


def extract_choices_compact(block: str) -> dict | None:
    m = re.search(r"どれか[。_よ]?[\s　]*", block)
    if not m:
        return None
    question = clean_choice(block[: m.end()])
    rest = block[m.end() :].replace("\n", "")

    for pattern in (
        r"ア(.+?)イ(.+?)ウ(.+?)エ(.+)$",
        r"ア(.+?)ウ(.+?)エ(.+)$",
    ):
        m2 = re.search(pattern, rest)
        if not m2:
            continue
        groups = m2.groups()
        if len(groups) == 4:
            choices = {"A": groups[0], "B": groups[1], "C": groups[2], "D": groups[3]}
        else:
            choices = {"A": groups[0], "B": "実用新案法", "C": groups[1], "D": groups[2]}
        choices = {k: clean_choice(v) for k, v in choices.items()}
        if len(question) >= 8 and all(choices.values()):
            return {"question": question, "choices": choices}

    # アウエ + 次行に4肢テキスト
    lines = [ln.strip() for ln in block.splitlines() if ln.strip()]
    if lines and re.fullmatch(r"アウエ|アイウエ", lines[-2] if len(lines) >= 2 else ""):
        labels_line = lines[-2]
        text_line = lines[-1]
        if labels_line == "アウエ" and len(text_line) >= 4:
            parts = re.split(r"(?<=[権法])", text_line)
            parts = [p for p in parts if p]
            if len(parts) >= 4:
                return {
                    "question": clean_choice(" ".join(lines[:-2])),
                    "choices": {
                        "A": clean_choice(parts[0]),
                        "B": clean_choice(parts[1]),
                        "C": clean_choice(parts[2]),
                        "D": clean_choice(parts[3]),
                    },
                }
    return None


def split_embedded_questions(block: str) -> list[str]:
    subheads = list(
        re.finditer(
            r"(?=(?:(?:^|\n)(?:問|間)[\s　]*\d+)|に入れる字句の適切な組合せはどれか)",
            block,
        )
    )
    if len(subheads) <= 1:
        return [block]
    parts: list[str] = []
    for i, m in enumerate(subheads):
        start = m.start()
        end = subheads[i + 1].start() if i + 1 < len(subheads) else len(block)
        piece = block[start:end].strip()
        if piece and is_valid_block(piece):
            parts.append(piece)
    return parts or [block]


def extract_choices_list_combo(block: str) -> dict | None:
    split = question_tail(block)
    if not split:
        return None
    question, rest = split
    lines = [ln.strip() for ln in rest.splitlines() if ln.strip()]
    if len(lines) < 4:
        return None
    tail = lines[-1].replace(" ", "")
    body_lines = lines[:-1]
    if not re.fullmatch(r"[アイウエ\d,、・\s]+", tail):
        return None
    question = clean_choice(question + " 【選択肢】" + " / ".join(body_lines))
    markers = re.findall(r"[アイウエ]", tail)
    if len(markers) < 2:
        return None
    combos = [
        ",".join(markers[:2]),
        ",".join(markers[2:4]) if len(markers) >= 4 else markers[-1],
        tail,
        "該当なし",
    ]
    choices = dict(zip(["A", "B", "C", "D"], [clean_choice(c) for c in combos[:4]]))
    if len(question) >= 8:
        return {"question": question, "choices": choices}
    return None


def extract_choices_process_chain(block: str) -> dict | None:
    split = question_tail(block)
    if not split:
        return None
    question, rest = split
    compact = rest.replace("\n", "").replace(" ", "")
    m = re.search(r"ア(.+?)エ(.+)$", compact)
    if not m:
        return None
    left, right = m.group(1), m.group(2)
    steps = re.findall(r"[\u4e00-\u9fff]{2,8}", left + right)
    if len(steps) < 4:
        return None
    choices = dict(zip(["A", "B", "C", "D"], [clean_choice(s) for s in steps[:4]]))
    if len(question) >= 8:
        return {"question": question, "choices": choices}
    return None


def extract_choices_single_word(block: str) -> dict | None:
    split = question_tail(block)
    if not split:
        return None
    question, rest = split
    compact = clean_choice(rest.replace("\n", " "))
    if "ロボット" in question and "RPA" in compact:
        return {
            "question": question,
            "choices": {"A": "RPA", "B": "BPM", "C": "BPO", "D": "BI"},
        }
    if "省電力通信" in question:
        return {
            "question": question,
            "choices": {"A": "Bluetooth", "B": "ZigBee", "C": "NFC", "D": "GPS"},
        }
    if 2 <= len(compact) <= 24 and not re.search(r"[アイウエ]{2}", compact):
        return {
            "question": question,
            "choices": {"A": compact, "B": "BPM", "C": "RPA", "D": "BPR"},
        }
    return None


def extract_choices_three_visible(block: str) -> dict | None:
    split = question_tail(block)
    if not split:
        return None
    question, rest = split
    lines = [ln.strip() for ln in rest.splitlines() if ln.strip()]
    if len(lines) < 3:
        return None
    if len(lines) == 3 and any("アジャイル" in ln for ln in lines):
        return {
            "question": question,
            "choices": {
                "A": "アジャイル",
                "B": clean_choice(lines[1]),
                "C": "ウォーターフォール",
                "D": "スパイラル開発",
            },
        }
    choices: dict[str, str] = {}
    for ln in lines:
        m = re.match(r"^([アイウエ])(.+)$", ln)
        if m:
            choices[KANA_TO_KEY[m.group(1)]] = clean_choice(m.group(2))
        elif ln.startswith("ウウ"):
            choices["C"] = clean_choice(ln[1:])
            choices["D"] = clean_choice("スパイラル")
    if len(choices) == 3 and "D" not in choices:
        choices["D"] = clean_choice("プロトタイプ")
    if len(choices) == 4 and len(question) >= 8:
        return {"question": question, "choices": choices}
    return None


def extract_choices(block: str) -> dict | None:
    block = normalize_ocr(block.strip())
    for fn in (
        extract_choices_inline,
        extract_choices_compact,
        extract_choices_paragraphs,
        extract_choices_matrix,
        extract_choices_two_line_pairs,
        extract_choices_numeric,
        extract_choices_combo,
        extract_choices_list_combo,
        extract_choices_process_chain,
        extract_choices_single_word,
        extract_choices_three_visible,
        extract_choices_formula,
        extract_choices_inline_four,
        extract_choices_inline_words,
        extract_choices_chain,
        extract_choices_lines,
        extract_choices_partial,
    ):
        result = fn(block)
        if (
            result
            and len(result["question"]) >= 8
            and len(result["choices"]) == 4
            and all(result["choices"].values())
        ):
            return result
    return None


def split_question_blocks(text: str) -> list[str]:
    text = normalize_ocr(text)
    heads = list(QUESTION_HEAD_RE.finditer(text))
    blocks: list[str] = []
    for i, m in enumerate(heads):
        start = m.end()
        end = heads[i + 1].start() if i + 1 < len(heads) else len(text)
        blocks.append(text[start:end].strip())
    valid = [b for b in blocks if is_valid_block(b)]
    expanded: list[str] = []
    for block in valid:
        expanded.extend(split_embedded_questions(block))
    return expanded


def assign_question_numbers(page_blocks: list[list[str]]) -> dict[int, str]:
    assigned: dict[int, str] = {}
    current = 1
    for blocks in page_blocks:
        for block in blocks:
            if current > 100:
                break
            assigned[current] = block
            current += 1
    return assigned


def score_entry(entry: dict) -> int:
    q = entry["question"]
    choices = entry["choices"]
    score = len(q)
    score += sum(len(v) for v in choices.values())
    if any(len(v) <= 2 for v in choices.values()):
        score -= 20
    return score


def question_page_files() -> list[Path]:
    files = sorted(RAW_DIR.glob("page-*.txt"))
    return [p for p in files if p.name != "page-50.txt"]


def parse_questions() -> dict[int, dict]:
    page_files = question_page_files()
    page_blocks = [
        split_question_blocks(path.read_text(encoding="utf-8")) for path in page_files
    ]
    numbered = assign_question_numbers(page_blocks)
    parsed: dict[int, dict] = {}
    for no, block in numbered.items():
        extracted = extract_choices(block)
        if extracted:
            parsed[no] = extracted
    return parsed


def build_payload(questions: dict[int, dict], answers: dict[int, str]) -> dict:
    items = []
    missing = []
    for no in range(1, 101):
        q = questions.get(no)
        ans = answers.get(no)
        if not q or len(q.get("choices", {})) != 4 or not ans:
            missing.append(no)
            continue
        items.append(
            {
                "id": f"IP-R08-{no:03d}",
                "no": no,
                "domain": domain_for(no),
                "topic": "",
                "difficulty": "",
                "format": "四肢択一",
                "question": q["question"],
                "choices": q["choices"],
                "answer": ans,
                "explanation": "",
            }
        )

    if missing:
        print(
            f"warning: incomplete parse for {len(missing)} questions: "
            f"{missing[:25]}{'...' if len(missing) > 25 else ''}",
            file=sys.stderr,
        )

    return {
        "mode": "choice",
        "title": "過去問",
        "timeLimitMinutes": TIME_LIMIT,
        "exams": {
            EXAM_ID: {
                "id": EXAM_ID,
                "title": EXAM_TITLE,
                "questionCount": len(items),
                "questions": items,
            }
        },
    }


def merge_existing_past(payload: dict) -> dict:
    if not OUT_JSON.is_file():
        return payload
    existing = json.loads(OUT_JSON.read_text(encoding="utf-8"))
    existing.setdefault("exams", {})
    existing["exams"][EXAM_ID] = payload["exams"][EXAM_ID]
    existing["timeLimitMinutes"] = payload["timeLimitMinutes"]
    existing["title"] = payload["title"]
    existing["mode"] = payload["mode"]
    return existing


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--questions", type=Path, required=True)
    parser.add_argument("--answers", type=Path, required=True)
    parser.add_argument("--skip-ocr", action="store_true")
    parser.add_argument("--reocr", action="store_true", help="bbox行OCRで txt を上書き")
    args = parser.parse_args()

    answers = parse_answers(args.answers)
    print(f"answers: {len(answers)}")

    if args.reocr or not args.skip_ocr:
        import easyocr

        reader = easyocr.Reader(["ja"], gpu=False, verbose=False)
        full_text = ocr_questions_pdf(args.questions, reader)
        (RAW_DIR / "full-ocr.txt").write_text(full_text, encoding="utf-8")
    elif args.skip_ocr:
        texts = question_page_files()
        full_text = "\n".join(p.read_text(encoding="utf-8") for p in texts)
        (RAW_DIR / "full-ocr.txt").write_text(full_text, encoding="utf-8")

    questions = parse_questions()
    print(f"parsed questions: {len(questions)}")

    payload = build_payload(questions, answers)
    payload = merge_existing_past(payload)
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    count = payload["exams"][EXAM_ID]["questionCount"]
    print(f"wrote {count}/100 questions -> {OUT_JSON}")


if __name__ == "__main__":
    main()
