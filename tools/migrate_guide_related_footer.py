#!/usr/bin/env python3
"""学習ガイド記事の末尾関連ブロックを用語辞典と同じカード型2列に揃える。"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GUIDE_DIR = ROOT / "guide"
TEMPLATE = GUIDE_DIR / "_template.html"

ASIDE_PATTERN = re.compile(
    r'    <aside class="tool-related-wrap">\n'
    r'      <div class="tool-related-block">\n'
    r'        <h2 class="tool-related-heading">関連する学習ガイド</h2>\n'
    r'        <ul class="tool-related-list">\n'
    r'((?:          .*\n)*?)'
    r'        </ul>\n'
    r'      </div>\n'
    r'      <div class="tool-related-block">\n'
    r'        <h2 class="tool-related-heading">学習リソース</h2>\n'
    r'        <ul class="tool-related-list">\n'
    r'((?:          .*\n)*?)'
    r'        </ul>\n'
    r'      </div>\n'
    r'    </aside>',
    re.MULTILINE,
)

LI_PATTERN = re.compile(r'^(\s*)<li(?![^>]*tool-related-list__index)([^>]*)>(.*)</li>\s*$', re.MULTILINE)
INDEX_LI_PATTERN = re.compile(
    r'^(\s*)<li class="tool-related-list__index">(.*)</li>\s*$', re.MULTILINE
)


def split_items(block: str) -> tuple[list[str], list[str]]:
    content: list[str] = []
    index: list[str] = []
    for line in block.splitlines():
        if not line.strip():
            continue
        if 'tool-related-list__index' in line:
            index.append(line)
        else:
            content.append(line)
    return content, index


def trim_resources(guide_content: list[str], resource_content: list[str]) -> list[str]:
    target = len(guide_content)
    if len(resource_content) <= target:
        return resource_content
    return resource_content[:target]


def build_aside(guide_block: str, resource_block: str) -> str:
    guide_content, guide_index = split_items(guide_block)
    resource_content, resource_index = split_items(resource_block)
    resource_content = trim_resources(guide_content, resource_content)

    guide_lines = guide_content + guide_index
    resource_lines = resource_content + resource_index

    return (
        '    <aside class="tool-related-wrap" id="related">\n'
        '      <h2 class="tool-related-section-title">関連するガイド・リソース</h2>\n'
        '      <div class="tool-related-block" id="related-guides">\n'
        '        <h2 class="tool-related-heading">関連する学習ガイド</h2>\n'
        '        <ul class="tool-related-list tool-related-list--cards">\n'
        + "\n".join(guide_lines)
        + "\n"
        "        </ul>\n"
        "      </div>\n"
        "\n"
        '      <div class="tool-related-block" id="related-resources">\n'
        '        <h2 class="tool-related-heading">学習リソース</h2>\n'
        '        <ul class="tool-related-list tool-related-list--cards">\n'
        + "\n".join(resource_lines)
        + "\n"
        "        </ul>\n"
        "      </div>\n"
        "    </aside>"
    )


def migrate_file(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    if 'id="related-guides"' in text:
        return False

    match = ASIDE_PATTERN.search(text)
    if not match:
        print(f"skip (no match): {path.relative_to(ROOT)}")
        return False

    new_aside = build_aside(match.group(1), match.group(2))
    path.write_text(text[: match.start()] + new_aside + text[match.end() :], encoding="utf-8")
    return True


def migrate_template() -> bool:
    old = (
        '    <aside class="tool-related-wrap">\n'
        "      <div class=\"tool-related-block\">\n"
        '        <h2 class="tool-related-heading">関連する学習ガイド</h2>\n'
        '        <ul class="tool-related-list">\n'
    )
    new = (
        '    <aside class="tool-related-wrap" id="related">\n'
        '      <h2 class="tool-related-section-title">関連するガイド・リソース</h2>\n'
        '      <div class="tool-related-block" id="related-guides">\n'
        '        <h2 class="tool-related-heading">関連する学習ガイド</h2>\n'
        '        <ul class="tool-related-list tool-related-list--cards">\n'
    )
    text = TEMPLATE.read_text(encoding="utf-8")
    if old not in text:
        return False
    text = text.replace(old, new, 1)
    text = text.replace(
        '      <div class="tool-related-block">\n'
        '        <h2 class="tool-related-heading">学習リソース</h2>\n'
        '        <ul class="tool-related-list">\n',
        '      <div class="tool-related-block" id="related-resources">\n'
        '        <h2 class="tool-related-heading">学習リソース</h2>\n'
        '        <ul class="tool-related-list tool-related-list--cards">\n',
        1,
    )
    TEMPLATE.write_text(text, encoding="utf-8")
    return True


def main() -> None:
    updated = 0
    for path in sorted(GUIDE_DIR.glob("*/index.html")):
        if migrate_file(path):
            updated += 1
    if migrate_template():
        print("updated _template.html")
    print(f"migrated {updated} guide articles")


if __name__ == "__main__":
    main()
