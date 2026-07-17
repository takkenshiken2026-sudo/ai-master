#!/usr/bin/env python3
"""「過去問想定 / 過去問を想定した」表記を全ページで統一する。

サイトの免責は一貫して「公式の過去問ではありません」と述べており、
harden_gsc.py も HTML 一部で「過去問想定」表記の除去を始めていたが、
guide 記事・exams ハブ・データ JSON などに旧表記が残っていた。
静的タイトルタグが既に「模擬問題」を採用しているのに合わせ、全体を
「模擬問題 / 本番形式の」へ統一する（自己矛盾の解消・法務上も安全）。

置換は長い（具体的な）パターンから順に適用する。

  python3 tools/normalize_exam_wording.py

冪等: 旧表記が無ければ何も変更しない。
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# 順序が重要（上ほど優先）。上位ルールが下位ルールの部分文字列を先に処理する。
REPLACEMENTS = [
    ("本番・過去問を想定した", "本番形式の"),
    ("過去問を想定した", "本番形式の"),
    ("本番・過去問想定", "本番形式"),
    ("過去問想定の模擬問題", "本番形式の模擬問題"),
    ("過去問想定問題", "模擬問題"),
    ("過去問想定・模擬問題", "模擬問題"),
    ("過去問想定 試験対策", "模擬問題 試験対策"),
    ("過去問想定", "模擬問題"),  # 取りこぼしの受け皿
]

# 対象ディレクトリ・ファイル（ビルドスクリプト tools/*.py は除外）
TARGET_DIRS = ["guide", "exams", "assets/data", "data", "assets/js"]
TARGET_SUFFIXES = {".html", ".json", ".js"}


def apply(text: str) -> tuple[str, int]:
    n = 0
    for old, new in REPLACEMENTS:
        c = text.count(old)
        if c:
            text = text.replace(old, new)
            n += c
    return text, n


def iter_files():
    for d in TARGET_DIRS:
        base = ROOT / d
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if p.is_file() and p.suffix in TARGET_SUFFIXES:
                yield p


def main() -> None:
    total_files = 0
    total_reps = 0
    for p in iter_files():
        text = p.read_text(encoding="utf-8")
        new, n = apply(text)
        if n:
            if p.suffix == ".json":
                json.loads(new)  # 壊れていないか検証
            p.write_text(new, encoding="utf-8")
            total_files += 1
            total_reps += n
            print(f"{p.relative_to(ROOT)}: {n}")
    print(f"updated {total_files} files, {total_reps} replacements")


if __name__ == "__main__":
    main()
