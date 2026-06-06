#!/usr/bin/env python3
"""移行済み CSV から案B用のカテゴリ別シード .py を生成する（一度きり／再生成用）。"""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV_FILE = ROOT / "data" / "glossary-terms.csv"
OUT_DIR = ROOT / "tools" / "glossary_seed"

MODULES = {
    "basics": ("basics.py", "基礎・機械学習"),
    "models-tech": ("models_tech.py", "モデル・技術"),
    "genai-use": ("genai_use.py", "生成AI活用"),
    "data-ops": ("data_ops.py", "データ・運用"),
    "governance": ("governance.py", "倫理・ビジネス"),
}


def py_str(s: str) -> str:
    return repr(s)


def main() -> None:
    rows = list(csv.DictReader(CSV_FILE.open(encoding="utf-8")))
    by_cat: dict[str, list] = defaultdict(list)
    for r in rows:
        by_cat[r["category"]].append(r)

    for cat_id, (filename, label) in MODULES.items():
        terms = sorted(by_cat.get(cat_id, []), key=lambda x: x["name"])
        lines = [
            f'"""案B: {label}（{len(terms)}語）。"""',
            "",
            "# id, name, yomi, reading, summary, tier, exams",
            "TERMS = [",
        ]
        for r in terms:
            tier = int(r["tier"]) if str(r.get("tier", "")).isdigit() else 2
            exams = r.get("exams") or "g-kentei"
            tup = (
                r["id"],
                r["name"],
                r["yomi"],
                r["reading"],
                r["summary"],
                tier,
                exams,
            )
            lines.append(f"    {tup!r},")
        lines.append("]")
        lines.append("")
        (OUT_DIR / filename).write_text("\n".join(lines), encoding="utf-8")
        print(f"wrote {filename} ({len(terms)} terms)")


if __name__ == "__main__":
    main()
