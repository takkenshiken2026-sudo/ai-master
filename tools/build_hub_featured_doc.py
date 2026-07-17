#!/usr/bin/env python3
"""data/*-featured.json から運用ドキュメント HTML を生成。

  python3 tools/build_hub_featured_doc.py
"""

from __future__ import annotations

import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys_path = ROOT / "tools"
import sys

sys.path.insert(0, str(sys_path))
from site_meta import SITE_ADSENSE_HTML, SITE_GA4_HTML  # noqa: E402

OUT = ROOT / "docs" / "hub-featured" / "index.html"
SITEMAP = ROOT / "sitemap.xml"
SITE = "https://ai-master.jp"

HUBS = (
    {
        "key": "glossary",
        "label": "用語辞典",
        "featured_json": ROOT / "data" / "glossary-featured.json",
        "index_json": ROOT / "data" / "glossary-index.json",
        "hub_url": f"{SITE}/glossary/",
        "article_base": "/glossary/",
    },
    {
        "key": "guide",
        "label": "学習ガイド",
        "featured_json": ROOT / "data" / "guide-featured.json",
        "index_json": ROOT / "data" / "guide-index.json",
        "hub_url": f"{SITE}/guide/",
        "article_base": "/guide/",
    },
    {
        "key": "career",
        "label": "キャリア",
        "featured_json": ROOT / "data" / "career-featured.json",
        "index_json": ROOT / "data" / "career-index.json",
        "hub_url": f"{SITE}/career/",
        "article_base": "/career/",
    },
)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def lookup_items(hub: dict) -> list[dict]:
    featured = load_json(hub["featured_json"])
    data = load_json(hub["index_json"])
    if hub["key"] == "glossary":
        by_id = {t["id"]: t for t in data["terms"]}
        featured_meta = {f["id"]: f for f in data.get("featured") or []}
    else:
        by_id = {a["id"]: a for a in data["articles"]}
        featured_meta = {f["id"]: f for f in data.get("featured") or []}

    rows = []
    for item_id in featured:
        row = by_id.get(item_id)
        meta = featured_meta.get(item_id, {})
        if not row:
            rows.append({"id": item_id, "name": item_id, "icon": meta.get("icon"), "missing": True})
            continue
        name = row.get("name") or item_id
        summary = row.get("summary") or row.get("keyword") or ""
        rows.append(
            {
                "id": item_id,
                "name": name,
                "summary": summary,
                "icon": meta.get("icon"),
                "url": f"{SITE}{hub['article_base']}{item_id}/",
            }
        )
    return rows


def render_featured_cards(rows: list[dict]) -> str:
    if not rows:
        return "<p>（未設定）</p>"
    parts = ['<ul class="hub-featured-live">']
    for row in rows:
        icon = row.get("icon")
        icon_html = (
            f'<span class="hub-featured-live__icon">'
            f'<img src="/assets/images/{html.escape(icon)}" alt="" width="56" height="56" loading="lazy">'
            f"</span>"
            if icon
            else '<span class="hub-featured-live__ph" aria-hidden="true">—</span>'
        )
        if row.get("missing"):
            parts.append(
                f'<li class="hub-featured-live__item hub-featured-live__item--warn">'
                f"{icon_html}<span>{html.escape(row['name'])}（未公開）</span></li>"
            )
            continue
        name = html.escape(row["name"])
        url = html.escape(row["url"])
        parts.append(
            f'<li class="hub-featured-live__item">'
            f'<a href="{url}">{icon_html}<span>{name}</span></a></li>'
        )
    parts.append("</ul>")
    return "\n".join(parts)


def update_sitemap() -> None:
    if not SITEMAP.is_file():
        return
    text = SITEMAP.read_text(encoding="utf-8")
    text = re.sub(
        r"\n  <url>\n    <loc>https://ai-master\.jp/docs/hub-featured/[^<]*</loc>[\s\S]*?</url>",
        "",
        text,
    )
    entry = f"""  <url>
    <loc>{SITE}/docs/hub-featured/</loc>
    <changefreq>monthly</changefreq>
    <priority>0.3</priority>
  </url>"""
    text = text.replace(
        "  <url>\n    <loc>https://ai-master.jp/legal/privacy.html</loc>",
        f"{entry}\n  <url>\n    <loc>https://ai-master.jp/legal/privacy.html</loc>",
        1,
    )
    SITEMAP.write_text(text, encoding="utf-8")


