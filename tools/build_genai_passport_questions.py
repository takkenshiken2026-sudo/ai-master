#!/usr/bin/env python3
"""生成AIパスポート Excel から assets/data/genai-passport/*.json を生成する。"""

from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "genai-passport"
OUT_DIR = ROOT / "assets" / "data" / "genai-passport"

DOWNLOADS = Path.home() / "Downloads"
XLSX = {
    "drill": DOWNLOADS / "【最終盤】生成AIパスポート_一問一答.xlsx",
    "practice": DOWNLOADS / "【最終盤】生成AIパスポート_実践演習.xlsx",
    "mock": DOWNLOADS / "【最終盤】生成AIパスポート_有料模試.xlsx",
}

MOCK_SHEETS = {
    "sample": "無料サンプル3問",
    "mock_01": "第1回",
    "mock_02": "第2回",
    "mock_03": "第3回",
}

MOCK_TITLES = {
    "sample": "サンプル（3問）",
    "mock_01": "模擬試験 第1回",
    "mock_02": "模擬試験 第2回",
    "mock_03": "模擬試験 第3回",
}

CHOICE_NUM = {"1": "A", "2": "B", "3": "C", "4": "D"}


def norm_header(cell: str) -> str:
    return (cell or "").replace("\ufeff", "").strip()


def cell_str(val) -> str:
    if val is None:
        return ""
    if isinstance(val, float) and val.is_integer():
        return str(int(val))
    return str(val).strip()


def load_sheet(path: Path, sheet_name: str) -> tuple[list[str], list[tuple]]:
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb[sheet_name]
    rows = list(ws.iter_rows(values_only=True))
    wb.close()
    if not rows:
        return [], []
    header = [norm_header(h) for h in rows[0]]
    body = [tuple(r) for r in rows[1:] if any(c is not None and str(c).strip() for c in r)]
    return header, body


def index_map(header: list[str]) -> dict[str, int]:
    return {h: i for i, h in enumerate(header)}


def pick(row: tuple, col: dict[str, int], *names: str, default: str = "") -> str:
    for name in names:
        if name in col:
            return cell_str(row[col[name]])
    return default


def normalize_choice_answer(raw: str) -> str:
    val = cell_str(raw).upper()
    if val in CHOICE_NUM:
        return CHOICE_NUM[val]
    if val in {"A", "B", "C", "D"}:
        return val
    return val


def question_no_from_id(qid: str, fallback: int) -> int:
    m = re.search(r"(\d+)$", qid or "")
    return int(m.group(1)) if m else fallback


def build_drill(path: Path) -> dict:
    header, rows = load_sheet(path, "問題バンク")
    col = index_map(header)
    questions = []
    for i, row in enumerate(rows, start=1):
        qid = pick(row, col, "id")
        questions.append(
            {
                "id": qid,
                "no": question_no_from_id(qid, i),
                "domain": pick(row, col, "章"),
                "topic": pick(row, col, "中項目"),
                "difficulty": pick(row, col, "難易度"),
                "statement": pick(row, col, "問題文"),
                "answer": pick(row, col, "正誤"),
                "explanation": pick(row, col, "解説"),
            }
        )
    return {"mode": "drill", "title": "一問一答", "questions": questions}


def build_practice(path: Path) -> dict:
    header, rows = load_sheet(path, "問題バンク")
    col = index_map(header)
    questions = []
    for i, row in enumerate(rows, start=1):
        qid = pick(row, col, "id")
        questions.append(
            {
                "id": qid,
                "no": question_no_from_id(qid, i),
                "domain": pick(row, col, "章"),
                "topic": pick(row, col, "中項目"),
                "difficulty": pick(row, col, "難易度"),
                "format": pick(row, col, "問題種別"),
                "question": pick(row, col, "問題文"),
                "choices": {
                    "A": pick(row, col, "選択肢1"),
                    "B": pick(row, col, "選択肢2"),
                    "C": pick(row, col, "選択肢3"),
                    "D": pick(row, col, "選択肢4"),
                },
                "answer": normalize_choice_answer(pick(row, col, "正解")),
                "explanation": pick(row, col, "解説"),
            }
        )
    return {"mode": "choice", "title": "実践演習", "questions": questions}


def build_mock_row(header: list[str], row: tuple, no: int) -> dict:
    col = index_map(header)
    qid = pick(row, col, "ID", "id")
    no_val = pick(row, col, "問番号")
    return {
        "id": qid,
        "no": int(float(no_val)) if no_val else no,
        "domain": pick(row, col, "章"),
        "topic": pick(row, col, "中項目"),
        "difficulty": pick(row, col, "難易度"),
        "format": pick(row, col, "問題タイプ", "問題種別"),
        "question": pick(row, col, "問題文"),
        "choices": {
            "A": pick(row, col, "選択肢A", "選択肢1"),
            "B": pick(row, col, "選択肢B", "選択肢2"),
            "C": pick(row, col, "選択肢C", "選択肢3"),
            "D": pick(row, col, "選択肢D", "選択肢4"),
        },
        "answer": normalize_choice_answer(pick(row, col, "正答", "正解")),
        "explanation": pick(row, col, "解説"),
    }


def build_mock(path: Path) -> dict:
    payload = {
        "mode": "choice",
        "title": "模擬試験",
        "timeLimitMinutes": 60,
        "exams": {},
    }
    for exam_id, sheet_name in MOCK_SHEETS.items():
        header, rows = load_sheet(path, sheet_name)
        questions = [build_mock_row(header, row, i) for i, row in enumerate(rows, start=1)]
        payload["exams"][exam_id] = {
            "id": exam_id,
            "title": MOCK_TITLES[exam_id],
            "questionCount": len(questions),
            "questions": questions,
        }
    return payload


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def copy_sources(paths: dict[str, Path]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    for src in paths.values():
        if not src.exists():
            raise FileNotFoundError(src)
        shutil.copy2(src, DATA_DIR / src.name)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--drill", type=Path, default=XLSX["drill"])
    parser.add_argument("--practice", type=Path, default=XLSX["practice"])
    parser.add_argument("--mock", type=Path, default=XLSX["mock"])
    parser.add_argument("--skip-copy", action="store_true")
    args = parser.parse_args()

    paths = {"drill": args.drill, "practice": args.practice, "mock": args.mock}
    if not args.skip_copy:
        copy_sources(paths)

    drill = build_drill(paths["drill"])
    practice = build_practice(paths["practice"])
    mock = build_mock(paths["mock"])

    write_json(OUT_DIR / "drill.json", drill)
    write_json(OUT_DIR / "practice.json", practice)
    write_json(OUT_DIR / "mock.json", mock)

    print(f"drill:    {len(drill['questions'])} questions -> {OUT_DIR / 'drill.json'}")
    print(f"practice: {len(practice['questions'])} questions -> {OUT_DIR / 'practice.json'}")
    for eid, exam in mock["exams"].items():
        print(f"mock {eid}: {exam['questionCount']} questions")
    print(f"mock -> {OUT_DIR / 'mock.json'}")


if __name__ == "__main__":
    main()
