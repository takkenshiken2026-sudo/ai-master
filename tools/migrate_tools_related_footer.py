#!/usr/bin/env python3
"""AIツール記事の末尾関連ブロックをカード型2列レイアウトに揃える。"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = ROOT / "tools"

ASIDE_RE = re.compile(
    r'<aside class="tool-related-wrap"(?: id="related")?>\s*\n'
    r'(?P<body>(?:^[ \t]+.*\n)*?)'
    r'^[ \t]*</aside>',
    re.MULTILINE,
)

BLOCK_RE = re.compile(
    r'^[ \t]*<div class="tool-related-block"(?: id="[^"]+")?>\s*\n'
    r'^[ \t]*<h2 class="tool-related-heading">(?P<h>[^<]+)</h2>\s*\n'
    r'^[ \t]*<ul class="tool-related-list(?: tool-related-list--cards)?">\s*\n'
    r'(?P<items>(?:^[ \t]*.*\n)*?)'
    r'^[ \t]*</ul>\s*\n'
    r'^[ \t]*</div>\s*\n',
    re.MULTILINE,
)


def normalize_items(items: str) -> str:
    lines: list[str] = []
    for line in items.splitlines():
        if not line.strip():
            continue
        lines.append(f"          {line.lstrip()}")
    return "\n".join(lines) + ("\n" if lines else "")


def build_aside(h1: str, block1: str, h2: str, block2: str) -> str:
    return (
        '    <aside class="tool-related-wrap" id="related">\n'
        '      <h2 class="tool-related-section-title">関連するツール・用語</h2>\n'
        '      <div class="tool-related-block" id="related-guides">\n'
        f'        <h2 class="tool-related-heading">{h1}</h2>\n'
        '        <ul class="tool-related-list tool-related-list--cards">\n'
        f"{block1}"
        "        </ul>\n"
        "      </div>\n"
        "\n"
        '      <div class="tool-related-block" id="related-resources">\n'
        f'        <h2 class="tool-related-heading">{h2}</h2>\n'
        '        <ul class="tool-related-list tool-related-list--cards">\n'
        f"{block2}"
        "        </ul>\n"
        "      </div>\n"
        "    </aside>"
    )


def migrate_file(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    if 'id="related-guides"' in text or 'id="related-exams"' in text:
        return False

    match = ASIDE_RE.search(text)
    if not match:
        print(f"skip (no aside): {path.relative_to(ROOT)}")
        return False

    blocks = list(BLOCK_RE.finditer(match.group("body")))
    if len(blocks) != 2:
        print(f"skip ({len(blocks)} blocks): {path.relative_to(ROOT)}")
        return False

    b1, b2 = blocks
    new_aside = build_aside(
        b1.group("h"),
        normalize_items(b1.group("items")),
        b2.group("h"),
        normalize_items(b2.group("items")),
    )
    path.write_text(text[: match.start()] + new_aside + text[match.end() :], encoding="utf-8")
    return True


def main() -> None:
    updated = 0
    for path in sorted(TOOLS_DIR.glob("*/index.html")):
        if migrate_file(path):
            updated += 1
            print(f"updated: {path.relative_to(ROOT)}")
    print(f"done: {updated} tool articles")


if __name__ == "__main__":
    main()