def main() -> None:
    sections = []
    for hub in HUBS:
        rows = lookup_items(hub)
        sections.append(
            f"""    <section class="tool-content-section">
      <h2>{html.escape(hub['label'])}</h2>
      <p><a href="{html.escape(hub['hub_url'])}">一覧を見る</a> · 設定: <code>data/{hub['key']}-featured.json</code></p>
      {render_featured_cards(rows)}
    </section>"""
        )

    body_sections = "\n".join(sections)
    page = f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="robots" content="noindex,nofollow">
  <meta name="description" content="AIマスター各一覧の「人気のページ」カードの運用。設定ファイル・公開中の記事リンク。">
  <title>人気カードの書き方 — AI Master</title>
  <link rel="canonical" href="{SITE}/docs/hub-featured/">
  <link rel="icon" href="/assets/images/favicon.svg" type="image/svg+xml">
  <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="../../assets/css/main.css">
  <link rel="stylesheet" href="../../assets/css/seo.css">
  <link rel="stylesheet" href="../../assets/css/tool-detail.css">
  <style>
    .hub-featured-live {{ list-style:none; padding:0; margin:16px 0 0; display:grid; gap:10px; }}
    .hub-featured-live__item a,
    .hub-featured-live__item {{ display:flex; align-items:center; gap:12px; padding:12px 14px; background:var(--surface-inset); border:1px solid var(--border-subtle); text-decoration:none; color:inherit; }}
    .hub-featured-live__item a:hover {{ background:var(--blue-soft); }}
    .hub-featured-live__icon {{ width:56px; height:56px; border-radius:12px; background:#fff; border:1px solid var(--gray-200); box-shadow:0 1px 4px rgba(15,23,42,.1); display:flex; align-items:center; justify-content:center; flex-shrink:0; overflow:hidden; }}
    .hub-featured-live__icon img {{ width:100%; height:100%; object-fit:contain; padding:4px; box-sizing:border-box; }}
    .hub-featured-live__icon:has(img[src*="tools/"]) img {{ width:72%; height:72%; padding:0; }}
    .hub-featured-live__ph {{ width:56px; text-align:center; color:var(--gray-400); flex-shrink:0; }}
    .hub-featured-live__item--warn {{ opacity:.85; }}
    .tool-content-section {{ margin-top:36px; }}
    .tool-content-section h2 {{ font-size:var(--text-xl); margin:0 0 8px; }}
    .tool-spec-table code {{ font-size:.9em; }}
  </style>
{SITE_GA4_HTML}{SITE_ADSENSE_HTML}</head>
<body class="page-body">
<nav class="site-nav">
  <a href="../../index.html" class="logo">AI<em>マスター</em></a>
  <ul class="nav-links">
    <li><a href="../../exams/">試験対策</a></li>
    <li><a href="../../guide/">学習ガイド</a></li>
    <li><a href="../../glossary/">用語辞典</a></li>
    <li><a href="../../tools/">AIツール</a></li>
    <li><a href="../../career/">キャリア</a></li>
  </ul>
</nav>
<main class="page-wrap page-wrap--article">
  <nav class="breadcrumb" aria-label="パンくずリスト">
    <ol>
      <li><a href="../../index.html">ホーム</a></li>
      <li aria-current="page">人気カードの書き方</li>
    </ol>
  </nav>
  <header class="tool-hero tool-hero--article">
    <p class="tool-hero-eyebrow">運用</p>
    <h1>人気カードの書き方</h1>
    <p class="tool-hero-sub">用語辞典 · 学習ガイド · キャリア共通</p>
  </header>
  <article class="tool-content">
    <p class="tool-lead">一覧上部の <strong>人気のページ</strong> に載る記事とアイコンの設定方法です。下のリンクから<strong>現在公開中の記事</strong>を確認できます。</p>

    <section>
      <h2>一覧ページ</h2>
      <ul class="tool-example-list">
        <li><a href="{SITE}/glossary/">用語辞典</a></li>
        <li><a href="{SITE}/guide/">学習ガイド</a></li>
        <li><a href="{SITE}/career/">キャリア</a></li>
      </ul>
    </section>

    <section>
      <h2>いま載っている記事</h2>
{body_sections}
    </section>

    <section>
      <h2>やること（2つ）</h2>
      <h3>1. 載せる記事を決める</h3>
      <p><code>*-featured.json</code> に記事IDを上から順に書く。</p>
      <table class="tool-spec-table">
        <thead><tr><th>ページ</th><th>ファイル</th></tr></thead>
        <tbody>
          <tr><td>用語辞典</td><td><code>data/glossary-featured.json</code></td></tr>
          <tr><td>学習ガイド</td><td><code>data/guide-featured.json</code></td></tr>
          <tr><td>キャリア</td><td><code>data/career-featured.json</code></td></tr>
        </tbody>
      </table>
      <h3>2. ビルド</h3>
      <pre class="tool-code-block"><code>python3 tools/build_glossary.py
python3 tools/build_guide_index.py
python3 tools/rebuild_career.py
python3 tools/build_hub_featured_doc.py</code></pre>
    </section>

    <section>
      <h2>アイコン</h2>
      <p>画像を置けば自動。例外だけ <code>data/hub-icon-aliases.json</code>。</p>
      <table class="tool-spec-table">
        <thead><tr><th>ページ</th><th>記事用</th><th>共通</th></tr></thead>
        <tbody>
          <tr><td>用語辞典</td><td><code>assets/images/glossary/{{ID}}.svg</code></td><td><code>glossary/categories/</code></td></tr>
          <tr><td>学習ガイド</td><td><code>assets/images/guide/{{ID}}/icon.svg</code></td><td><code>guide/categories/</code></td></tr>
          <tr><td>キャリア</td><td><code>assets/images/career/{{ID}}/icon.svg</code></td><td><code>career/categories/</code></td></tr>
        </tbody>
      </table>
    </section>
  </article>
</main>
<footer>
  <div class="foot-inner">
    <p class="foot-disclaimer">G検定は（社）日本ディープラーニング協会の登録商標です。生成AIパスポートは一般社団法人グロービスの商標です。当サイトは各試験の公式サイトではありません。</p>
    <div class="foot-bottom">
      <span>© 2026 AIマスター. All rights reserved.</span>
      <span class="foot-legal"><a href="../../legal/privacy.html">プライバシーポリシー</a> · <a href="../../legal/terms.html">利用規約</a></span>
    </div>
  </div>
</footer>
</body>
</html>
"""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(page, encoding="utf-8")
    update_sitemap()
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
