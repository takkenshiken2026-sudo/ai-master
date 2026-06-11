#!/usr/bin/env python3
"""data/glossary-terms.csv から用語辞典の静的 HTML と sitemap エントリを生成する。

使い方:
  python3 tools/build_glossary.py              # 一覧 + sitemap 更新
  python3 tools/build_glossary.py --scaffold llm  # 用語詳細の雛形を追加
  python3 tools/build_glossary.py --sync-json    # CSV → JSON 同期のみ
"""

from __future__ import annotations

import argparse
import html
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from glossary_terms import load_terms_csv, sync_json_from_csv, terms_to_json_payload  # noqa: E402
from site_meta import SITE_GA4_HTML  # noqa: E402
GLOSSARY_INDEX = ROOT / "glossary" / "index.html"
SITEMAP = ROOT / "sitemap.xml"
SITE_ORIGIN = "https://ai-master.jp"

FEATURED_JSON = ROOT / "data" / "glossary-featured.json"
ICON_ALIASES_JSON = ROOT / "data" / "glossary-icon-aliases.json"
GLOSSARY_IMG = ROOT / "assets/images" / "glossary"

PREFIX_VENDOR = (
    ("claude-", "Anthropic"),
    ("gpt-", "OpenAI"),
    ("gemini-", "Google"),
)

PER_PAGE = 100
INDEX_JSON = ROOT / "data" / "glossary-index.json"

TAG_CLASS = {
    "basics": "tag-basics",
    "models-tech": "tag-models-tech",
    "genai-use": "tag-genai-use",
    "data-ops": "tag-data-ops",
    "governance": "tag-governance",
}

CHEVRON = (
    '<svg class="term-chevron" viewBox="0 0 16 16" fill="none" '
    'stroke="currentColor" stroke-width="1.5" aria-hidden="true">'
    '<path d="M6 4l4 4-4 4" stroke-linecap="round" stroke-linejoin="round"/>'
    "</svg>"
)


def load_data() -> dict:
    terms = load_terms_csv()
    if not terms:
        raise SystemExit(
            "data/glossary-terms.csv がありません。"
            " python3 tools/seed_glossary_terms.py を実行してください。"
        )
    return terms_to_json_payload(terms)


def sort_terms_jp(terms: list[dict]) -> list[dict]:
    def key(t: dict) -> tuple:
        sk = t.get("sortKey") or t.get("name", "")
        is_kana = bool(re.match(r"^[ぁ-ん]", sk))
        return (0 if is_kana else 1, t.get("name", ""))

    return sorted(terms, key=key)


def sort_terms_az(terms: list[dict]) -> list[dict]:
    return sorted(terms, key=lambda t: (t.get("yomi") or t.get("name", "")).lower())


def term_has_page(term: dict) -> bool:
    """静的 HTML が存在する用語だけリンク・sitemap 対象にする。"""
    return (ROOT / "glossary" / term["id"] / "index.html").is_file()


def load_featured_ids() -> list[str]:
    if not FEATURED_JSON.is_file():
        return []
    return json.loads(FEATURED_JSON.read_text(encoding="utf-8"))


def load_icon_aliases() -> dict:
    if not ICON_ALIASES_JSON.is_file():
        return {"vendors": {}, "terms": {}}
    data = json.loads(ICON_ALIASES_JSON.read_text(encoding="utf-8"))
    return {
        "vendors": data.get("vendors") or {},
        "terms": data.get("terms") or {},
    }


def _glossary_image_rel(path: Path) -> str | None:
    try:
        rel = path.relative_to(ROOT / "assets" / "images")
    except ValueError:
        return None
    return rel.as_posix()


def resolve_glossary_icon(term_id: str, csv_row: dict, aliases: dict) -> str | None:
    """人気カード用アイコンを解決。詳細は data/GLOSSARY-FEATURED.md。"""
    terms_map = aliases.get("terms") or {}
    if term_id in terms_map:
        return terms_map[term_id]

    for ext in (".svg", ".png", ".webp"):
        candidate = GLOSSARY_IMG / f"{term_id}{ext}"
        if candidate.is_file():
            return _glossary_image_rel(candidate)

    notes = csv_row.get("notes") or ""
    vendor_match = re.search(r"開発元:\s*(.+)", notes)
    vendors = aliases.get("vendors") or {}
    if vendor_match:
        vendor = vendor_match.group(1).strip()
        if vendor in vendors:
            return vendors[vendor]

    for prefix, vendor in PREFIX_VENDOR:
        if term_id.startswith(prefix) and vendor in vendors:
            return vendors[vendor]

    category = csv_row.get("category") or ""
    for ext in (".svg", ".png", ".webp"):
        candidate = GLOSSARY_IMG / "categories" / f"{category}{ext}"
        if candidate.is_file():
            return _glossary_image_rel(candidate)

    return None


