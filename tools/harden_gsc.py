#!/usr/bin/env python3
"""GSC 向けの noindex 付与と sitemap 整備。

  python3 tools/harden_gsc.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from site_meta import (  # noqa: E402
    PLAYER_DEEPLINK_CANONICAL_HTML,
    SITE_CANONICAL_NORMALIZE_HTML,
    SITE_ORIGIN,
    render_robots_meta,
)

SITEMAP = ROOT / "sitemap.xml"
GUIDE_DIR = ROOT / "guide"
NOINDEX_META = render_robots_meta().strip()

# JS プレイヤー・未公開コンテンツはインデックス対象外
NOINDEX_PATHS = [
    ROOT / "exams/g-kentei/practice/index.html",
    ROOT / "exams/g-kentei/drill/index.html",
    ROOT / "exams/genai-passport/practice/index.html",
    ROOT / "exams/genai-passport/drill/index.html",
    ROOT / "exams/g-kentei/mock/play.html",
    ROOT / "exams/g-kentei/mock/index.html",
    ROOT / "exams/genai-passport/mock/play.html",
    ROOT / "exams/genai-passport/mock/index.html",
    ROOT / "exams/it-passport/index.html",
    ROOT / "exams/it-passport/past/index.html",
    ROOT / "exams/it-passport/past/play.html",
    ROOT / "exams/it-passport/drill/index.html",
    ROOT / "exams/it-passport/drill/questions/index.html",
    ROOT / "exams/it-passport/practice/index.html",
    ROOT / "exams/it-passport/practice/questions/index.html",
    ROOT / "exams/it-passport/mock/index.html",
    ROOT / "exams/it-passport/mock/play.html",
]

PLAYER_SCRIPT_PATHS = [
    ROOT / "exams/g-kentei/practice/index.html",
    ROOT / "exams/g-kentei/drill/index.html",
    ROOT / "exams/genai-passport/practice/index.html",
    ROOT / "exams/genai-passport/drill/index.html",
]

# sitemap から除外（noindex または未公開）
SITEMAP_EXCLUDE = {
    f"{SITE_ORIGIN}/exams/g-kentei/drill/",
    f"{SITE_ORIGIN}/exams/g-kentei/practice/",
    f"{SITE_ORIGIN}/exams/genai-passport/drill/",
    f"{SITE_ORIGIN}/exams/genai-passport/practice/",
    f"{SITE_ORIGIN}/exams/it-passport/",
    f"{SITE_ORIGIN}/exams/it-passport/past/",
    f"{SITE_ORIGIN}/exams/it-passport/drill/",
    f"{SITE_ORIGIN}/exams/it-passport/practice/",
    f"{SITE_ORIGIN}/exams/it-passport/mock/",
    f"{SITE_ORIGIN}/exams/it-passport/drill/questions/",
    f"{SITE_ORIGIN}/exams/it-passport/practice/questions/",
    f"{SITE_ORIGIN}/exams/g-kentei/mock/",
    f"{SITE_ORIGIN}/exams/genai-passport/mock/",
}

TEXT_REPLACEMENTS = (
    ("過去問想定 ", ""),
    ("過去問を想定した", "本番形式の"),
    ("本番・過去問を想定した", "本番形式の"),
)


def ensure_noindex(path: Path) -> bool:
    if not path.is_file():
        return False
    text = path.read_text(encoding="utf-8")
    changed = False
    if "noindex" not in text:
        marker = '<meta name="viewport" content="width=device-width, initial-scale=1.0">'
        if marker in text:
            text = text.replace(
                marker,
                f"{marker}\n  {NOINDEX_META}",
                1,
            )
            changed = True
    for old, new in TEXT_REPLACEMENTS:
        if old in text:
            text = text.replace(old, new)
            changed = True
    if changed:
        path.write_text(text, encoding="utf-8")
    return changed


def ensure_player_head_scripts(path: Path) -> bool:
    if not path.is_file():
        return False
    text = path.read_text(encoding="utf-8")
    changed = False

    if 'match[1] + "/q/"' not in text:
        marker = '<link rel="canonical" href="'
        idx = text.find(marker)
        if idx >= 0:
            end = text.find(">", idx) + 1
            text = text[:end] + "\n" + PLAYER_DEEPLINK_CANONICAL_HTML.strip() + text[end:]
            changed = True

    if 'path.endsWith("/index.html")' not in text:
        marker = '<link rel="canonical" href="'
        idx = text.find(marker)
        if idx >= 0:
            end = text.find(">", idx) + 1
            if 'match[1] + "/q/"' in text:
                script_end = text.find("</script>", text.find('match[1] + "/q/"'))
                if script_end >= 0:
                    end = script_end + len("</script>")
            text = text[:end] + "\n" + SITE_CANONICAL_NORMALIZE_HTML.strip() + text[end:]
            changed = True

    if changed:
        path.write_text(text, encoding="utf-8")
    return changed


def strip_domain_urls(text: str) -> str:
    return re.sub(
        r"\n  <url>\n    <loc>https://ai-master\.jp/exams/[^<]+/(?:practice|drill)/domain/[^<]+</loc>[\s\S]*?</url>",
        "",
        text,
    )


def guide_sitemap_entries() -> list[str]:
    entries = [
        f"""  <url>
    <loc>{SITE_ORIGIN}/guide/</loc>
    <changefreq>weekly</changefreq>
    <priority>0.9</priority>
  </url>"""
    ]
    for article_dir in sorted(GUIDE_DIR.iterdir()):
        if not article_dir.is_dir():
            continue
        if not (article_dir / "index.html").is_file():
            continue
        loc = f"{SITE_ORIGIN}/guide/{article_dir.name}/"
        entries.append(
            f"""  <url>
    <loc>{loc}</loc>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>"""
        )
    return entries


def update_sitemap() -> None:
    if not SITEMAP.is_file():
        print("skip sitemap: not found")
        return

    text = SITEMAP.read_text(encoding="utf-8")

    text = re.sub(
        r"\n  <!-- guide-pages:start -->[\s\S]*?  <!-- guide-pages:end -->",
        "",
        text,
    )

    for loc in SITEMAP_EXCLUDE:
        text = re.sub(
            rf"\n  <url>\n    <loc>{re.escape(loc)}</loc>[\s\S]*?</url>",
            "",
            text,
        )

    text = strip_domain_urls(text)

    guide_block = (
        "\n  <!-- guide-pages:start -->\n"
        + "\n".join(guide_sitemap_entries()[1:])
        + "\n  <!-- guide-pages:end -->"
    )
    text = text.replace(
        "  <url>\n    <loc>https://ai-master.jp/exams/</loc>",
        guide_block + "\n  <url>\n    <loc>https://ai-master.jp/exams/</loc>",
        1,
    )

    SITEMAP.write_text(text, encoding="utf-8")
    guide_count = len(guide_sitemap_entries()) - 1
    print(f"updated sitemap: +{guide_count} guide URLs, excluded {len(SITEMAP_EXCLUDE)} exam URLs")


def main() -> None:
    patched = 0
    for path in NOINDEX_PATHS:
        if ensure_noindex(path):
            patched += 1
            print(f"noindex: {path.relative_to(ROOT)}")
    for path in PLAYER_SCRIPT_PATHS:
        if ensure_player_head_scripts(path):
            patched += 1
            print(f"player scripts: {path.relative_to(ROOT)}")
    update_sitemap()
    print(f"patched {patched} HTML files")


if __name__ == "__main__":
    main()
