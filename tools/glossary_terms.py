#!/usr/bin/env python3
"""用語マスタ CSV の読み込み・検証（静的サイトビルド共通）。"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV_FILE = ROOT / "data" / "glossary-terms.csv"
CATEGORIES_FILE = ROOT / "data" / "glossary-categories.json"

CSV_FIELDS = [
    "id",
    "name",
    "yomi",
    "reading",
    "summary",
    "category",
    "sort_key",
    "status",
    "tier",
    "exams",
    "priority",
    "notes",
]

SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def load_categories() -> dict:
    with CATEGORIES_FILE.open(encoding="utf-8") as f:
        return json.load(f)


def load_terms_csv() -> list[dict]:
    if not CSV_FILE.is_file():
        return []
    with CSV_FILE.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = []
        for row in reader:
            if not row.get("id") or row["id"].startswith("#"):
                continue
            rows.append({k: (row.get(k) or "").strip() for k in CSV_FIELDS})
        return rows


def terms_to_json_payload(terms: list[dict]) -> dict:
    meta = load_categories()
    categories = {k: v["label"] for k, v in meta["categories"].items()}
    json_terms = []
    for t in terms:
        json_terms.append(
            {
                "id": t["id"],
                "name": t["name"],
                "yomi": t["yomi"],
                "reading": t.get("reading") or "",
                "summary": t["summary"],
                "category": t["category"],
                "sortKey": t.get("sort_key") or t["name"][:1],
                "status": t.get("status") or "planned",
                "tier": int(t["tier"]) if t.get("tier", "").isdigit() else 3,
                "exams": [x.strip() for x in t.get("exams", "").split("|") if x.strip()],
                "priority": t.get("priority") or "",
                "notes": t.get("notes") or "",
            }
        )
    return {"categories": categories, "terms": json_terms}


def validate_terms(terms: list[dict]) -> list[str]:
    errors: list[str] = []
    seen_ids: set[str] = set()
    seen_names: set[str] = set()
    cat_ids = set(load_categories()["categories"].keys())

    for i, t in enumerate(terms, start=2):
        row = f"CSV行{i}"
        tid = t.get("id", "")
        if not tid:
            errors.append(f"{row}: id が空です")
            continue
        if not SLUG_RE.match(tid):
            errors.append(f"{row}: id '{tid}' は slug 形式（小文字・ハイフン）にしてください")
        if tid in seen_ids:
            errors.append(f"{row}: id '{tid}' が重複しています")
        seen_ids.add(tid)

        name = t.get("name", "")
        if not name:
            errors.append(f"{row}: name が空です")
        elif name in seen_names:
            errors.append(f"{row}: name '{name}' が重複しています")
        seen_names.add(name)

        if t.get("category") not in cat_ids:
            errors.append(f"{row}: category '{t.get('category')}' が未定義です")

        if not t.get("summary"):
            errors.append(f"{row}: summary が空です（一覧・スニペット用）")

        status = t.get("status") or "planned"
        if status not in {"planned", "draft", "published"}:
            errors.append(f"{row}: status は planned / draft / published のいずれかです")

    return errors


def audit_report(terms: list[dict]) -> str:
    meta = load_categories()
    targets = meta["categories"]
    total_target = meta["totalTarget"]
    by_cat: dict[str, int] = {k: 0 for k in targets}
    by_tier: dict[int, int] = {1: 0, 2: 0, 3: 0}
    by_status: dict[str, int] = {}

    for t in terms:
        cat = t.get("category", "")
        if cat in by_cat:
            by_cat[cat] += 1
        tier = int(t["tier"]) if str(t.get("tier", "")).isdigit() else 3
        by_tier[tier] = by_tier.get(tier, 0) + 1
        st = t.get("status") or "planned"
        by_status[st] = by_status.get(st, 0) + 1

    lines = [
        f"用語総数: {len(terms)} / 目標 {total_target['min']}〜{total_target['max']}（推奨 {total_target['recommended']}）",
        "",
        "【カテゴリ別】目標件数との差分",
    ]
    for cid, info in targets.items():
        n = by_cat.get(cid, 0)
        diff = n - info["target"]
        mark = "OK" if diff >= 0 else f"あと {-diff}"
        lines.append(f"  {info['label']} ({cid}): {n} / {info['target']} … {mark}")

    lines += [
        "",
        "【優先度 tier】",
        f"  tier1（最優先記事化）: {by_tier.get(1, 0)}",
        f"  tier2: {by_tier.get(2, 0)}",
        f"  tier3: {by_tier.get(3, 0)}",
        "",
        "【公開状態】",
    ]
    for st, n in sorted(by_status.items()):
        lines.append(f"  {st}: {n}")

    total = len(terms)
    if total < total_target["min"]:
        lines.append(f"\n→ あと {total_target['min'] - total} 語で下限 {total_target['min']} に到達")
    elif total > total_target["max"]:
        lines.append(f"\n→ {total - total_target['max']} 語削減すると上限 {total_target['max']} 以内")
    else:
        lines.append("\n→ 総数は目標レンジ内です。カテゴリ別の過不足を調整してください。")

    return "\n".join(lines)


def write_csv(terms: list[dict], path: Path | None = None) -> None:
    out = path or CSV_FILE
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for t in terms:
            writer.writerow({k: t.get(k, "") for k in CSV_FIELDS})


def sync_json_from_csv() -> None:
    terms = load_terms_csv()
    if not terms:
        raise SystemExit(f"CSV が空または未作成です: {CSV_FILE}")
    errors = validate_terms(terms)
    if errors:
        raise SystemExit("検証エラー:\n" + "\n".join(errors[:10]))
    json_path = ROOT / "data" / "glossary-terms.json"
    payload = terms_to_json_payload(terms)
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="用語マスタ CSV の検証・監査")
    parser.add_argument("--audit", action="store_true", help="カテゴリ別の過不足レポートを表示")
    parser.add_argument("--validate", action="store_true", help="CSV を検証")
    parser.add_argument("--sync-json", action="store_true", help="CSV から glossary-terms.json を更新")
    args = parser.parse_args()

    if args.sync_json:
        sync_json_from_csv()
        print(f"synced {ROOT / 'data/glossary-terms.json'}")
        terms = load_terms_csv()
        print(audit_report(terms))
        return

    terms = load_terms_csv()
    if not terms:
        raise SystemExit(f"CSV が見つかりません: {CSV_FILE}\n先に python3 tools/seed_glossary_terms.py を実行してください。")

    if args.validate or not args.audit:
        errors = validate_terms(terms)
        if errors:
            print("検証エラー:")
            for e in errors:
                print(f"  - {e}")
            raise SystemExit(1)
        print(f"OK: {len(terms)} 語")

    if args.audit or not args.validate:
        print(audit_report(terms))


if __name__ == "__main__":
    main()
