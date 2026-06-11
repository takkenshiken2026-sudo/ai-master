#!/usr/bin/env python3
"""関連用語を試験問題と同数・同カード形式に揃える。

  python3 tools/normalize_glossary_related_terms.py
  python3 tools/normalize_glossary_related_terms.py --dry-run
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GLOSSARY_DIR = ROOT / "glossary"

EXAMS_BLOCK_RE = re.compile(
    r'(<div class="tool-related-block" id="related-exams">[\s\S]*?'
    r'<ul class="tool-related-list)(?: tool-related-list--cards)?(">)([\s\S]*?)(</ul>)',
    re.MULTILINE,
)
TERMS_BLOCK_RE = re.compile(
    r'(<div class="tool-related-block")(?: id="related-terms")?(>\s*'
    r'<h2 class="tool-related-heading">関連用語</h2>\s*'
    r')(<ul class=")(tool-related-list(?: tool-related-list--cards)?)(">)([\s\S]*?)(</ul>)',
    re.MULTILINE,
)
LI_RE = re.compile(r"<li[^>]*>[\s\S]*?</li>", re.MULTILINE)


def classify_li(li: str) -> str:
    if "tool-related-list__index" in li:
        return "index"
    if "tool-related-list__soon" in li:
        return "soon"
    return "link"


def normalize_terms_list(items: list[str], limit: int) -> list[str]:
    links: list[str] = []
    soon: list[str] = []
    index: list[str] = []
    for li in items:
        kind = classify_li(li)
        if kind == "index":
            index.append(li.strip())
        elif kind == "soon":
            soon.append(li.strip())
        else:
            links.append(li.strip())
    return links[:limit] + soon + index


def normalize_html(text: str) -> tuple[str, bool]:
    exam_match = EXAMS_BLOCK_RE.search(text)
    terms_match = TERMS_BLOCK_RE.search(text)
    if not exam_match or not terms_match:
        return text, False

    exam_items = LI_RE.findall(exam_match.group(3))
    exam_count = sum(1 for li in exam_items if classify_li(li) == "link")
    if exam_count == 0:
        return text, False

    term_items = LI_RE.findall(terms_match.group(6))
    new_term_items = normalize_terms_list(term_items, exam_count)
    term_lines = "\n          ".join(new_term_items)

    new_exam_ul = (
        f"{exam_match.group(1)} tool-related-list--cards{exam_match.group(2)}"
        f"{exam_match.group(3)}{exam_match.group(4)}"
    )
    new_terms_block = (
        f'{terms_match.group(1)} id="related-terms"{terms_match.group(2)}'
        f'{terms_match.group(3)}tool-related-list tool-related-list--cards{terms_match.group(5)}'
        f"\n          {term_lines}\n        {terms_match.group(7)}"
    )

    changed = False
    if new_exam_ul != exam_match.group(0):
        text = text[: exam_match.start()] + new_exam_ul + text[exam_match.end() :]
        changed = True
        terms_match = TERMS_BLOCK_RE.search(text)
        if not terms_match:
            return text, changed
        term_items = LI_RE.findall(terms_match.group(6))
        new_term_items = normalize_terms_list(term_items, exam_count)
        term_lines = "\n          ".join(new_term_items)
        new_terms_block = (
            f'{terms_match.group(1)} id="related-terms"{terms_match.group(2)}'
            f'{terms_match.group(3)}tool-related-list tool-related-list--cards{terms_match.group(5)}'
            f"\n          {term_lines}\n        {terms_match.group(7)}"
        )

    if new_terms_block != terms_match.group(0):
        text = text[: terms_match.start()] + new_terms_block + text[terms_match.end() :]
        changed = True

    return text, changed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    updated = 0
    for path in sorted(GLOSSARY_DIR.glob("*/index.html")):
        original = path.read_text(encoding="utf-8")
        if 'id="related-exams"' not in original:
            continue
        new_text, changed = normalize_html(original)
        if not changed:
            continue
        updated += 1
        print(f"{'would update' if args.dry_run else 'updated'}: {path.relative_to(ROOT)}")
        if not args.dry_run:
            path.write_text(new_text, encoding="utf-8")
    print(f"done: {updated} file(s)")


if __name__ == "__main__":
    main()
