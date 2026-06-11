#!/usr/bin/env python3
"""用語辞典 ↔ 試験問題の逆引き JSON を生成・更新する。

  python3 tools/build_glossary_question_links.py              # 全用語（公開記事のみ）
  python3 tools/build_glossary_question_links.py --ids bert   # 特定用語のみ
  python3 tools/build_glossary_question_links.py --validate   # リンク検証のみ
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GLOSSARY_DIR = ROOT / "glossary"
GLOSSARY_TERMS_JSON = ROOT / "data" / "glossary-terms.json"
QUESTION_INDEX_JSON = ROOT / "data" / "question-index.json"
OUTPUT_JSON = ROOT / "data" / "glossary-question-links.json"

EXAM_QUESTION_JSON = {
    "g-kentei": {
        "drill": ROOT / "assets/data/g-kentei/drill.json",
        "practice": ROOT / "assets/data/g-kentei/practice.json",
    },
    "genai-passport": {
        "drill": ROOT / "assets/data/genai-passport/drill.json",
        "practice": ROOT / "assets/data/genai-passport/practice.json",
    },
}

LINK_RE = re.compile(
    r'href="\.\./\.\./exams/(?P<exam>g-kentei|genai-passport)/'
    r'(?P<mode>drill|practice)/q/(?P<slug>[a-z0-9-]+)/"'
)

MAX_QUESTIONS = 8


def load_terms() -> dict[str, dict]:
    data = json.loads(GLOSSARY_TERMS_JSON.read_text(encoding="utf-8"))
    terms: dict[str, dict] = {}
    for t in data.get("terms") or []:
        tid = t.get("id")
        if not tid:
            continue
        if not (GLOSSARY_DIR / tid / "index.html").is_file():
            continue
        terms[tid] = t
    return terms


def load_question_index() -> dict[tuple[str, str, str], dict]:
    """(exam, mode, slug) -> metadata"""
    data = json.loads(QUESTION_INDEX_JSON.read_text(encoding="utf-8"))
    out: dict[tuple[str, str, str], dict] = {}
    for exam_id, exam_data in (data.get("exams") or {}).items():
        for mode_id, mode_data in exam_data.items():
            if not isinstance(mode_data, dict):
                continue
            for q in mode_data.get("questions") or []:
                slug = (q.get("slug") or "").lower()
                if slug:
                    out[(exam_id, mode_id, slug)] = q
    return out


def load_all_questions_text() -> list[dict]:
    rows: list[dict] = []
    for exam_id, modes in EXAM_QUESTION_JSON.items():
        for mode_id, path in modes.items():
            if not path.is_file():
                continue
            payload = json.loads(path.read_text(encoding="utf-8"))
            for q in payload.get("questions") or []:
                qid = q.get("id") or ""
                slug = qid.lower().replace("_", "-")
                text = " ".join(
                    filter(
                        None,
                        [
                            q.get("topic") or "",
                            q.get("statement") or q.get("question") or "",
                            q.get("explanation") or "",
                        ],
                    )
                )
                rows.append(
                    {
                        "exam": exam_id,
                        "mode": mode_id,
                        "id": qid,
                        "slug": slug,
                        "topic": q.get("topic") or "",
                        "text": text,
                    }
                )
    return rows


def parse_html_links(term_id: str) -> list[dict]:
    path = GLOSSARY_DIR / term_id / "index.html"
    html = path.read_text(encoding="utf-8")
    seen: set[tuple[str, str, str]] = set()
    links: list[dict] = []
    for m in LINK_RE.finditer(html):
        key = (m.group("exam"), m.group("mode"), m.group("slug"))
        if key in seen:
            continue
        seen.add(key)
        links.append(
            {
                "exam": key[0],
                "mode": key[1],
                "slug": key[2],
                "source": "html",
            }
        )
    return links


def auto_match_questions(name: str, yomi: str, questions: list[dict]) -> list[dict]:
    needles = [n for n in {name, yomi} if n and len(n) >= 2]
    if not needles:
        return []
    scored: list[tuple[int, dict]] = []
    for q in questions:
        text = q["text"]
        score = 0
        for needle in needles:
            if needle in text:
                score += len(needle)
        if score > 0:
            scored.append((score, q))
    scored.sort(key=lambda x: (-x[0], x[1]["exam"], x[1]["mode"], x[1]["id"]))
    out: list[dict] = []
    seen: set[tuple[str, str, str]] = set()
    for _, q in scored:
        key = (q["exam"], q["mode"], q["slug"])
        if key in seen:
            continue
        seen.add(key)
        out.append(
            {
                "exam": q["exam"],
                "mode": q["mode"],
                "slug": q["slug"],
                "source": "auto",
            }
        )
        if len(out) >= MAX_QUESTIONS:
            break
    return out


def enrich_question(entry: dict, index: dict[tuple[str, str, str], dict]) -> dict:
    key = (entry["exam"], entry["mode"], entry["slug"])
    meta = index.get(key, {})
    qid = meta.get("id") or entry["slug"].upper()
    topic = meta.get("topic") or ""
    label = f"{qid} · {topic}".strip(" ·") if topic else qid
    return {
        "exam": entry["exam"],
        "mode": entry["mode"],
        "slug": entry["slug"],
        "id": qid,
        "topic": topic,
        "label": label,
        "source": entry.get("source", "auto"),
        "url": f"/exams/{entry['exam']}/{entry['mode']}/q/{entry['slug']}/",
        "playerUrl": f"/exams/{entry['exam']}/{entry['mode']}/?q={entry['slug']}",
    }


def build_term_entry(term: dict, questions: list[dict], index: dict) -> dict:
    tid = term["id"]
    html_links = parse_html_links(tid)
    auto_links = auto_match_questions(term.get("name") or "", term.get("yomi") or "", questions)

    merged: list[dict] = []
    seen: set[tuple[str, str, str]] = set()
    for entry in html_links + auto_links:
        key = (entry["exam"], entry["mode"], entry["slug"])
        if key in seen:
            continue
        seen.add(key)
        merged.append(enrich_question(entry, index))
        if len(merged) >= MAX_QUESTIONS:
            break

    exams = set(term.get("exams") or [])
    exams.update(q["exam"] for q in merged)
    exams_sorted = sorted(exams)

    return {
        "termId": tid,
        "name": term.get("name") or tid,
        "exams": exams_sorted,
        "questions": merged,
    }


def build_payload(term_ids: list[str] | None = None) -> dict:
    terms = load_terms()
    if term_ids:
        terms = {k: v for k, v in terms.items() if k in term_ids}
    questions = load_all_questions_text()
    index = load_question_index()

    if OUTPUT_JSON.is_file() and term_ids:
        existing = json.loads(OUTPUT_JSON.read_text(encoding="utf-8"))
        payload_terms = existing.get("terms") or {}
    else:
        payload_terms = {}

    for tid, term in sorted(terms.items()):
        payload_terms[tid] = build_term_entry(term, questions, index)

    return {
        "version": 1,
        "maxQuestionsPerTerm": MAX_QUESTIONS,
        "terms": payload_terms,
    }


def validate_payload(payload: dict) -> list[str]:
    errors: list[str] = []
    index = load_question_index()
    for tid, entry in (payload.get("terms") or {}).items():
        html_path = GLOSSARY_DIR / tid / "index.html"
        if not html_path.is_file():
            errors.append(f"{tid}: glossary page missing")
        for q in entry.get("questions") or []:
            key = (q["exam"], q["mode"], q["slug"])
            if key not in index:
                errors.append(f"{tid}: unknown question {key}")
            page = ROOT / "exams" / q["exam"] / q["mode"] / "q" / q["slug"] / "index.html"
            if not page.is_file():
                errors.append(f"{tid}: missing page {page.relative_to(ROOT)}")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ids", help="comma-separated term ids")
    parser.add_argument("--validate", action="store_true")
    args = parser.parse_args()

    term_ids = [x.strip() for x in args.ids.split(",")] if args.ids else None

    if args.validate:
        if not OUTPUT_JSON.is_file():
            raise SystemExit(f"missing {OUTPUT_JSON}")
        payload = json.loads(OUTPUT_JSON.read_text(encoding="utf-8"))
    else:
        payload = build_payload(term_ids)
        OUTPUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {OUTPUT_JSON.relative_to(ROOT)} ({len(payload['terms'])} terms)")

    errors = validate_payload(payload)
    if errors:
        print(f"validation: {len(errors)} error(s)")
        for e in errors[:30]:
            print(f"  - {e}")
        if len(errors) > 30:
            print(f"  ... and {len(errors) - 30} more")
        raise SystemExit(1)
    print(f"validation: OK ({len(payload.get('terms') or {})} terms)")


if __name__ == "__main__":
    main()