def build_featured_payload(csv_by_id: dict[str, dict]) -> tuple[list[str], list[dict]]:
    aliases = load_icon_aliases()
    featured: list[dict] = []
    for term_id in load_featured_ids():
        csv_row = csv_by_id.get(term_id)
        if not csv_row:
            print(f"warn: featured term not in CSV: {term_id}")
            continue
        if not term_has_page({"id": term_id}):
            print(f"warn: featured term has no page: {term_id}")
            continue
        item: dict = {"id": term_id}
        icon = resolve_glossary_icon(term_id, csv_row, aliases)
        if icon:
            item["icon"] = icon
        featured.append(item)
    return [item["id"] for item in featured], featured


def render_term_row(term: dict, categories: dict) -> str:
    cat_label = categories.get(term["category"], term["category"])
    tag_cls = TAG_CLASS.get(term["category"], "tag-basics")
    name = html.escape(term["name"])
    yomi = html.escape(term.get("yomi") or "")
    published = term_has_page(term)

    inner = f"""        <div class="term-main">
          <div class="term-name">{name}</div>
          <div class="term-yomi">{yomi}</div>
        </div>
        <span class="term-tag {tag_cls}">{html.escape(cat_label)}</span>
        {CHEVRON}"""

    if published:
        href = html.escape(f"{term['id']}/")
        return (
            f'      <li class="term-row">\n'
            f'        <a href="{href}" class="term-row-link">\n{inner}\n'
            f"        </a>\n"
            f"      </li>"
        )

    return (
        f'      <li class="term-row term-row--planned">\n'
        f'        <div class="term-row-link" aria-disabled="true">\n{inner}\n'
        f"        </div>\n"
        f"      </li>"
    )


def write_index_json(data: dict, csv_by_id: dict[str, dict]) -> None:
    categories = data["categories"]
    terms = data["terms"]
    featured_ids, featured = build_featured_payload(csv_by_id)
    payload = {
        "categories": categories,
        "featuredIds": featured_ids,
        "featured": featured,
        "terms": [
            {
                "id": t["id"],
                "name": t["name"],
                "yomi": t.get("yomi") or "",
                "summary": t.get("summary") or "",
                "category": t["category"],
                "sortKey": t.get("sortKey") or t["name"][:1],
                "published": term_has_page(t),
            }
            for t in terms
        ],
    }
    INDEX_JSON.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"wrote {INDEX_JSON.relative_to(ROOT)}")


def build_index_html(data: dict) -> str:
    categories = data["categories"]
    terms = data["terms"]
    published_count = sum(1 for t in terms if term_has_page(t))

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="description" content="G検定・生成AIパスポートの学習に役立つAI用語辞典。生成AI、LLM、プロンプトなど、わかりやすく解説した用語集を掲載しています。">
  <title>AI用語辞典 — AI Master</title>
  <link rel="canonical" href="{SITE_ORIGIN}/glossary/">
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="AI Master">
  <meta property="og:title" content="AI用語辞典 — AI Master">
  <meta property="og:description" content="G検定・生成AIパスポートの学習に役立つAI用語辞典。">
  <meta property="og:url" content="{SITE_ORIGIN}/glossary/">
  <meta property="og:locale" content="ja_JP">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@500;600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="../assets/css/main.css">
  <link rel="stylesheet" href="../assets/css/hub.css">
  <link rel="stylesheet" href="../assets/css/seo.css">
  <link rel="stylesheet" href="../assets/css/glossary.css">
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@graph": [
      {{
        "@type": "BreadcrumbList",
        "itemListElement": [
          {{ "@type": "ListItem", "position": 1, "name": "ホーム", "item": "{SITE_ORIGIN}/" }},
          {{ "@type": "ListItem", "position": 2, "name": "用語辞典", "item": "{SITE_ORIGIN}/glossary/" }}
        ]
      }},
      {{
        "@type": "CollectionPage",
        "name": "AI用語辞典",
        "description": "G検定・生成AIパスポートの学習に役立つAI用語辞典",
        "url": "{SITE_ORIGIN}/glossary/",
        "isPartOf": {{ "@id": "{SITE_ORIGIN}/#website" }},
        "inLanguage": "ja"
      }},
      {{
        "@type": "DefinedTermSet",
        "name": "AI Master 用語辞典",
        "url": "{SITE_ORIGIN}/glossary/"
      }}
    ]
  }}
  </script>
{SITE_GA4_HTML}</head>
<body class="page-body">

<nav class="site-nav">
  <a href="../index.html" class="logo">AI<em>マスター</em></a>
  <ul class="nav-links">
    <li><a href="../exams/">試験対策</a></li>
    <li><a href="index.html" class="active">用語辞典</a></li>
    <li><a href="../tools/">AIツール</a></li>
    <li><a href="../career/">キャリア</a></li>
  </ul>
