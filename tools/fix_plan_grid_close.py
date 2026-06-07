#!/usr/bin/env python3
"""tool-plan-grid の閉じタグ </div> が欠けている記事を修正する。"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
GRID_OPEN = '<div class="tool-plan-grid">'
TABLE_MARK = '<table class="tool-spec-table">'


def fix_file(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    start = text.find(GRID_OPEN)
    if start == -1:
        return False
    table = text.find(TABLE_MARK, start)
    if table == -1:
        return False
    chunk = text[start:table]
    missing = chunk.count("<div") - chunk.count("</div>")
    if missing <= 0:
        return False
    insert = "      </div>\n" * missing
    path.write_text(text[:table] + insert + text[table:], encoding="utf-8")
    return True


def main() -> None:
    fixed = [p.parent.name for p in sorted(TOOLS.glob("*/index.html")) if fix_file(p)]
    print(f"fixed {len(fixed)} files")


if __name__ == "__main__":
    main()
