#!/usr/bin/env python3
"""data/guide-articles.csv から data/guide-index.json を生成する。

  python3 tools/build_guide_index.py
"""

from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from hub_icons import load_aliases, resolve_guide_icon  # noqa: E402
CSV_FILE = ROOT / "data" / "guide-articles.csv"
META_FILE = ROOT / "data" / "guide-categories.json"
INDEX_FILE = ROOT / "data" / "guide-index.json"
ICON_ALIASES_JSON = ROOT / "data" / "guide-icon-aliases.json"
GUIDE_DIR = ROOT / "guide"


def load_meta() -> dict:
    return json.loads(META_FILE.read_text(encoding="utf-8"))


def article_published(article_id: str) -> bool:
    return (GUIDE_DIR / article_id / "index.html").is_file()


def main() -> None:
    meta = load_meta()
    cat_map = meta["csvCategoryMap"]
    categories = {k: v["label"] for k, v in meta["categories"].items()}
    cat_order = list(categories.keys())
    cat_counters: dict[str, int] = defaultdict(int)

    articles: list[dict] = []
    with CSV_FILE.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            no = int(row["No"])
            csv_cat = row["カテゴリ"].strip()
            category = cat_map.get(csv_cat)
            if not category:
                raise SystemExit(f"未知のカテゴリ: {csv_cat} (No.{no})")

            cat_counters[category] += 1
            article_id = f"{category}-{cat_counters[category]:02d}"
            priority = row["優先度"].strip()
            keyword = row["想定キーワード"].strip()

            article = {
                "id": article_id,
                "no": no,
                "name": row["タイトル"].strip(),
                "summary": "",
                "category": category,
                "keyword": keyword,
                "priority": priority,
                "featured": priority == "高" and cat_counters[category] <= 2,
                "published": article_published(article_id),
            }
            articles.append(article)

    aliases = load_aliases(ICON_ALIASES_JSON)
    for article in articles:
        icon = resolve_guide_icon(article["id"], article["category"], aliases)
        if icon:
            article["icon"] = icon

    articles.sort(key=lambda a: a["no"])
    payload = {
        "categories": categories,
        "categoryOrder": cat_order,
        "articles": articles,
    }
    INDEX_FILE.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    published = sum(1 for a in articles if a["published"])
    print(f"Wrote {INDEX_FILE} ({len(articles)} articles, {published} published)")


if __name__ == "__main__":
    main()