</nav>

<main class="page-wrap page-wrap--article">
  <nav class="breadcrumb" aria-label="パンくずリスト">
    <ol>
      <li><a href="../index.html">ホーム</a></li>
      <li aria-current="page">用語辞典</li>
    </ol>
  </nav>

  <header class="hub-header">
    <h1>AI用語辞典</h1>
    <p class="hub-intro">G検定・生成AIパスポートの学習に役立つAI用語を、わかりやすく解説しています。カテゴリで絞り込みながら調べられます。解説記事のある用語から順次公開しています（未公開は「準備中」でクリックできません）。</p>
    <div class="search-wrap hub-search">
      <svg class="search-icon" width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">
        <circle cx="6.5" cy="6.5" r="4.5"/><path d="M10.5 10.5l3 3" stroke-linecap="round"/>
      </svg>
      <input type="search" id="glossarySearchInput" placeholder="用語・読み・説明文を検索（Enterで実行）…" autocomplete="off" enterkeyhint="search">
    </div>
  </header>

  <div class="hub-filter-row" id="glossaryCategoryFilters" aria-label="カテゴリで絞り込み"></div>

  <section class="hub-featured" id="glossaryFeatured">
    <p class="hub-featured-label">人気のページ</p>
    <div class="hub-featured-grid" id="glossaryFeaturedGrid"></div>
  </section>

  <div class="hub-meta-row">
    <div>
      <p class="hub-result-meta" id="glossaryResultMeta">{len(terms)}件（解説公開 {published_count}件 · 準備中 {len(terms) - published_count}件）</p>
      <p class="hub-result-range" id="glossaryResultRange"></p>
    </div>
    <div class="hub-sort-wrap">
      <label for="glossarySortSelect">並び順</label>
      <select id="glossarySortSelect">
        <option value="alpha">五十音順</option>
        <option value="az">A-Z順</option>
      </select>
    </div>
  </div>

  <ul class="hub-list" id="termList" aria-label="用語一覧">
    <li class="hub-empty" aria-live="polite">読み込み中…</li>
  </ul>

  <nav class="hub-pagination" id="glossaryPagination" aria-label="ページ送り"></nav>
</main>

<footer>
  <div class="foot-inner">
    <div class="foot-top">
      <div>
        <div class="foot-logo">AI<em>マスター</em></div>
        <p class="foot-tagline">AIスキルを、キャリアの武器に。</p>
      </div>
      <div class="foot-cols">
        <div class="foot-col">
          <p class="foot-col-h">学ぶ</p>
          <a href="index.html">AI用語辞典</a>
          <a href="../tools/">AIツール</a>
        </div>
        <div class="foot-col">
          <p class="foot-col-h">試験対策</p>
          <a href="../exams/g-kentei/">G検定対策</a>
          <a href="../exams/genai-passport/">生成AIパスポート対策</a>
          <a href="../exams/">資格一覧</a>
        </div>
        <div class="foot-col">
          <p class="foot-col-h">キャリア</p>
          <a href="../career/">AI職種ガイド</a>
        </div>
      </div>
    </div>
    <p class="foot-disclaimer">G検定は（社）日本ディープラーニング協会の登録商標です。生成AIパスポートは一般社団法人グロービスの商標です。当サイトは各試験の公式サイトではありません。</p>
    <div class="foot-bottom">
      <span>© 2026 AIマスター. All rights reserved.</span>
      <span class="foot-legal">
        <a href="../legal/privacy.html">プライバシーポリシー</a>
        ·
        <a href="../legal/terms.html">利用規約</a>
      </span>
    </div>
  </div>
</footer>

