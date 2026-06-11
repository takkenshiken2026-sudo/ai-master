#!/usr/bin/env python3
"""ai_master_icons_inline_svg.html から hub-icons SVG を生成する。"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "tools" / "ai_master_icons_inline_svg.html"
OUT = ROOT / "assets" / "images" / "hub-icons"

# HTML の日本語ラベル → ファイル slug
LABEL_TO_SLUG: dict[str, str] = {
    "試験対策": "nav-exams",
    "学習ガイド": "nav-guide",
    "AI用語辞典": "nav-glossary",
    "AIツール": "nav-tools",
    "AIキャリア": "nav-career",
    "試験概要": "exam-overview",
    "勉強法": "study-method",
    "資格比較": "cert-compare",
    "分野別解説": "domain-grid",
    "難易度": "difficulty",
    "試験日程": "exam-schedule",
    "合格後の活かし方": "after-cert",
    "勉強時間の目安": "study-time",
    "出題範囲": "exam-scope",
    "受験費用": "exam-cost",
    "合格率": "pass-rate",
    "G検定": "g-kentei",
    "生成AIパスポート": "genai",
    "資格一覧": "cert-list",
    "模擬試験": "mock-exam",
    "一問一答": "drill",
    "AI職種": "career-role",
    "年収・市場": "career-market",
    "ロードマップ": "career-roadmap",
    "転職・チェンジ": "career-move",
    "未経験から": "career-beginner",
    "必要スキル": "career-skills",
}

# 出力 slug → 参照するアイコン slug（同じ path を複数ファイルに）
ALIASES: dict[str, str] = {
    # 学習ガイド — G検定 / パスポートで同じ線画
    "gk-exam-overview": "exam-overview",
    "gp-exam-overview": "exam-overview",
    "gk-study-method": "study-method",
    "gp-study-method": "study-method",
    "gk-exam-scope": "exam-scope",
    "gp-exam-scope": "exam-scope",
    "gk-domain-grid": "domain-grid",
    "gp-domain-grid": "domain-grid",
    # 用語辞典カテゴリ
    "glossary-basics": "nav-glossary",
    "glossary-models": "nav-exams",
    "glossary-genai": "genai",
    "glossary-data": "domain-grid",
    "glossary-governance": "cert-list",
    # 学習ガイド — 共通カテゴリ
    "audience": "career-role",
    "enterprise": "cert-list",
}


def parse_icons(html: str) -> dict[str, list[str]]:
    icons: dict[str, list[str]] = {}
    blocks = re.findall(
        r'<div class="ic">\s*<svg[^>]*>(.*?)</svg>\s*<span>([^<]+)</span>',
        html,
        flags=re.S,
    )
    for svg_inner, label in blocks:
        slug = LABEL_TO_SLUG.get(label.strip())
        if not slug:
            raise ValueError(f"unknown icon label: {label!r}")
        paths = re.findall(r'<path d="([^"]+)"', svg_inner)
        # 透明背景用の M0 0h24 行は除外
        paths = [p for p in paths if not p.startswith("M0 0h24")]
        icons[slug] = paths
    return icons


def render_icon(paths: list[str]) -> str:
    path_lines = "\n".join(f'    <path d="{d}"/>' for d in paths)
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" aria-hidden="true">\n'
        '  <path stroke="none" d="M0 0h24v24H0z" fill="none"/>\n'
        '  <g fill="none" stroke="#111" stroke-width="1" '
        'stroke-linecap="round" stroke-linejoin="round">\n'
        f"{path_lines}\n"
        "  </g>\n"
        "</svg>\n"
    )


def main() -> None:
    if not SOURCE.is_file():
        raise SystemExit(f"missing icon source: {SOURCE}")

    html = SOURCE.read_text(encoding="utf-8")
    icons = parse_icons(html)
    OUT.mkdir(parents=True, exist_ok=True)

    written: dict[str, str] = {}
    for slug, paths in icons.items():
        written[slug] = render_icon(paths)
        (OUT / f"{slug}.svg").write_text(written[slug], encoding="utf-8")

    for alias, target in ALIASES.items():
        if target not in written:
            raise ValueError(f"alias target missing: {target}")
        (OUT / f"{alias}.svg").write_text(written[target], encoding="utf-8")

    total = len(icons) + len(ALIASES)
    print(f"wrote {total} icons to {OUT.relative_to(ROOT)} from {SOURCE.name}")


if __name__ == "__main__":
    main()
