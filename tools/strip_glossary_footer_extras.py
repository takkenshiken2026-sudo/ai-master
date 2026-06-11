#!/usr/bin/env python3
"""用語辞典フッターから演習ブロックと「用語辞典一覧へ」を除去。

  python3 tools/strip_glossary_footer_extras.py
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GLOSSARY_DIR = ROOT / "glossary"

EXAM_RESOURCES_RE = re.compile(
    r"\n?\s*<!-- exam-resources:start -->[\s\S]*?<!-- exam-resources:end -->",
    re.MULTILINE,
)
INDEX_LI_RE = re.compile(
    r'\n?\s*<li class="tool-related-list__index">[\s\S]*?</li>',
    re.MULTILINE,
)


def strip_html(text: str) -> tuple[str, bool]:
    updated = text
    changed = False

    new = EXAM_RESOURCES_RE.sub("", updated)
    if new != updated:
        updated = new
        changed = True

    new = INDEX_LI_RE.sub("", updated)
    if new != updated:
        updated = re.sub(r"\n{3,}", "\n\n", updated)
        updated = updated
        changed = True

    return updated, changed


def main() -> None:
    count = 0
    for path in sorted(GLOSSARY_DIR.glob("*/index.html")):
        original = path.read_text(encoding="utf-8")
        updated, changed = strip_html(original)
        if not changed:
            continue
        path.write_text(updated, encoding="utf-8")
        count += 1
        print(f"updated: {path.relative_to(ROOT)}")
    print(f"done: {count} file(s)")


if __name__ == "__main__":
    main()
