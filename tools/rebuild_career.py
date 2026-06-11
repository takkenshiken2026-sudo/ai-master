#!/usr/bin/env python3
"""キャリア記事マスタの検証と index JSON の同期。

  python3 tools/rebuild_career.py
  python3 tools/rebuild_career.py --audit
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from hub_icons import load_aliases, resolve_career_icon  # noqa: E402
CATEGORIES_FILE = ROOT / "data" / "career-categories.json"
INDEX_FILE = ROOT / "data" / "career-index.json"
ICON_ALIASES_JSON = ROOT / "data" / "career-icon-aliases.json"


def load_categories() -> dict:
    return json.loads(CATEGORIES_FILE.read_text(encoding="utf-8"))


def load_index() -> dict:
    return json.loads(INDEX_FILE.read_text(encoding="utf-8"))


def validate(articles: list[dict], cat_ids: set[str]) -> list[str]:
    errors: list[str] = []
    seen_ids: set[str] = set()
    for i, a in enumerate(articles, start=1):
        row = f"記事{i}"
        aid = a.get("id", "")
        if not aid:
            errors.append(f"{row}: id が空です")
            continue
        if aid in seen_ids:
            errors.append(f"{row}: id '{aid}' が重複しています")
        seen_ids.add(aid)
        if a.get("category") not in cat_ids:
            errors.append(f"{row}: category '{a.get('category')}' が未定義です")
        if not a.get("name"):
            errors.append(f"{row}: name が空です")
        if not a.get("summary"):
            errors.append(f"{row}: summary が空です")
    return errors


def audit_report(articles: list[dict], meta: dict) -> str:
    targets = meta["categories"]
    total_target = meta["totalTarget"]
    by_cat = {k: 0 for k in targets}
    for a in articles:
        cat = a.get("category", "")
        if cat in by_cat:
            by_cat[cat] += 1
    lines = [
        f"記事総数: {len(articles)} / 目標 {total_target['min']}〜{total_target['max']}（推奨 {total_target['recommended']}）",
        "",
        "【カテゴリ別】目標件数との差分",
    ]
    for cid, info in targets.items():
        n = by_cat.get(cid, 0)
        diff = n - info["target"]
        mark = "OK" if diff >= 0 else f"あと {-diff}"
        lines.append(f"  {info['label']} ({cid}): {n} / {info['target']} … {mark}")
    return "\n".join(lines)


def enrich_article_icons(articles: list[dict]) -> None:
    aliases = load_aliases(ICON_ALIASES_JSON)
    for article in articles:
        icon = resolve_career_icon(article["id"], article.get("category", ""), aliases)
        if icon:
            article["icon"] = icon
        else:
            article.pop("icon", None)


def sync_index_categories(data: dict, meta: dict) -> dict:
    categories = {k: v["label"] for k, v in meta["categories"].items()}
    articles = data.get("articles") or data.get("roles") or []
    return {"categories": categories, "articles": articles}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit", action="store_true")
    args = parser.parse_args()

    meta = load_categories()
    data = load_index()
    cat_ids = set(meta["categories"].keys())
    articles = data.get("articles") or data.get("roles") or []

    errors = validate(articles, cat_ids)
    if errors:
        print("検証エラー:")
        for e in errors:
            print(" ", e)
        raise SystemExit(1)

    payload = sync_index_categories(data, meta)
    enrich_article_icons(payload["articles"])
    INDEX_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"synced {INDEX_FILE.relative_to(ROOT)}")
    print()
    print(audit_report(payload["articles"], meta))


if __name__ == "__main__":
    main()
