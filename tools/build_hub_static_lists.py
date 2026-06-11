#!/usr/bin/env python3
"""ハブ一覧ページにクローラ向け静的リンクを埋め込む（JS 実行前にもリンクが存在する）。"""

from __future__ import annotations

import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS_JS = ROOT / "assets" / "js" / "tools-data.js"
GLOSSARY_INDEX = ROOT / "data" / "glossary-index.json"
TOOLS_INDEX = ROOT / "tools" / "index.html"
GLOSSARY_INDEX_HTML = ROOT / "glossary" / "index.html"

MARKER_START = "  <!-- hub-crawl-links:start -->"
MARKER_END = "  <!-- hub-crawl-links:end -->"

GLOSSARY_TERM_LIST = """
  <ul class="hub-list" id="termList" aria-label="用語一覧">
    <li class="hub-empty" aria-live="polite">読み込み中…</li>
  </ul>"""

TOOLS_TOOL_LIST = """
  <ul class="tool-list" id="toolList" aria-label="AIツール一覧">
    <li class="hub-empty" aria-live="polite">読み込み中…</li>
  </ul>"""


def parse_tools() -> list[tuple[str, str]]:
    text = TOOLS_JS.read_text(encoding="utf-8")
    tools_block = text.split("const CATEGORIES")[0]
    tools: list[tuple[str, str]] = []
    for block in re.findall(r"\{[^{}]+\}", tools_block):
        id_m = re.search(r'id:\s*"([^"]+)"', block)
        name_m = re.search(r'name:\s*"([^"]+)"', block)
        if not id_m or not name_m or "article: true" not in block:
            continue
        tools.append((id_m.group(1), name_m.group(1)))
    tools.sort(key=lambda x: x[1])
    return tools


def parse_glossary() -> list[tuple[str, str]]:
    if not GLOSSARY_INDEX.is_file():
        return []
    data = json.loads(GLOSSARY_INDEX.read_text(encoding="utf-8"))
    terms = [
        (t["id"], t["name"])
        for t in data.get("terms", [])
        if t.get("published") and (ROOT / "glossary" / t["id"] / "index.html").is_file()
    ]
    terms.sort(key=lambda x: x[1])
    return terms


def render_tool_crawl(tools: list[tuple[str, str]]) -> str:
    items = "\n".join(
        f'      <li><a href="{html.escape(tid)}/">{html.escape(name)}</a></li>'
        for tid, name in tools
    )
    return f"""{MARKER_START}
  <div class="hub-crawl-links" hidden>
    <ul aria-label="AIツール（クローラ向けリンク）">
{items}
    </ul>
  </div>
{MARKER_END}"""


def render_glossary_crawl(terms: list[tuple[str, str]]) -> str:
    items = "\n".join(
        f'      <li><a href="{html.escape(tid)}/">{html.escape(name)}</a></li>'
        for tid, name in terms
    )
    return f"""{MARKER_START}
  <div class="hub-crawl-links" hidden>
    <ul aria-label="用語辞典（クローラ向けリンク）">
{items}
    </ul>
  </div>
{MARKER_END}"""


def remove_legacy_crawl_list(text: str, list_id: str, list_class: str) -> str:
    pattern = re.compile(
        rf"\n  <ul class=\"{re.escape(list_class)}\" id=\"{re.escape(list_id)}\"[\s\S]*?</ul>\n",
        re.MULTILINE,
    )
    return pattern.sub("\n", text, count=1)


def ensure_interactive_list(text: str, marker_end: str, list_html: str, list_id: str) -> str:
    if re.search(rf'id="{re.escape(list_id)}"', text):
        return text
    return text.replace(marker_end, marker_end + list_html, 1)


def inject(path: Path, crawl_block: str, list_html: str, list_id: str, legacy_class: str) -> None:
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(rf"{re.escape(MARKER_START)}[\s\S]*?{re.escape(MARKER_END)}")
    if pattern.search(text):
        text = pattern.sub(crawl_block, text)
    else:
        text = text.replace(
            f'  <ul class="{legacy_class}" id="{list_id}" aria-label="',
            crawl_block + f'\n  <ul class="{legacy_class}" id="{list_id}" aria-label="',
            1,
        )
    text = remove_legacy_crawl_list(text, list_id, legacy_class)
    text = remove_legacy_crawl_list(text, list_id, f"{legacy_class} hub-crawl-list")
    text = ensure_interactive_list(text, MARKER_END, list_html, list_id)
    path.write_text(text, encoding="utf-8")


def main() -> None:
    tools = parse_tools()
    inject(
        TOOLS_INDEX,
        render_tool_crawl(tools),
        TOOLS_TOOL_LIST,
        "toolList",
        "tool-list",
    )
    print(f"tools hub: {len(tools)} article links")

    terms = parse_glossary()
    if terms:
        inject(
            GLOSSARY_INDEX_HTML,
            render_glossary_crawl(terms),
            GLOSSARY_TERM_LIST,
            "termList",
            "hub-list",
        )
        print(f"glossary hub: {len(terms)} published links")


if __name__ == "__main__":
    main()
