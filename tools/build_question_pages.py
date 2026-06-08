#!/usr/bin/env python3
"""問題 JSON から SEO 用の静的 HTML（1問1ページ・分野一覧）を生成する。

使い方:
  python3 tools/build_question_pages.py
  python3 tools/build_question_pages.py --exam g-kentei --mode drill
"""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from site_meta import SITE_ICONS_HTML, SITE_ORIGIN, render_og_meta
SITEMAP = ROOT / "sitemap.xml"
INDEX_JSON = ROOT / "data" / "question-index.json"
GLOSSARY_TERMS_JSON = ROOT / "data" / "glossary-terms.json"

EXAMS = {
    "g-kentei": {
        "label": "G検定",
        "data_dir": "g-kentei",
        "modes": {
            "drill": {
                "label": "一問一答",
                "json": "assets/data/g-kentei/drill.json",
                "kind": "drill",
            },
            "practice": {
                "label": "実践演習",
                "json": "assets/data/g-kentei/practice.json",
                "kind": "choice",
            },
        },
    },
    "genai-passport": {
        "label": "生成AIパスポート",
        "data_dir": "genai-passport",
        "modes": {
            "drill": {
                "label": "一問一答",
                "json": "assets/data/genai-passport/drill.json",
                "kind": "drill",
            },
            "practice": {
                "label": "実践演習",
                "json": "assets/data/genai-passport/practice.json",
                "kind": "choice",
            },
        },
    },
}

FOOTER = """    <p class="foot-disclaimer">G検定は（社）日本ディープラーニング協会の登録商標です。生成AIパスポートは一般社団法人グロービスの商標です。当サイトは各試験の公式サイトではありません。</p>
    <div class="foot-bottom">
      <span>© 2026 AIマスター. All rights reserved.</span>
      <span class="foot-legal">
        <a href="{legal}privacy.html">プライバシーポリシー</a>
        ·
        <a href="{legal}terms.html">利用規約</a>
      </span>
    </div>"""


