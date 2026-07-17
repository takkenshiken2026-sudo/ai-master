#!/usr/bin/env python3
"""試験ハブページに <h1> を含む静的ヒーローを埋め込む。

exams/{exam}/index.html のヒーローは exam-hero.js が exam-profiles.json から
クライアントサイドで描画しており、静的 HTML には <h1> が存在しなかった。
主要ハブページの主見出しを CSR 依存にするのは、クロールのレンダリング予算・
fetch 失敗時のリスクがあるため、静的フォールバックを埋め込む
（progressive enhancement: JS は従来どおり innerHTML を上書きするので二重にならない）。

出力マークアップは exam-hero.js の renderHero(profile, "hub") と一致させ、
JS 実行後の再描画で見た目が変わらないようにする。

  python3 tools/render_exam_hero_static.py

冪等: すでに data-exam-hero-static="1" が付いていれば何もしない。
"""

from __future__ import annotations

import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILES = json.loads((ROOT / "assets/data/exam-profiles.json").read_text(encoding="utf-8"))

# インデックス対象のハブページのみ（練習/演習ページは noindex）
HUB_PAGES = {
    "g-kentei": ROOT / "exams/g-kentei/index.html",
    "genai-passport": ROOT / "exams/genai-passport/index.html",
}


def esc(s: str) -> str:
    # exam-hero.js の escapeHtml と同等（& < > " をエスケープ）
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def render_stats(stats: list[dict]) -> str:
    out = []
    for stat in stats:
        note = f"（{stat['note']}）" if stat.get("note") else ""
        label = esc(f"{stat.get('label','')}{note}")
        out.append(
            f"""
        <div class="exam-hero__stat">
          <p class="exam-hero__stat-line">
            <span class="exam-hero__stat-label">{label}</span>
            <span class="exam-hero__stat-value">{esc(stat.get('value',''))}</span>
          </p>
        </div>"""
        )
    return "".join(out)


def render_hero_inner(profile: dict) -> str:
    hub = profile.get("hub") or {}
    title = hub.get("title") or f"{profile.get('examName','')} 試験対策"
    lede_parts = list(profile.get("lede") or [])
    if hub.get("hint"):
        lede_parts.append(hub["hint"])
    lede = "".join(
        f'<p class="exam-hero__lede">{esc(p)}</p>' for p in lede_parts
    )
    return f"""
      <div class="exam-hero__inner">
        <p class="exam-hero__org">{esc(profile.get('org',''))}</p>
        <h1 class="exam-hero__title">{esc(title)}</h1>
        <div class="exam-hero__copy">{lede}</div>
        <div class="exam-hero__stats" aria-label="試験概要">
          {render_stats(profile.get('stats') or [])}
        </div>
        <p class="exam-hero__disclaimer">当サイトの問題は本番形式の模擬問題です（公式の過去問ではありません）。</p>
      </div>
    """


def patch(exam_id: str, path: Path) -> bool:
    if not path.is_file():
        print(f"skip (missing): {path}")
        return False
    text = path.read_text(encoding="utf-8")
    if 'data-exam-hero-static="1"' in text:
        print(f"skip (already static): {exam_id}")
        return False
    profile = PROFILES.get(exam_id)
    if not profile:
        print(f"skip (no profile): {exam_id}")
        return False

    # 空の hidden な .exam-hero div を、静的フォールバック入りの div に置換
    pattern = re.compile(
        r'<div\s+class="exam-hero"\s+data-exam-hero="'
        + re.escape(exam_id)
        + r'"[^>]*>\s*</div>'
    )
    m = pattern.search(text)
    if not m:
        print(f"skip (hero div not found / not empty): {exam_id}")
        return False

    inner = render_hero_inner(profile)
    replacement = (
        f'<div\n    class="exam-hero"\n'
        f'    data-exam-hero="{exam_id}"\n'
        f'    data-exam-mode="hub"\n'
        f'    data-profiles-url="../../assets/data/exam-profiles.json"\n'
        f'    data-exam-hero-static="1"\n'
        f'  >{inner}</div>'
    )
    text = text[: m.start()] + replacement + text[m.end() :]
    path.write_text(text, encoding="utf-8")
    print(f"static hero: {exam_id} <h1>{profile.get('hub',{}).get('title')}</h1>")
    return True


def main() -> None:
    n = 0
    for exam_id, path in HUB_PAGES.items():
        if patch(exam_id, path):
            n += 1
    print(f"patched {n} hub pages")


if __name__ == "__main__":
    main()
