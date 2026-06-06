#!/usr/bin/env python3
"""用語マスタをシードから一括再構築し、一覧JSON・HTMLを生成する。

  python3 tools/rebuild_glossary.py
  python3 tools/rebuild_glossary.py --dry-run
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from glossary_seed import ALL_BY_CATEGORY  # noqa: E402
from glossary_seed.exclusions import EXCLUDED_CATEGORIES, EXCLUDED_TERM_IDS  # noqa: E402
from glossary_seed.removals import REMOVAL_IDS  # noqa: E402
from glossary_terms import (  # noqa: E402
    CSV_FILE,
    audit_report,
    terms_to_json_payload,
    validate_terms,
    write_csv,
)

JSON_FILE = ROOT / "data" / "glossary-terms.json"


def sort_key_from(name: str, reading: str) -> str:
    if reading and re.match(r"^[ぁ-ん]", reading):
        return reading[:1]
    return name[:1] if name else ""


def seed_tuple_to_row(item: tuple, category: str) -> dict:
    id_, name, yomi, reading, summary, tier, exams = item
    return {
        "id": id_,
        "name": name,
        "yomi": yomi,
        "reading": reading,
        "summary": summary,
        "category": category,
        "sort_key": sort_key_from(name, reading),
        "status": "planned",
        "tier": str(tier),
        "exams": exams,
        "priority": "",
        "notes": "",
    }


def is_excluded(row: dict) -> bool:
    return (
        row.get("category") in EXCLUDED_CATEGORIES
        or row.get("id") in EXCLUDED_TERM_IDS
        or row.get("id") in REMOVAL_IDS
    )


def build_terms() -> list[dict]:
    terms: list[dict] = []
    seen_ids: set[str] = set()
    seen_names: set[str] = set()

    for category, seed_list in ALL_BY_CATEGORY.items():
        for item in seed_list:
            row = seed_tuple_to_row(item, category)
            if is_excluded(row):
                continue
            if row["id"] in seen_ids or row["name"] in seen_names:
                continue
            seen_ids.add(row["id"])
            seen_names.add(row["name"])
            terms.append(row)

    # 公開済み記事は status を維持
    published_ids = {
        p.name
        for p in (ROOT / "glossary").iterdir()
        if p.is_dir() and (p / "index.html").is_file()
    }
    for row in terms:
        if row["id"] in published_ids:
            row["status"] = "published"

    return sorted(terms, key=lambda x: (x["category"], x["name"]))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-build", action="store_true", help="CSV/JSON のみ（HTMLは生成しない）")
    args = parser.parse_args()

    terms = build_terms()
    errors = validate_terms(terms)
    if errors:
        print("検証エラー:")
        for e in errors[:20]:
            print(" ", e)
        raise SystemExit(1)

    print(audit_report(terms))
    if args.dry_run:
        print("\n--dry-run のため書き込みしません")
        return

    write_csv(terms, CSV_FILE)
    JSON_FILE.write_text(
        json.dumps(terms_to_json_payload(terms), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"\nwrote {CSV_FILE.relative_to(ROOT)}")
    print(f"synced {JSON_FILE.relative_to(ROOT)}")

    if not args.no_build:
        subprocess.run([sys.executable, str(ROOT / "tools" / "build_glossary.py")], check=True)


if __name__ == "__main__":
    main()
