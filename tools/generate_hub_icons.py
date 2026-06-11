#!/usr/bin/env python3
"""Tabler ストローク SVG を assets/images/hub-icons/ に生成。"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "images" / "hub-icons"
STROKE = "#334155"

# path d 属性のみ（参照: ai_master_icons_inline_svg.html）
ICONS: dict[str, list[str]] = {
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
        "M7 7h1",
        "M7 11h1",
        "M16 7h1",
        "M16 11h1",
        "M16 15h1",
    ],
    "nav-tools": [
        "M3 21h4l13 -13a1.5 1.5 0 0 0 -4 -4l-13 13v4",
        "M14.5 5.5l4 4",
        "M12 8l-5 -5l-4 4l5 5",
        "M7 8l-1.5 1.5",
        "M16 12l5 5l-4 4l-5 -5",
        "M16 17l-1.5 1.5",
    ],
    "nav-career": [
        "M3 9a2 2 0 0 1 2 -2h14a2 2 0 0 1 2 2v9a2 2 0 0 1 -2 2h-14a2 2 0 0 1 -2 -2l0 -9",
        "M8 7v-2a2 2 0 0 1 2 -2h4a2 2 0 0 1 2 2v2",
        "M12 12l0 .01",
        "M3 13a20 20 0 0 0 18 0",
    ],
    "exam-overview": [
        "M9 5h-2a2 2 0 0 0 -2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2 -2v-12a2 2 0 0 0 -2 -2h-2",
        "M9 5a2 2 0 0 1 2 -2h2a2 2 0 0 1 2 2a2 2 0 0 1 -2 2h-2a2 2 0 0 1 -2 -2",
        "M9 12l.01 0",
        "M13 12l2 0",
        "M9 16l.01 0",
        "M13 16l2 0",
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
    "difficulty": [
        "M3 13a1 1 0 0 1 1 -1h4a1 1 0 0 1 1 1v6a1 1 0 0 1 -1 1h-4a1 1 0 0 1 -1 -1l0 -6",
        "M15 9a1 1 0 0 1 1 -1h4a1 1 0 0 1 1 1v10a1 1 0 0 1 -1 1h-4a1 1 0 0 1 -1 -1l0 -10",
        "M9 5a1 1 0 0 1 1 -1h4a1 1 0 0 1 1 1v14a1 1 0 0 1 -1 1h-4a1 1 0 0 1 -1 -1l0 -14",
        "M4 20h14",
    ],
    "after-cert": [
        "M6 9a6 6 0 1 0 12 0a6 6 0 1 0 -12 0",
        "M12 15l3.4 5.89l1.598 -3.233l3.598 .232l-3.4 -5.889",
        "M6.802 12l-3.4 5.89l3.598 -.233l1.598 3.232l3.4 -5.889",
    ],
    "exam-scope": [
        "M9.615 20h-2.615a2 2 0 0 1 -2 -2v-12a2 2 0 0 1 2 -2h8a2 2 0 0 1 2 2v8",
        "M14 19l2 2l4 -4",
        "M9 8h4",
        "M9 12h2",
    ],
    "pass-rate": [
        "M3 17l6 -6l4 4l8 -8",
        "M14 7l7 0l0 7",
    ],
    "g-kentei": [
        "M15.5 13a3.5 3.5 0 0 0 -3.5 3.5v1a3.5 3.5 0 0 0 7 0v-1.8",
        "M8.5 13a3.5 3.5 0 0 1 3.5 3.5v1a3.5 3.5 0 0 1 -7 0v-1.8",
        "M17.5 16a3.5 3.5 0 0 0 0 -7h-.5",
        "M19 9.3v-2.8a3.5 3.5 0 0 0 -7 0",
        "M6.5 16a3.5 3.5 0 0 1 0 -7h.5",
        "M5 9.3v-2.8a3.5 3.5 0 0 1 7 0v10",
    ],
    "genai": [
        "M16 18a2 2 0 0 1 2 2a2 2 0 0 1 2 -2a2 2 0 0 1 -2 -2a2 2 0 0 1 -2 2m0 -12a2 2 0 0 1 2 2a2 2 0 0 1 2 -2a2 2 0 0 1 -2 -2a2 2 0 0 1 -2 2m-7 12a6 6 0 0 1 6 -6a6 6 0 0 1 -6 -6a6 6 0 0 1 -6 6a6 6 0 0 1 6 6",
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
        "M21.121 20.121a3 3 0 1 0 -4.242 0c.418 .419 1.125 1.045 2.121 1.879c1.051 -.89 1.759 -1.516 2.121 -1.879",
        "M19 18v.01",
    ],
    "career-move": [
        "M18 15l3 -3l-3 -3",
        "M3 12a2 2 0 1 0 4 0a2 2 0 1 0 -4 0",
        "M7 12h14",
    ],
    "glossary-basics": [
        "M10 19h-6a1 1 0 0 1 -1 -1v-14a1 1 0 0 1 1 -1h6a2 2 0 0 1 2 2a2 2 0 0 1 2 -2h6a1 1 0 0 1 1 1v14a1 1 0 0 1 -1 1h-6a2 2 0 0 0 -2 2a2 2 0 0 0 -2 -2",
        "M12 5v16",
    ],
    "glossary-models": [
        "M11 12a1 1 0 1 0 2 0a1 1 0 1 0 -2 0",
        "M7 12a5 5 0 1 0 10 0a5 5 0 1 0 -10 0",
        "M3 12a9 9 0 1 0 18 0a9 9 0 1 0 -18 0",
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
        "M9 16h1",
        "M14 8h1",
        "M14 12h1",
        "M14 16h1",
        "M5 21v-14a2 2 0 0 1 2 -2h10a2 2 0 0 1 2 2v14",
    ],
}


def render_svg(paths: list[str]) -> str:
    body = "\n".join(f'  <path d="{d}"/>' for d in paths)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"'
        f' stroke="{STROKE}" stroke-width="1.5" stroke-linecap="round"'
        f' stroke-linejoin="round" aria-hidden="true">\n{body}\n</svg>\n'
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for slug, paths in ICONS.items():
        (OUT / f"{slug}.svg").write_text(render_svg(paths), encoding="utf-8")
    print(f"wrote {len(ICONS)} icons to {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
