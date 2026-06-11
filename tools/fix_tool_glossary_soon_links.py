#!/usr/bin/env python3
"""Replace tool article「準備中」glossary pills with links when the term is published.

  python3 tools/fix_tool_glossary_soon_links.py
  python3 tools/fix_tool_glossary_soon_links.py --dry-run
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = ROOT / "tools"
GLOSSARY_DIR = ROOT / "glossary"

# Display label (inside soon <li>) -> glossary slug
LABEL_TO_SLUG: dict[str, str] = {
    "プロンプト": "prompt",
    "ハルシネーション": "hallucination",
    "大規模言語モデル（LLM）": "llm",
    "LLM": "llm",
    "RAG（検索拡張生成）": "rag",
    "RAG": "rag",
    "Text-to-Image（画像生成）": "text-to-image",
}

SOON_RE = re.compile(
    r'<li class="tool-related-list__soon">([^<]+?)\s*'
    r'<span class="tool-soon-badge">準備中</span></li>'
)


def published_slugs() -> set[str]:
    return {p.name for p in GLOSSARY_DIR.iterdir() if p.is_dir() and (p / "index.html").is_file()}


def fix_html(text: str, published: set[str]) -> tuple[str, int]:
    count = 0

    def repl(match: re.Match[str]) -> str:
        nonlocal count
        label = match.group(1).strip()
        slug = LABEL_TO_SLUG.get(label)
        if not slug or slug not in published:
            return match.group(0)
        count += 1
        return f'<li><a href="../../glossary/{slug}/">{label}</a></li>'

    return SOON_RE.sub(repl, text), count


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    published = published_slugs()
    files_changed = 0
    links_added = 0

    for path in sorted(TOOLS_DIR.glob("*/index.html")):
        original = path.read_text(encoding="utf-8")
        updated, n = fix_html(original, published)
        if n == 0:
            continue
        links_added += n
        files_changed += 1
        print(f"{'would update' if args.dry_run else 'updated'}: {path.relative_to(ROOT)} ({n} link(s))")
        if not args.dry_run:
            path.write_text(updated, encoding="utf-8")

    print(f"done: {files_changed} file(s), {links_added} link(s)")


if __name__ == "__main__":
    main()
