#!/usr/bin/env python3
"""用語辞典の末尾関連ブロックに related-exams / related-terms とカードクラスを付与する。"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GLOSSARY_DIR = ROOT / "glossary"

ASIDE_RE = re.compile(
    r'<aside class="tool-related-wrap" id="related">\n'
    r'      <h2 class="tool-related-section-title">関連する試験・用語</h2>\n'
    r'\n'
    r'      <div class="tool-related-block">\n'
    r'        <h2 class="tool-related-heading">関連する試験問題</h2>\n'
    r'        <ul class="tool-related-list">\n'
    r'(?P<exams>(?:          .*\n)*?)'
    r'        </ul>\n'
    r'      </div>\n'
    r'      <div class="tool-related-block">\n'
    r'        <h2 class="tool-related-heading">関連用語</h2>\n'
    r'        <ul class="tool-related-list">\n'
    r'(?P<terms>(?:          .*\n)*?)'
    r'        </ul>\n'
    r'      </div>\n'
    r'</aside>',
    re.MULTILINE,
)


def migrate_html(text: str) -> tuple[str, bool]:
    if 'id="related-exams"' in text:
        return text, False

    match = ASIDE_RE.search(text)
    if not match:
        return text, False

    replacement = (
        '<aside class="tool-related-wrap" id="related">\n'
        '      <h2 class="tool-related-section-title">関連する試験・用語</h2>\n'
        '      <div class="tool-related-block" id="related-exams">\n'
        '        <h2 class="tool-related-heading">関連する試験問題</h2>\n'
        '        <ul class="tool-related-list tool-related-list--cards">\n'
        f"{match.group('exams')}"
        "        </ul>\n"
        "      </div>\n"
        "\n"
        '      <div class="tool-related-block" id="related-terms">\n'
        '        <h2 class="tool-related-heading">関連用語</h2>\n'
        '        <ul class="tool-related-list tool-related-list--cards">\n'
        f"{match.group('terms')}"
        "        </ul>\n"
        "      </div>\n"
        "</aside>"
    )
    return text[: match.start()] + replacement + text[match.end() :], True


def main() -> None:
    updated = 0
    skipped = 0
    for path in sorted(GLOSSARY_DIR.glob("*/index.html")):
        original = path.read_text(encoding="utf-8")
        new_text, changed = migrate_html(original)
        if not changed:
            if "tool-related-wrap" in original and 'id="related-exams"' not in original:
                skipped += 1
                print(f"skip (no match): {path.relative_to(ROOT)}")
            continue
        path.write_text(new_text, encoding="utf-8")
        updated += 1
        print(f"updated: {path.relative_to(ROOT)}")
    print(f"done: {updated} updated, {skipped} skipped")


if __name__ == "__main__":
    main()
