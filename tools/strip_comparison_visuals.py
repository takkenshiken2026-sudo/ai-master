#!/usr/bin/env python3
"""比較セクションのブランド行（画像+名称）と表ヘッダーのロゴ画像を削除する。"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"

TABLE_LOGO_RE = re.compile(
    r'<img src="[^"]*" alt="[^"]*" class="tool-table-logo" width="22" height="22">'
)
ORPHAN_BRAND_RE = re.compile(
    r"\n\s*<div class=\"tool-compare-brand\">[\s\S]*?</div>",
    re.MULTILINE,
)
STRAY_CLOSE_RE = re.compile(r"\n\s*</div>\s*\n\s*<table class=\"tool-spec-table\">")


def remove_brands_block(text: str) -> str:
    marker = '<div class="tool-compare-brands">'
    while True:
        start = text.find(marker)
        if start == -1:
            break
        depth = 0
        end = None
        i = start
        while i < len(text):
            if text.startswith("<div", i):
                depth += 1
            elif text.startswith("</div>", i):
                depth -= 1
                if depth == 0:
                    end = i + len("</div>")
                    break
            i += 1
        if end is None:
            break
        text = text[:start] + text[end:]
    text = ORPHAN_BRAND_RE.sub("", text)
    text = STRAY_CLOSE_RE.sub("\n\n      <table class=\"tool-spec-table\">", text)
    return text


def strip_file(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    original = text
    text = remove_brands_block(text)
    text = TABLE_LOGO_RE.sub("", text)
    if text != original:
        path.write_text(text, encoding="utf-8")
    return text != original


def main() -> None:
    changed = sum(1 for p in TOOLS.glob("*/index.html") if strip_file(p))
    print(f"updated {changed} files")


if __name__ == "__main__":
    main()
