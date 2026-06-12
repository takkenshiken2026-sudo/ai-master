#!/usr/bin/env python3
"""キャリア記事の末尾関連ブロックをカード型2列レイアウトに揃える。"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAREER_DIR = ROOT / "career"

ASIDE_RE = re.compile(
    r'    <aside class="tool-related-wrap">\n'
    r'      <div class="tool-related-block">\n'
    r'        <h2 class="tool-related-heading">(?P<h1>[^<]+)</h2>\n'
    r'        <ul class="tool-related-list">\n'
    r'(?P<b1>(?:          .*\n)*?)'
    r'        </ul>\n'
    r'      </div>\n'
    r'      <div class="tool-related-block">\n'
    r'        <h2 class="tool-related-heading">(?P<h2>[^<]+)</h2>\n'
    r'        <ul class="tool-related-list">\n'
    r'(?P<b2>(?:          .*\n)*?)'
    r'        </ul>\n'
    r'      </div>\n'
    r'    </aside>',
    re.MULTILINE,
)


def build_aside(h1: str, block1: str, h2: str, block2: str) -> str:
    return (
        '    <aside class="tool-related-wrap" id="related">\n'
        '      <h2 class="tool-related-section-title">関連するキャリア・リソース</h2>\n'
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
    if 'id="related-guides"' in text:
        return False

    match = ASIDE_RE.search(text)
    if not match:
        print(f"skip (no match): {path.relative_to(ROOT)}")
        return False

    new_aside = build_aside(match.group("h1"), match.group("b1"), match.group("h2"), match.group("b2"))
    path.write_text(text[: match.start()] + new_aside + text[match.end() :], encoding="utf-8")
    return True


def main() -> None:
    updated = 0
    for path in sorted(CAREER_DIR.glob("*/index.html")):
        if migrate_file(path):
            updated += 1
            print(f"updated: {path.relative_to(ROOT)}")
    print(f"done: {updated} career articles")


if __name__ == "__main__":
    main()
