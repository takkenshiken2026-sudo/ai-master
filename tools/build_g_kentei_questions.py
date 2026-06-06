#!/usr/bin/env python3
"""G検定 Excel から assets/data/g-kentei/*.json を生成する。"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "g-kentei"
OUT_DIR = ROOT / "assets" / "data" / "g-kentei"

DOWNLOADS = Path.home() / "Downloads"
XLSX = {
    "drill": DOWNLOADS / "【最終盤】G検定_一問一答.xlsx",
    "practice": DOWNLOADS / "【最終盤】G検定_実践演習.xlsx",
    "mock": DOWNLOADS / "【最終盤】G検定_有料模試.xlsx",
}

MOCK_TITLES = {
    "sample": "サンプル（3問）",
    "mock_01": "模擬試験 第1回",
    "mock_02": "模擬試験 第2回",
    "mock_03": "模擬試験 第3回",
}


def norm_header(cell: str) -> str:
    return (cell or "").replace("\ufeff", "").strip()


def cell_str(val) -> str:
    if val is None:
        return ""
    return str(val).strip()


def load_rows(path: Path) -> tuple[list[str], list[tuple]]:
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    wb.close()
    if not rows:
        return [], []
    header = [norm_header(h) for h in rows[0]]
    body = [tuple(r) for r in rows[1:] if any(c is not None and str(c).strip() for c in r)]
    return header, body


def index_map(header: list[str]) -> dict[str, int]:
    return {h: i for i, h in enumerate(header)}


def build_drill(path: Path) -> dict:
    header, rows = load_rows(path)
    col = index_map(header)
    questions = []
    for row in rows:
        questions.append(
            {
                "id": cell_str(row[col["id"]]),
                "no": int(cell_str(row[col["question_no"]])),
                "domain": cell_str(row[col["domain"]]),
                "topic": cell_str(row[col["topic"]]),
                "difficulty": cell_str(row[col["difficulty"]]),
                "statement": cell_str(row[col["statement"]]),
                "answer": cell_str(row[col["answer"]]),
                "explanation": cell_str(row[col["explanation"]]),
            }
        )
    return {
        "mode": "drill",
        "title": "一問一答",
        "questions": questions,
    }


def build_choice_rows(header: list[str], rows: list[tuple]) -> list[dict]:
    col = index_map(header)
    questions = []
    for row in rows:
        questions.append(
            {
                "id": cell_str(row[col["id"]]) if "id" in col else cell_str(row[col["exam_id"]]),
                "no": cell_str(row[col["question_no"]]),
                "domain": cell_str(row[col["domain"]]),
                "topic": cell_str(row[col["topic"]]),
                "difficulty": cell_str(row[col["difficulty"]]),
                "format": cell_str(row[col["format"]]),
                "question": cell_str(row[col["question"]]),
                "choices": {
                    "A": cell_str(row[col["choice_a"]]),
                    "B": cell_str(row[col["choice_b"]]),
                    "C": cell_str(row[col["choice_c"]]),
                    "D": cell_str(row[col["choice_d"]]),
                },
                "answer": cell_str(row[col["answer"]]).upper(),
                "explanation": cell_str(row[col["explanation"]]),
            }
        )
    return questions


def build_practice(path: Path) -> dict:
    header, rows = load_rows(path)
    return {
        "mode": "choice",
        "title": "実践演習",
        "questions": build_choice_rows(header, rows),
    }


def build_mock(path: Path) -> dict:
    header, rows = load_rows(path)
    col = index_map(header)
    exams: dict[str, list] = {}
    for row in rows:
        exam_id = cell_str(row[col["exam_id"]])
        exams.setdefault(exam_id, []).append(row)

    payload = {
        "mode": "choice",
        "title": "模擬試験",
        "timeLimitMinutes": 120,
        "exams": {},
    }
    for exam_id, exam_rows in exams.items():
        questions = build_choice_rows(header, exam_rows)
        payload["exams"][exam_id] = {
            "id": exam_id,
            "title": MOCK_TITLES.get(exam_id, exam_id),
            "questionCount": len(questions),
            "questions": questions,
        }
    return payload


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def copy_sources(paths: dict[str, Path]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    for key, src in paths.items():
        if not src.exists():
            raise FileNotFoundError(src)
        dest = DATA_DIR / src.name
        shutil.copy2(src, dest)


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
