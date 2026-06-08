#!/usr/bin/env python3
"""全HTMLのグロナビに「学習ガイド」タブを追加する（未追加のファイルのみ）。

  python3 tools/patch_nav_guide.py
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", "node_modules", "supabase"}

EXAM_LINE_RE = re.compile(
    r"^(\s*)<li><a href=\"([^\"]*exams/?)\"([^>]*)>試験対策</a></li>\s*$",
    re.MULTILINE,
)


def guide_href_from_exam(exam_href: str) -> str:
    if "exams" in exam_href:
        return exam_href.replace("exams", "guide", 1)
    return "../guide/"


def patch_file(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    if "学習ガイド" in text:
        return False
    if "試験対策</a></li>" not in text:
        return False

    def repl(match: re.Match[str]) -> str:
        indent = match.group(1)
        exam_href = match.group(2)
        guide_href = guide_href_from_exam(exam_href)
        return (
            f'{indent}<li><a href="{exam_href}"{match.group(3)}>試験対策</a></li>\n'
            f'{indent}<li><a href="{guide_href}">学習ガイド</a></li>\n'
        )

    new_text, count = EXAM_LINE_RE.subn(repl, text, count=1)
    if count != 1:
        return False
    path.write_text(new_text, encoding="utf-8")
    return True


def main() -> None:
    updated = 0
    for path in ROOT.rglob("*.html"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if patch_file(path):
            updated += 1
    print(f"Patched {updated} HTML files")


if __name__ == "__main__":
    main()