<script src="../assets/js/hub-list-nav.js" defer></script>
<script src="../assets/js/glossary-list.js" defer></script>
</body>
</html>
"""


def scaffold_term_page(term: dict, categories: dict) -> None:
    term_dir = ROOT / "glossary" / term["id"]
    out = term_dir / "index.html"
    if out.is_file():
        print(f"skip scaffold (exists): {out.relative_to(ROOT)}")
        return

    cat_label = categories.get(term["category"], "")
    title = term.get("title") or f"{term['name']}とは？意味をわかりやすく解説"
    description = term.get("description") or term.get("summary", "")
    name = html.escape(term["name"])
    yomi = html.escape(term.get("yomi") or "")
    summary = html.escape(term.get("summary") or "")
    cat = html.escape(cat_label)
    slug = term["id"]
    url = f"{SITE_ORIGIN}/glossary/{slug}/"

    content = f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="description" content="{html.escape(description)}">
  <title>{html.escape(title)} — AI Master</title>
  <link rel="canonical" href="{url}">
  <meta property="og:type" content="article">
  <meta property="og:site_name" content="AI Master">
  <meta property="og:title" content="{html.escape(title)}">
  <meta property="og:description" content="{html.escape(description)}">
  <meta property="og:url" content="{url}">
  <meta property="og:locale" content="ja_JP">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="../../assets/css/main.css">
  <link rel="stylesheet" href="../../assets/css/seo.css">
  <link rel="stylesheet" href="../../assets/css/tool-detail.css">
{SITE_GA4_HTML}</head>
<body class="page-body">

<nav class="site-nav">
  <a href="../../index.html" class="logo">AI<em>マスター</em></a>
  <ul class="nav-links">
    <li><a href="../../exams/">試験対策</a></li>
    <li><a href="../index.html" class="active">用語辞典</a></li>
    <li><a href="../../tools/">AIツール</a></li>
    <li><a href="../../career/">キャリア</a></li>
  </ul>
</nav>

<main class="page-wrap page-wrap--article">
  <nav class="breadcrumb" aria-label="パンくずリスト">
    <ol>
      <li><a href="../../index.html">ホーム</a></li>
      <li><a href="../index.html">用語辞典</a></li>
      <li aria-current="page">{name}</li>
    </ol>
  </nav>

  <header class="tool-hero tool-hero--article">
    <p class="tool-hero-eyebrow">{cat}</p>
    <h1>{html.escape(title)}</h1>
    <p class="tool-hero-sub">読み：{yomi}</p>
  </header>

  <article class="tool-content">
    <p class="tool-lead">{summary} この用語の詳細記事は現在準備中です。一覧に戻るか、関連する<strong>生成AI</strong>の解説記事をご覧ください。</p>
    <p><a href="../generative-ai/">生成AIの解説記事へ</a> · <a href="../index.html">用語辞典一覧へ</a></p>
  </article>
</main>

<footer>
  <div class="foot-inner">
    <p class="foot-disclaimer">G検定は（社）日本ディープラーニング協会の登録商標です。生成AIパスポートは一般社団法人グロービスの商標です。当サイトは各試験の公式サイトではありません。</p>
    <div class="foot-bottom">
      <span>© 2026 AIマスター. All rights reserved.</span>
      <span class="foot-legal">
        <a href="../../legal/privacy.html">プライバシーポリシー</a>
        ·
        <a href="../../legal/terms.html">利用規約</a>
      </span>
    </div>
  </div>
</footer>

</body>
</html>
"""
    term_dir.mkdir(parents=True, exist_ok=True)
    out.write_text(content, encoding="utf-8")
    print(f"wrote scaffold: {out.relative_to(ROOT)}")


def update_sitemap(data: dict) -> None:
    if not SITEMAP.is_file():
        print("skip sitemap: file not found")
        return

    text = SITEMAP.read_text(encoding="utf-8")
    text = re.sub(
        r"\n  <url>\n    <loc>https://ai-master\.jp/glossary/[^<]*</loc>[\s\S]*?</url>",
        "",
        text,
    )

    entries = [
        f"""  <url>
    <loc>{SITE_ORIGIN}/glossary/</loc>
    <changefreq>weekly</changefreq>
    <priority>0.9</priority>
  </url>"""
    ]
    for term in data["terms"]:
        if not term_has_page(term):
            continue
        loc = f"{SITE_ORIGIN}/glossary/{term['id']}/"
        entries.append(
            f"""  <url>
    <loc>{loc}</loc>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>"""
        )

    insert = "\n".join(entries)
    text = text.replace(
        "  <url>\n    <loc>https://ai-master.jp/tools/</loc>",
        f"{insert}\n  <url>\n    <loc>https://ai-master.jp/tools/</loc>",
        1,
    )
    SITEMAP.write_text(text, encoding="utf-8")
    print(f"updated {SITEMAP.relative_to(ROOT)}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scaffold", metavar="ID", help="用語詳細ページの雛形を生成")
    parser.add_argument("--sync-json", action="store_true", help="CSV から glossary-terms.json を更新")
    args = parser.parse_args()

    if args.sync_json:
        sync_json_from_csv()
        print("synced data/glossary-terms.json")
        return

    data = load_data()
    categories = data["categories"]
    csv_by_id = {row["id"]: row for row in load_terms_csv()}

    if args.scaffold:
        term = next((t for t in data["terms"] if t["id"] == args.scaffold), None)
        if not term:
            raise SystemExit(f"unknown term id: {args.scaffold}")
        scaffold_term_page(term, categories)
        return

    write_index_json(data, csv_by_id)
    GLOSSARY_INDEX.write_text(build_index_html(data), encoding="utf-8")
    print(f"wrote {GLOSSARY_INDEX.relative_to(ROOT)}")
    subprocess.run(
        [sys.executable, str(ROOT / "tools" / "build_hub_static_lists.py")],
        check=True,
        cwd=str(ROOT),
    )
    update_sitemap(data)


if __name__ == "__main__":
    main()
