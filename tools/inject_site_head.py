#!/usr/bin/env python3
"""全 HTML にファビコン・OG 寸法メタを注入する（未設定ページのみ）。"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from site_meta import (
    SITE_GA4_HTML,
    SITE_ICONS_HTML,
    SITE_OG_HEIGHT,
    SITE_OG_IMAGE,
    SITE_OG_WIDTH,
)

ICON_MARKER = 'rel="icon" href="/assets/images/favicon.svg"'
OG_DIM_MARKER = 'property="og:image:width"'
GA4_MARKER = "googletagmanager.com/gtag/js"

DEFAULT_OG_BLOCK = f"""  <meta property="og:image:width" content="{SITE_OG_WIDTH}">
  <meta property="og:image:height" content="{SITE_OG_HEIGHT}">
"""


def inject_icons(content: str) -> str:
    if ICON_MARKER in content:
        return content
    match = re.search(r"(<link rel=\"canonical\"[^>]*>\n)", content)
    if match:
        return content[: match.end()] + SITE_ICONS_HTML + content[match.end() :]
    match = re.search(r"(<title>[^<]*</title>\n)", content)
    if match:
        return content[: match.end()] + SITE_ICONS_HTML + content[match.end() :]
    return content


def inject_ga4(content: str) -> str:
    if GA4_MARKER in content:
        return content
    return content.replace("</head>", f"{SITE_GA4_HTML}</head>", 1)


def inject_default_og_dims(content: str) -> str:
    if OG_DIM_MARKER in content:
        return content
    if SITE_OG_IMAGE not in content:
        return content
    pattern = (
        r'(<meta property="og:image" content="'
        + re.escape(SITE_OG_IMAGE)
        + r'">\n)'
    )
    return re.sub(pattern, r"\1" + DEFAULT_OG_BLOCK, content, count=1)


def process_file(path: Path) -> bool:
    original = path.read_text(encoding="utf-8")
    updated = inject_icons(original)
    updated = inject_default_og_dims(updated)
    updated = inject_ga4(updated)
    if updated != original:
        path.write_text(updated, encoding="utf-8")
        return True
    return False


def main() -> None:
    changed = 0
    for path in sorted(ROOT.rglob("*.html")):
        if process_file(path):
            changed += 1
    print(f"Updated {changed} HTML files")


if __name__ == "__main__":
    main()
