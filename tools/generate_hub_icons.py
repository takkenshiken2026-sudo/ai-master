#!/usr/bin/env python3
"""ハブカテゴリアイコン — 色付き背景 + 線画を assets/images/hub-icons/ に生成。"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "images" / "hub-icons"

# Tabler path d（24×24）
PATHS: dict[str, list[str]] = {
    "nav-exams": [
        "M11 12a1 1 0 1 0 2 0a1 1 0 1 0 -2 0",
        "M7 12a5 5 0 1 0 10 0a5 5 0 1 0 -10 0",
        "M3 12a9 9 0 1 0 18 0a9 9 0 1 0 -18 0",
    ],
    "nav-guide": [
        "M19 4v16h-12a2 2 0 0 1 -2 -2v-12a2 2 0 0 1 2 -2h12",
        "M19 16h-12a2 2 0 0 0 -2 2",
        "M9 8h6",
    ],
    "nav-glossary": [
        "M10 19h-6a1 1 0 0 1 -1 -1v-14a1 1 0 0 1 1 -1h6a2 2 0 0 1 2 2a2 2 0 0 1 2 -2h6a1 1 0 0 1 1 1v14a1 1 0 0 1 -1 1h-6a2 2 0 0 0 -2 2a2 2 0 0 0 -2 -2",
        "M12 5v16",
    ],
    "nav-tools": [
        "M3 21h4l13 -13a1.5 1.5 0 0 0 -4 -4l-13 13v4",
        "M14.5 5.5l4 4",
    ],
    "nav-career": [
        "M3 9a2 2 0 0 1 2 -2h14a2 2 0 0 1 2 2v9a2 2 0 0 1 -2 2h-14a2 2 0 0 1 -2 -2l0 -9",
        "M8 7v-2a2 2 0 0 1 2 -2h4a2 2 0 0 1 2 2v2",
        "M12 12l0 .01",
    ],
    "exam-overview": [
        "M9 5h-2a2 2 0 0 0 -2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2 -2v-12a2 2 0 0 0 -2 -2h-2",
        "M9 5a2 2 0 0 1 2 -2h2a2 2 0 0 1 2 2a2 2 0 0 1 -2 2h-2a2 2 0 0 1 -2 -2",
        "M9 12l.01 0",
        "M13 12l2 0",
    ],
    "study-method": [
        "M4 20h4l10.5 -10.5a2.828 2.828 0 1 0 -4 -4l-10.5 10.5v4",
        "M13.5 6.5l4 4",
    ],
    "cert-compare": [
        "M7 20l10 0",
        "M6 6l6 -1l6 1",
        "M12 3l0 17",
        "M9 12l-3 -6l-3 6a3 3 0 0 0 6 0",
        "M21 12l-3 -6l-3 6a3 3 0 0 0 6 0",
    ],
    "domain-grid": [
        "M4 5a1 1 0 0 1 1 -1h4a1 1 0 0 1 1 1v4a1 1 0 0 1 -1 1h-4a1 1 0 0 1 -1 -1l0 -4",
        "M14 5a1 1 0 0 1 1 -1h4a1 1 0 0 1 1 1v4a1 1 0 0 1 -1 1h-4a1 1 0 0 1 -1 -1l0 -4",
        "M4 15a1 1 0 0 1 1 -1h4a1 1 0 0 1 1 1v4a1 1 0 0 1 -1 1h-4a1 1 0 0 1 -1 -1l0 -4",
        "M14 15a1 1 0 0 1 1 -1h4a1 1 0 0 1 1 1v4a1 1 0 0 1 -1 1h-4a1 1 0 0 1 -1 -1l0 -4",
    ],
    "exam-scope": [
        "M9.615 20h-2.615a2 2 0 0 1 -2 -2v-12a2 2 0 0 1 2 -2h8a2 2 0 0 1 2 2v8",
        "M14 19l2 2l4 -4",
        "M9 8h4",
    ],
    "difficulty": [
        "M3 13a1 1 0 0 1 1 -1h4a1 1 0 0 1 1 1v6a1 1 0 0 1 -1 1h-4a1 1 0 0 1 -1 -1l0 -6",
        "M15 9a1 1 0 0 1 1 -1h4a1 1 0 0 1 1 1v10a1 1 0 0 1 -1 1h-4a1 1 0 0 1 -1 -1l0 -10",
        "M9 5a1 1 0 0 1 1 -1h4a1 1 0 0 1 1 1v14a1 1 0 0 1 -1 1h-4a1 1 0 0 1 -1 -1l0 -14",
    ],
    "after-cert": [
        "M6 9a6 6 0 1 0 12 0a6 6 0 1 0 -12 0",
        "M12 15l3.4 5.89l1.598 -3.233l3.598 .232l-3.4 -5.889",
    ],
    "pass-rate": [
        "M3 17l6 -6l4 4l8 -8",
        "M14 7l7 0l0 7",
    ],
    "g-kentei-mark": [
        "M15.5 13a3.5 3.5 0 0 0 -3.5 3.5v1a3.5 3.5 0 0 0 7 0v-1.8",
        "M8.5 13a3.5 3.5 0 0 1 3.5 3.5v1a3.5 3.5 0 0 1 -7 0v-1.8",
        "M17.5 16a3.5 3.5 0 0 0 0 -7h-.5",
        "M6.5 16a3.5 3.5 0 0 1 0 -7h.5",
    ],
    "genai-mark": [
        "M16 18a2 2 0 0 1 2 2a2 2 0 0 1 2 -2a2 2 0 0 1 -2 -2a2 2 0 0 1 -2 2m0 -12a2 2 0 0 1 2 2a2 2 0 0 1 2 -2a2 2 0 0 1 -2 -2a2 2 0 0 1 -2 2m-7 12a6 6 0 0 1 6 -6a6 6 0 0 1 -6 -6a6 6 0 0 1 -6 6a6 6 0 0 1 6 6",
    ],
    "glossary-basics": [
        "M10 11h12v12H10z",
        "M13 14h6",
        "M13 17h4",
    ],
    "glossary-models": [
        "M11 12a1 1 0 1 0 2 0a1 1 0 1 0 -2 0",
        "M7 12a5 5 0 1 0 10 0a5 5 0 1 0 -10 0",
    ],
    "glossary-genai": [
        "M16 18a2 2 0 0 1 2 2a2 2 0 0 1 2 -2a2 2 0 0 1 -2 -2a2 2 0 0 1 -2 2m0 -12a2 2 0 0 1 2 2a2 2 0 0 1 2 -2a2 2 0 0 1 -2 -2a2 2 0 0 1 -2 2m-7 12a6 6 0 0 1 6 -6a6 6 0 0 1 -6 -6a6 6 0 0 1 -6 6a6 6 0 0 1 6 6",
    ],
    "glossary-data": [
        "M4 5a1 1 0 0 1 1 -1h4a1 1 0 0 1 1 1v4a1 1 0 0 1 -1 1h-4a1 1 0 0 1 -1 -1l0 -4",
        "M14 5a1 1 0 0 1 1 -1h4a1 1 0 0 1 1 1v4a1 1 0 0 1 -1 1h-4a1 1 0 0 1 -1 -1l0 -4",
        "M4 15a1 1 0 0 1 1 -1h4a1 1 0 0 1 1 1v4a1 1 0 0 1 -1 1h-4a1 1 0 0 1 -1 -1l0 -4",
        "M14 15a1 1 0 0 1 1 -1h4a1 1 0 0 1 1 1v4a1 1 0 0 1 -1 1h-4a1 1 0 0 1 -1 -1l0 -4",
    ],
    "glossary-governance": [
        "M12 3a12 12 0 0 0 8.5 3a12 12 0 0 1 -8.5 15a12 12 0 0 1 -8.5 -15a12 12 0 0 0 8.5 -3",
    ],
    "audience": [
        "M9 7a4 4 0 1 0 8 0a4 4 0 0 0 -8 0",
        "M3 21v-2a4 4 0 0 1 4 -4h10a4 4 0 0 1 4 4v2",
    ],
    "enterprise": [
        "M3 21h18",
        "M9 8h1",
        "M9 12h1",
        "M14 8h1",
        "M14 12h1",
        "M5 21v-14a2 2 0 0 1 2 -2h10a2 2 0 0 1 2 2v14",
    ],
    "career-role": [
        "M8 7a4 4 0 1 0 8 0a4 4 0 0 0 -8 0",
        "M6 21v-2a4 4 0 0 1 4 -4h4",
        "M15 19l2 2l4 -4",
    ],
    "career-market": [
        "M7 15h-3a1 1 0 0 1 -1 -1v-8a1 1 0 0 1 1 -1h12a1 1 0 0 1 1 1v3",
        "M7 10a1 1 0 0 1 1 -1h12a1 1 0 0 1 1 1v8a1 1 0 0 1 -1 1h-12a1 1 0 0 1 -1 -1l0 -8",
        "M12 14a2 2 0 1 0 4 0a2 2 0 0 0 -4 0",
    ],
    "career-roadmap": [
        "M12 18.5l-3 -1.5l-6 3v-13l6 -3l6 3l6 -3v7.5",
        "M9 4v13",
        "M15 7v5.5",
    ],
    "career-move": [
        "M18 15l3 -3l-3 -3",
        "M3 12a2 2 0 1 0 4 0a2 2 0 1 0 -4 0",
        "M7 12h14",
    ],
}

THEMES = {
    "blue": {"bg": "#E8F0FE", "stroke": "#1A5CDB"},
    "green": {"bg": "#EAF3DE", "stroke": "#3B6D11"},
    "purple": {"bg": "#F3EEFF", "stroke": "#4A1EA0"},
    "pink": {"bg": "#FBEAF0", "stroke": "#993556"},
    "slate": {"bg": "#E8EEF4", "stroke": "#334155"},
    "indigo": {"bg": "#EEF2FF", "stroke": "#4338CA"},
}

# slug -> {theme, paths_key}
BADGES: dict[str, dict] = {
    # 学習ガイド — G検定系
    "gk-exam-overview": {"theme": "blue", "paths": "exam-overview"},
    "gk-study-method": {"theme": "blue", "paths": "study-method"},
    "gk-exam-scope": {"theme": "blue", "paths": "exam-scope"},
    "gk-domain-grid": {"theme": "blue", "paths": "domain-grid"},
    # 生成AIパスポート系
    "gp-exam-overview": {"theme": "green", "paths": "exam-overview"},
    "gp-study-method": {"theme": "green", "paths": "study-method"},
    "gp-exam-scope": {"theme": "green", "paths": "exam-scope"},
    "gp-domain-grid": {"theme": "green", "paths": "domain-grid"},
    # 学習ガイド — 共通
    "cert-compare": {"theme": "indigo", "paths": "cert-compare"},
    "nav-glossary": {"theme": "indigo", "paths": "nav-glossary"},
    "audience": {"theme": "indigo", "paths": "audience"},
    "enterprise": {"theme": "indigo", "paths": "enterprise"},
    "pass-rate": {"theme": "indigo", "paths": "pass-rate"},
    "difficulty": {"theme": "indigo", "paths": "difficulty"},
    "after-cert": {"theme": "indigo", "paths": "after-cert"},
    # 資格マーク単体（フォールバック）
    "g-kentei": {"theme": "blue", "paths": "g-kentei-mark"},
    "genai": {"theme": "green", "paths": "genai-mark"},
    # 用語辞典
    "glossary-basics": {"theme": "blue", "paths": "glossary-basics"},
    "glossary-models": {"theme": "blue", "paths": "glossary-models"},
    "glossary-genai": {"theme": "green", "paths": "glossary-genai"},
    "glossary-data": {"theme": "purple", "paths": "glossary-data"},
    "glossary-governance": {"theme": "pink", "paths": "glossary-governance"},
    # キャリア
    "career-role": {"theme": "blue", "paths": "career-role"},
    "career-market": {"theme": "green", "paths": "career-market"},
    "career-roadmap": {"theme": "purple", "paths": "career-roadmap"},
    "career-move": {"theme": "pink", "paths": "career-move"},
    # ナビ（文字なし・単色背景）
    "nav-exams": {"theme": "blue", "paths": "nav-exams"},
    "nav-guide": {"theme": "blue", "paths": "nav-guide"},
    "nav-tools": {"theme": "slate", "paths": "nav-tools"},
    "nav-career": {"theme": "blue", "paths": "nav-career"},
}


def render_badge(*, theme: dict, paths: list[str]) -> str:
    path_lines = "\n".join(
        f'    <path d="{d}"/>'
        for d in paths
    )
    icon_block = (
        f'  <g transform="translate(4,4) scale(0.78)" '
        f'fill="none" stroke="{theme["stroke"]}" stroke-width="1.75" '
        f'stroke-linecap="round" stroke-linejoin="round">\n{path_lines}\n  </g>'
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" aria-hidden="true">\n'
        f'  <rect width="32" height="32" rx="8" fill="{theme["bg"]}"/>\n'
        f"{icon_block}\n"
        f"</svg>\n"
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for slug, spec in BADGES.items():
        theme = THEMES[spec["theme"]]
        paths = PATHS[spec["paths"]]
        (OUT / f"{slug}.svg").write_text(
            render_badge(theme=theme, paths=paths),
            encoding="utf-8",
        )
    print(f"wrote {len(BADGES)} badge icons to {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
