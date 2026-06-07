#!/usr/bin/env python3
"""ツール記事の JSON-LD publisher をページ単体で完結する定義に修正する。"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = ROOT / "tools"

PUBLISHER_RE = re.compile(
    r'"publisher":\s*\{\s*"@id":\s*"https://ai-master\.jp/#organization"\s*\}',
    re.MULTILINE,
)
PUBLISHER_NEW = (
    '"publisher": { "@type": "Organization", "name": "AI Master", '
    '"url": "https://ai-master.jp/" }'
)


def main() -> None:
    count = 0
    for path in TOOLS_DIR.glob("*/index.html"):
        text = path.read_text(encoding="utf-8")
        if not PUBLISHER_RE.search(text):
            continue
        path.write_text(PUBLISHER_RE.sub(PUBLISHER_NEW, text), encoding="utf-8")
        count += 1
    print(f"patched {count} tool articles")


if __name__ == "__main__":
    main()