def id_slug(question_id: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", question_id.lower()).strip("-")


def domain_sort_key(domain: str) -> tuple:
    m = re.match(r"第(\d+)章", domain)
    if m:
        return (0, int(m.group(1)), domain)
    return (1, 0, domain)


def build_domain_slugs(domains: list[str]) -> dict[str, str]:
    ordered = sorted(set(domains), key=domain_sort_key)
    slugs: dict[str, str] = {}
    used: set[str] = set()
    for i, domain in enumerate(ordered, 1):
        m = re.match(r"第(\d+)章", domain)
        if m:
            slug = f"chapter-{int(m.group(1)):02d}"
        else:
            slug = f"domain-{i:02d}"
        base = slug
        n = 2
        while slug in used:
            slug = f"{base}-{n}"
            n += 1
        used.add(slug)
        slugs[domain] = slug
    return slugs


def rel_to_root(depth: int) -> str:
    return "../" * depth


def trim_text(text: str, limit: int = 118) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


def seo_hub_title(exam_label: str, mode_label: str) -> str:
    return f"{exam_label} 過去問想定 {mode_label} 問題一覧 — AIマスター"


def seo_hub_description(exam_label: str, mode_label: str, count: int) -> str:
    return trim_text(
        f"{exam_label}の本番・過去問を想定した{mode_label}の模擬問題（全{count}問）。"
        "公式の過去問ではなく、分野別に解説付きで掲載。"
    )


def seo_domain_title(exam_label: str, mode_label: str, domain: str) -> str:
    return f"{exam_label} 過去問想定 {mode_label} {domain} — AIマスター"


def seo_domain_description(
    exam_label: str, mode_label: str, domain: str, count: int
) -> str:
    return trim_text(
        f"{exam_label}の過去問を想定した{mode_label}「{domain}」の模擬問題（{count}問）。解説付き。"
    )


def seo_question_title(exam_label: str, mode_label: str, qid: str, topic: str) -> str:
    return f"【{exam_label} 過去問想定 {mode_label}】{qid} · {topic} — AIマスター"


def seo_question_description(
    exam_label: str, mode_label: str, topic: str, prompt: str
) -> str:
    return trim_text(
        f"{exam_label}の過去問を想定した{mode_label}（{topic}）。"
        f"{prompt or ''} 模擬問題・解説付き。"
    )


def seo_hub_intro(exam_label: str, mode_label: str, count: int) -> str:
    return (
        f"本番・過去問を想定した模擬問題を全{count}問、分野別に掲載しています"
        "（公式の過去問ではありません）。演習は"
    )


def seo_question_intro(exam_label: str, mode_label: str) -> str:
    return (
        f"{exam_label}の過去問を想定した{mode_label}の模擬問題です。"
        "解説付きで個別に学習できます。"
    )


def load_questions(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("questions") or []


def validate_questions(questions: list[dict], kind: str) -> None:
    ids = [q.get("id") for q in questions]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate question id detected")
    slugs = [id_slug(i) for i in ids]
    if len(slugs) != len(set(slugs)):
        raise ValueError("duplicate question slug detected")
    required = (
        ["id", "domain", "topic", "statement", "answer", "explanation"]
        if kind == "drill"
        else ["id", "domain", "topic", "question", "choices", "answer", "explanation"]
    )
    for q in questions:
        for key in required:
            if not q.get(key):
                raise ValueError(f"missing field {key} in question {q.get('id')}")


def render_nav(rel: str, exams_active: bool = True) -> str:
    active = ' class="active"' if exams_active else ""
    return f"""<nav class="site-nav">
  <a href="{rel}index.html" class="logo">AI<em>マスター</em></a>
  <ul class="nav-links">
    <li><a href="{rel}exams/"{active}>試験対策</a></li>
    <li><a href="{rel}glossary/">用語辞典</a></li>
    <li><a href="{rel}tools/">AIツール</a></li>
    <li><a href="{rel}career/">キャリア</a></li>
  </ul>
</nav>"""


def render_footer(rel: str) -> str:
    return FOOTER.format(legal=f"{rel}legal/")


def page_shell(
    *,
    rel: str,
    title: str,
    description: str,
    canonical: str,
    breadcrumb_html: str,
    body_html: str,
    json_ld: dict | None = None,
    css_depth: int = 4,
    og_type: str = "website",
) -> str:
    css = rel_to_root(css_depth) + "assets/css/"
    json_block = ""
    if json_ld:
        json_block = (
            f'  <script type="application/ld+json">\n'
            f"{json.dumps(json_ld, ensure_ascii=False, indent=2)}\n"
            f"  </script>\n"
        )
    esc_title = html.escape(title)
    esc_desc = html.escape(description)
    og_block = render_og_meta(title, description, canonical, og_type=og_type)
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="description" content="{esc_desc}">
  <title>{esc_title}</title>
  <link rel="canonical" href="{canonical}">
{SITE_ICONS_HTML}{og_block}  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@500;600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="{css}main.css">
  <link rel="stylesheet" href="{css}hub.css">
  <link rel="stylesheet" href="{css}seo.css">
  <link rel="stylesheet" href="{css}question-detail.css">
{json_block}</head>
<body class="page-body">

{render_nav(rel_to_root(css_depth))}

<main class="page-wrap page-wrap--article">
{breadcrumb_html}
{body_html}
</main>

<footer>
  <div class="foot-inner">
{render_footer(rel_to_root(css_depth))}
  </div>
</footer>

</body>
</html>
"""


def breadcrumb(items: list[tuple[str, str | None]]) -> str:
  lines = ['  <nav class="breadcrumb" aria-label="パンくずリスト">', "    <ol>"]
  for label, href in items:
      if href:
          lines.append(f'      <li><a href="{html.escape(href)}">{html.escape(label)}</a></li>')
      else:
          lines.append(f'      <li aria-current="page">{html.escape(label)}</li>')
  lines.extend(["    </ol>", "  </nav>"])
  return "\n".join(lines)


def load_published_glossary() -> list[tuple[str, str]]:
    if not GLOSSARY_TERMS_JSON.is_file():
        return []
    data = json.loads(GLOSSARY_TERMS_JSON.read_text(encoding="utf-8"))
    terms: list[tuple[str, str]] = []
    for term in data.get("terms") or []:
        tid = term.get("id")
        name = term.get("name")
        if not tid or not name:
            continue
        if (ROOT / "glossary" / tid / "index.html").is_file():
            terms.append((name, tid))
    terms.sort(key=lambda x: len(x[0]), reverse=True)
    return terms


def match_glossary_terms(
    text: str, glossary: list[tuple[str, str]], limit: int = 6
) -> list[tuple[str, str]]:
    matched: list[tuple[str, str]] = []
    seen: set[str] = set()
    for name, tid in glossary:
        if len(name) < 2 or tid in seen:
            continue
        if name in text:
            matched.append((name, tid))
            seen.add(tid)
        if len(matched) >= limit:
            break
    return matched


def render_question_header(q: dict, exam_label: str, mode_label: str) -> str:
    topic = html.escape(q.get("topic") or "")
    intro = html.escape(seo_question_intro(exam_label, mode_label))
    return f"""  <header class="hub-header hub-header--question">
    <h1>{topic}</h1>
    <p class="hub-intro">{intro}</p>
  </header>"""


def render_meta_pills(q: dict, domain_slug: str) -> str:
    domain = html.escape(q.get("domain", ""))
    return f"""  <div class="question-page__meta">
    <a class="question-page__pill question-page__pill--link" href="../../domain/{domain_slug}/">{domain}</a>
    <span class="question-page__pill question-page__pill--muted">{html.escape(q.get("difficulty", ""))}</span>
    <span class="question-page__pill question-page__pill--muted">ID: {html.escape(q.get("id", ""))}</span>
  </div>"""


def render_related_section(
    q: dict,
    *,
    exam_id: str,
    exam_label: str,
    mode_label: str,
    domain_slug: str,
    by_domain: dict[str, list[dict]],
    glossary: list[tuple[str, str]],
    rel_root: str,
) -> str:
    domain = q.get("domain", "")
    topic = q.get("topic", "")
    text = " ".join(
        filter(
            None,
            [topic, q.get("statement") or q.get("question") or "", q.get("explanation") or ""],
        )
    )

    keyword_links: list[tuple[str, str]] = [
        (exam_label, f"{rel_root}exams/{exam_id}/"),
        (mode_label, "../../"),
        (domain, f"../../domain/{domain_slug}/"),
        ("問題一覧", "../../questions/"),
        ("用語辞典", f"{rel_root}glossary/"),
    ]
    for name, tid in match_glossary_terms(text, glossary):
        keyword_links.append((name, f"{rel_root}glossary/{tid}/"))

    pills: list[str] = []
    seen_href: set[str] = set()
    for label, href in keyword_links:
        if href in seen_href:
            continue
        seen_href.add(href)
        pills.append(
            f'<a class="question-page__pill question-page__pill--link" '
            f'href="{html.escape(href)}">{html.escape(label)}</a>'
        )

    siblings = [
        item
        for item in by_domain.get(domain, [])
        if item.get("topic") == topic and item["id"] != q["id"]
    ][:5]
    sibling_html = ""
    if siblings:
        items = []
        for item in siblings:
            qs = id_slug(item["id"])
            items.append(
                f'      <li><a href="../{qs}/">'
                f'{html.escape(item.get("id", qs))} · {html.escape(topic)}</a></li>'
            )
        sibling_html = f"""
    <h3 class="question-page__related-sub">同じトピックの問題</h3>
    <ul class="question-page__related-list">
{chr(10).join(items)}
    </ul>"""

    return f"""  <section class="question-page__related" aria-label="関連キーワード">
    <h2 class="question-page__related-title">関連キーワード</h2>
    <div class="question-page__keywords">
      {"".join(pills)}
    </div>{sibling_html}
  </section>"""


def render_drill_body(q: dict, exam_label: str, mode_label: str, domain_slug: str) -> str:
    statement = html.escape(q["statement"])
    answer = html.escape(q["answer"])
    explanation = html.escape(q["explanation"])
    return f"""{render_question_header(q, exam_label, mode_label)}
{render_meta_pills(q, domain_slug)}
  <article class="question-page__card">
    <h2 class="question-page__section-title">問題</h2>
    <p class="question-page__prompt">{statement}</p>
    <p class="question-page__answer-row">正解: {answer}</p>
  </article>
  <article class="question-page__card">
    <h2 class="question-page__section-title">解説</h2>
    <p class="question-page__explanation">{explanation}</p>
  </article>"""


def render_choice_body(q: dict, exam_label: str, mode_label: str, domain_slug: str) -> str:
    prompt = html.escape(q["question"])
    answer = q["answer"].upper()
    choices = q.get("choices") or {}
    choice_items = []
    for key in ("A", "B", "C", "D"):
        label = html.escape(choices.get(key, ""))
        cls = "question-page__choice"
        if key == answer:
            cls += " question-page__choice--answer"
        choice_items.append(f'      <li class="{cls}">{key}. {label}</li>')
    choices_html = "\n".join(choice_items)
    explanation = html.escape(q["explanation"])
    return f"""{render_question_header(q, exam_label, mode_label)}
{render_meta_pills(q, domain_slug)}
  <article class="question-page__card">
    <h2 class="question-page__section-title">問題</h2>
    <p class="question-page__prompt">{prompt}</p>
    <ol class="question-page__choices">
{choices_html}
    </ol>
  </article>
  <article class="question-page__card">
    <h2 class="question-page__section-title">解説（正解: {html.escape(answer)}）</h2>
    <p class="question-page__explanation">{explanation}</p>
  </article>"""


def render_question_actions(
    player_href: str, prev_href: str | None, next_href: str | None
) -> str:
    prev_link = (
        f'<a class="btn-ghost" href="{html.escape(prev_href)}">前の問題</a>'
        if prev_href
        else ""
    )
    next_link = (
        f'<a class="btn-ghost" href="{html.escape(next_href)}">次の問題</a>'
        if next_href
        else ""
    )
    return f"""  <div class="question-page__actions">
    <a class="btn-solid" href="{html.escape(player_href)}">演習モードで解く</a>
    {prev_link}
    {next_link}
  </div>"""


def build_mode(
    exam_id: str,
    exam_cfg: dict,
    mode_id: str,
    mode_cfg: dict,
) -> tuple[list[str], dict]:
    json_path = ROOT / mode_cfg["json"]
    questions = load_questions(json_path)
    validate_questions(questions, mode_cfg["kind"])

    base_dir = ROOT / "exams" / exam_id / mode_id
    q_root = base_dir / "q"
    domain_root = base_dir / "domain"
    questions_hub = base_dir / "questions"

    if q_root.exists():
        shutil.rmtree(q_root)
    if domain_root.exists():
        shutil.rmtree(domain_root)
    if questions_hub.exists():
        shutil.rmtree(questions_hub)

    domains = [q["domain"] for q in questions]
    domain_slugs = build_domain_slugs(domains)

    by_domain: dict[str, list[dict]] = {}
    for q in questions:
        by_domain.setdefault(q["domain"], []).append(q)

    for domain in by_domain:
        by_domain[domain].sort(key=lambda x: (x.get("no") if isinstance(x.get("no"), int) else str(x.get("no"))))

    sitemap_urls: list[str] = []
    index_entries: list[dict] = []

    exam_label = exam_cfg["label"]
    mode_label = mode_cfg["label"]
    rel_hub = rel_to_root(4)

    # questions hub
    domain_cards = []
    for domain in sorted(by_domain.keys(), key=domain_sort_key):
        slug = domain_slugs[domain]
        count = len(by_domain[domain])
        domain_cards.append(
            f"""      <a class="question-domain-card" href="../domain/{slug}/">
        <strong>{html.escape(domain)}</strong>
        <span>{count}問</span>
      </a>"""
        )
    hub_intro = seo_hub_intro(exam_label, mode_label, len(questions))
    hub_body = f"""  <header class="hub-header">
    <h1>{html.escape(exam_label)} 過去問想定 {html.escape(mode_label)} 問題一覧</h1>
    <p class="hub-intro">{html.escape(hub_intro)}<a href="../">演習モード</a>をご利用ください。</p>
  </header>
  <div class="question-domain-grid">
{chr(10).join(domain_cards)}
  </div>"""
    hub_path = questions_hub / "index.html"
    hub_path.parent.mkdir(parents=True, exist_ok=True)
    hub_canonical = f"{SITE_ORIGIN}/exams/{exam_id}/{mode_id}/questions/"
    hub_breadcrumb = breadcrumb(
        [
            ("ホーム", f"{rel_hub}index.html"),
            ("試験対策", f"{rel_hub}exams/"),
            (exam_label, f"{rel_hub}exams/{exam_id}/"),
            (mode_label, "../"),
            ("問題一覧", None),
        ]
    )
    hub_path.write_text(
        page_shell(
            rel=rel_hub,
            title=seo_hub_title(exam_label, mode_label),
            description=seo_hub_description(exam_label, mode_label, len(questions)),
            canonical=hub_canonical,
            breadcrumb_html=hub_breadcrumb,
            body_html=hub_body,
            css_depth=4,
        ),
        encoding="utf-8",
    )
    sitemap_urls.append(hub_canonical)

    ordered_all: list[dict] = []
    for domain in sorted(by_domain.keys(), key=domain_sort_key):
        ordered_all.extend(by_domain[domain])

    slug_to_index = {id_slug(q["id"]): i for i, q in enumerate(ordered_all)}

    for domain in sorted(by_domain.keys(), key=domain_sort_key):
        slug = domain_slugs[domain]
        domain_questions = by_domain[domain]
        list_items = []
        for q in domain_questions:
            qs = id_slug(q["id"])
            topic = html.escape(q.get("topic") or qs)
            list_items.append(f'      <li><a href="../../q/{qs}/">{topic}</a></li>')
        domain_body = f"""  <header class="hub-header">
    <h1>{html.escape(domain)}</h1>
    <p class="hub-intro">{html.escape(exam_label)}の過去問を想定した{html.escape(mode_label)} · {len(domain_questions)}問（模擬問題）</p>
  </header>
  <ul class="question-hub-list">
{chr(10).join(list_items)}
  </ul>
  <p><a href="../../questions/">← 分野一覧へ</a> · <a href="../../">演習モードへ</a></p>"""
        domain_dir = domain_root / slug
        domain_dir.mkdir(parents=True, exist_ok=True)
        domain_canonical = f"{SITE_ORIGIN}/exams/{exam_id}/{mode_id}/domain/{slug}/"
        domain_breadcrumb = breadcrumb(
            [
                ("ホーム", f"{rel_to_root(5)}index.html"),
                ("試験対策", f"{rel_to_root(5)}exams/"),
                (exam_label, f"{rel_to_root(5)}exams/{exam_id}/"),
                (mode_label, "../../"),
                ("問題一覧", "../../questions/"),
                (domain, None),
            ]
        )
        (domain_dir / "index.html").write_text(
            page_shell(
                rel=rel_to_root(5),
                title=seo_domain_title(exam_label, mode_label, domain),
                description=seo_domain_description(
                    exam_label, mode_label, domain, len(domain_questions)
                ),
                canonical=domain_canonical,
                breadcrumb_html=domain_breadcrumb,
                body_html=domain_body,
                css_depth=5,
            ),
            encoding="utf-8",
        )
        sitemap_urls.append(domain_canonical)

    glossary = load_published_glossary()
    rel_root = rel_to_root(5)

    for i, q in enumerate(ordered_all):
        qs = id_slug(q["id"])
        q_dir = q_root / qs
        q_dir.mkdir(parents=True, exist_ok=True)
        kind = mode_cfg["kind"]
        domain_slug = domain_slugs[q["domain"]]
        if kind == "drill":
            body = render_drill_body(q, exam_label, mode_label, domain_slug)
        else:
            body = render_choice_body(q, exam_label, mode_label, domain_slug)
        player_href = f"../../?q={qs}"
        prev_href = f"../{id_slug(ordered_all[i - 1]['id'])}/" if i > 0 else None
        next_href = (
            f"../{id_slug(ordered_all[i + 1]['id'])}/" if i < len(ordered_all) - 1 else None
        )
        body += render_question_actions(player_href, prev_href, next_href)
        body += render_related_section(
            q,
            exam_id=exam_id,
            exam_label=exam_label,
            mode_label=mode_label,
            domain_slug=domain_slug,
            by_domain=by_domain,
            glossary=glossary,
            rel_root=rel_root,
        )

        topic = q.get("topic") or qs
        qid = q.get("id") or qs.upper()
        prompt = q.get("statement") if kind == "drill" else q.get("question")
        title = seo_question_title(exam_label, mode_label, qid, topic)
        description = seo_question_description(exam_label, mode_label, topic, prompt or "")
        canonical = f"{SITE_ORIGIN}/exams/{exam_id}/{mode_id}/q/{qs}/"
        crumb = breadcrumb(
            [
                ("ホーム", f"{rel_to_root(5)}index.html"),
                ("試験対策", f"{rel_to_root(5)}exams/"),
                (exam_label, f"{rel_to_root(5)}exams/{exam_id}/"),
                (mode_label, "../../"),
                ("問題一覧", "../../questions/"),
                (topic, None),
            ]
        )
        json_ld = {
            "@context": "https://schema.org",
            "@graph": [
                {
                    "@type": "BreadcrumbList",
                    "itemListElement": [
                        {"@type": "ListItem", "position": 1, "name": "ホーム", "item": f"{SITE_ORIGIN}/"},
                        {
                            "@type": "ListItem",
                            "position": 2,
                            "name": exam_label,
                            "item": f"{SITE_ORIGIN}/exams/{exam_id}/",
                        },
                        {
                            "@type": "ListItem",
                            "position": 3,
                            "name": f"{mode_label} {topic}",
                            "item": canonical,
                        },
                    ],
                },
                {
                    "@type": "LearningResource",
                    "name": title,
                    "description": description,
                    "url": canonical,
                    "inLanguage": "ja",
                    "learningResourceType": f"過去問想定の{mode_label}",
                    "keywords": f"{exam_label}, 過去問想定, 模擬問題, {q.get('domain', '')}, {topic}",
                },
            ],
        }
        (q_dir / "index.html").write_text(
            page_shell(
                rel=rel_to_root(5),
                title=title,
                description=description,
                canonical=canonical,
                breadcrumb_html=crumb,
                body_html=body,
                json_ld=json_ld,
                css_depth=5,
                og_type="article",
            ),
            encoding="utf-8",
        )
        sitemap_urls.append(canonical)
        index_entries.append(
            {
                "exam": exam_id,
                "mode": mode_id,
                "id": q["id"],
                "slug": qs,
                "domain": q["domain"],
                "domainSlug": domain_slugs[q["domain"]],
                "topic": q.get("topic"),
                "url": canonical,
            }
        )

    if len(index_entries) != len(questions):
        raise RuntimeError("generated page count mismatch")

    print(f"wrote {len(questions)} questions + hubs: exams/{exam_id}/{mode_id}/")
    return sitemap_urls, {
        "exam": exam_id,
        "mode": mode_id,
        "count": len(questions),
        "domainSlugs": domain_slugs,
        "questions": index_entries,
    }


def update_sitemap(urls: list[str]) -> None:
    if not SITEMAP.is_file():
        print("skip sitemap: not found")
        return
    text = SITEMAP.read_text(encoding="utf-8")
    text = re.sub(
        r"\n  <!-- question-pages:start -->[\s\S]*?  <!-- question-pages:end -->",
        "",
        text,
    )
    if not urls:
        SITEMAP.write_text(text, encoding="utf-8")
        return
    entries = []
    for loc in sorted(set(urls)):
        entries.append(
            f"""  <url>
    <loc>{loc}</loc>
    <changefreq>monthly</changefreq>
    <priority>0.7</priority>
  </url>"""
        )
    block = (
        "\n  <!-- question-pages:start -->\n"
        + "\n".join(entries)
        + "\n  <!-- question-pages:end -->"
    )
    text = text.replace("</urlset>", f"{block}\n</urlset>")
    SITEMAP.write_text(text, encoding="utf-8")
    print(f"updated sitemap with {len(entries)} question URLs")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exam", choices=list(EXAMS.keys()))
    parser.add_argument("--mode", choices=["drill", "practice"])
    args = parser.parse_args()

    all_urls: list[str] = []
    index_payload: dict = {"exams": {}}

    for exam_id, exam_cfg in EXAMS.items():
        if args.exam and args.exam != exam_id:
            continue
        index_payload["exams"].setdefault(exam_id, {})
        for mode_id, mode_cfg in exam_cfg["modes"].items():
            if args.mode and args.mode != mode_id:
                continue
            urls, meta = build_mode(exam_id, exam_cfg, mode_id, mode_cfg)
            all_urls.extend(urls)
            index_payload["exams"][exam_id][mode_id] = meta

    INDEX_JSON.parent.mkdir(parents=True, exist_ok=True)
    INDEX_JSON.write_text(
        json.dumps(index_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {INDEX_JSON.relative_to(ROOT)}")

    if not args.exam and not args.mode:
        update_sitemap(all_urls)
    else:
        print("note: sitemap is updated on full build only")


if __name__ == "__main__":
    main()
