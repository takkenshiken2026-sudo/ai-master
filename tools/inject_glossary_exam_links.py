#!/usr/bin/env python3
"""用語辞典記事に「演習・模擬試験」ブロックを注入する（SEO主リンクは維持）。

  python3 tools/inject_glossary_exam_links.py --ids generative-ai,text-to-video,bert
  python3 tools/inject_glossary_exam_links.py --all
"""

from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GLOSSARY_DIR = ROOT / "glossary"
LINKS_JSON = ROOT / "data" / "glossary-question-links.json"

MARKER_START = "      <!-- exam-resources:start -->"
MARKER_END = "      <!-- exam-resources:end -->"

EXAM_HUBS = {
    "g-kentei": [
        ("G検定 一問一答", "drill"),
        ("G検定 模擬試験", "mock"),
        ("G検定 実践演習", "practice"),
    ],
    "genai-passport": [
        ("生成AIパスポート 一問一答", "drill"),
        ("生成AIパスポート 模擬試験", "mock"),
        ("生成AIパスポート 実践演習", "practice"),
    ],
}


def hub_exams(entry: dict) -> list[str]:
    """Show drill/mock/practice hubs for exams with hand-curated question links first."""
    questions = entry.get("questions") or []
    html_exams = sorted({q["exam"] for q in questions if q.get("source") == "html"})
    if html_exams:
        return html_exams
    return sorted(entry.get("exams") or [])


def render_resources_block(entry: dict) -> str:
    exams = hub_exams(entry)
    questions = entry.get("questions") or []
    items: list[str] = []

    for exam_id in exams:
        for label, mode in EXAM_HUBS.get(exam_id, []):
            href = f"../../exams/{exam_id}/{mode}/"
            items.append(f'          <li><a href="{href}">{html.escape(label)}</a></li>')

    first_drill = next((q for q in questions if q.get("mode") == "drill"), None)
    if first_drill:
        player = first_drill.get("playerUrl", "").lstrip("/")
        qid = first_drill.get("id") or first_drill.get("slug", "").upper()
        items.append(
            f'          <li><a href="../../{player}">{html.escape(qid)}を演習モードで解く</a></li>'
        )

    if not items:
        return ""

    lis = "\n".join(items)
    return f"""{MARKER_START}
      <div class="tool-related-block" id="exam-resources">
        <h2 class="tool-related-heading">演習・模擬試験</h2>
        <ul class="tool-related-list">
{lis}
        </ul>
      </div>
{MARKER_END}"""


def inject_into_html(text: str, block: str) -> str:
    if not block:
        return text

    pattern = re.compile(
        re.escape(MARKER_START) + r"[\s\S]*?" + re.escape(MARKER_END)
    )
    if pattern.search(text):
        return pattern.sub(block, text, count=1)

    if 'id="exam-resources"' in text or "exam-resources:start" in text:
        return text

    # Insert after related-exams block if present, else after opening aside
    anchor = '      <div class="tool-related-block" id="related-exams">'
    if anchor in text:
        end = text.find("      </div>", text.find(anchor))
        if end != -1:
            end += len("      </div>")
            return text[:end] + "\n" + block + text[end:]

    aside = '<aside class="tool-related-wrap"'
    pos = text.find(aside)
    if pos == -1:
        return text
    close = text.find(">", pos)
    if close == -1:
        return text
    return text[: close + 1] + "\n" + block + text[close + 1 :]


def inject_term(term_id: str, entry: dict) -> bool:
    path = GLOSSARY_DIR / term_id / "index.html"
    if not path.is_file():
        print(f"skip missing: {term_id}")
        return False
    block = render_resources_block(entry)
    if not block:
        print(f"skip empty: {term_id}")
        return False
    original = path.read_text(encoding="utf-8")
    updated = inject_into_html(original, block)
    if updated == original:
        print(f"unchanged: {term_id}")
        return False
    path.write_text(updated, encoding="utf-8")
    print(f"updated: {path.relative_to(ROOT)}")
    return True


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ids", help="comma-separated term ids")
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()

    if not LINKS_JSON.is_file():
        raise SystemExit(f"missing {LINKS_JSON} — run build_glossary_question_links.py first")

    payload = json.loads(LINKS_JSON.read_text(encoding="utf-8"))
    terms: dict[str, dict] = payload.get("terms") or {}

    if args.all:
        target_ids = sorted(terms.keys())
    elif args.ids:
        target_ids = [x.strip() for x in args.ids.split(",") if x.strip()]
    else:
        raise SystemExit("specify --ids or --all")

    count = 0
    for tid in target_ids:
        entry = terms.get(tid)
        if not entry:
            print(f"skip unknown id: {tid}")
            continue
        if inject_term(tid, entry):
            count += 1
    print(f"done: {count} file(s) updated")


if __name__ == "__main__":
    main()
