#!/usr/bin/env python3
"""ツール記事のカナ表記・別名を補強して日本語検索の取りこぼしを減らす。

Search Console のクエリ分析で、ツール名をカタカナや表記ゆれで検索する流入
（例: 「ディープル翻訳」→ tools/deepl/、掲載順位 61 位）が確認された。
本サイトのツール記事はリード文で「<strong>名称</strong>（カナ）」と読みを添える
規約になっているが、一部の記事でこのカナ表記が抜けていた。

このスクリプトは冪等で、対象ツールに対して次を補う:

1. リード文の先頭 ``<strong>名称</strong>`` 直後にカナ読み ``（カナ）`` を挿入
   （すでに ``（`` が続く場合はスキップ）。
2. JSON-LD の SoftwareApplication エンティティに ``alternateName``（カナ・
   英語表記ゆれ）を付与（すでにある場合はスキップ）。

  python3 tools/enrich_tool_names.py

対象は Search Console でカナ・表記ゆれの需要が確認できたツールに限定する。
読みは標準的な日本語表記のみを用い、推測が必要なものは含めない。
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = ROOT / "tools"

# id: {"name": SoftwareApplication の name, "lead_kana": リード文へ挿入する読み,
#      "alt": JSON-LD alternateName に足す別名（カナ・表記ゆれ）}
# lead_kana を None にすると本文カナ挿入はスキップ（既にカナがある記事）。
TOOLS = {
    "deepl": {
        "name": "DeepL",
        "lead_kana": "ディープル",
        "alt": ["ディープル", "ディープエル", "DeepL翻訳"],
    },
    "ollama": {
        "name": "Ollama",
        "lead_kana": "オラマ",
        "alt": ["オラマ"],
    },
    "capcut": {
        "name": "CapCut",
        "lead_kana": "キャップカット",
        "alt": ["キャップカット"],
    },
    "github-copilot": {
        "name": "GitHub Copilot",
        "lead_kana": None,  # 既に（ギットハブ・コパイロット）あり
        "alt": ["ギットハブコパイロット", "GitHubコパイロット"],
    },
    "grok": {
        "name": "Grok",
        "lead_kana": None,  # 既に（グロック）あり
        "alt": ["グロック"],
    },
    "copilot": {
        "name": "Microsoft Copilot",
        "lead_kana": None,  # 既に（マイクロソフト・コパイロット）あり
        "alt": ["マイクロソフトコパイロット", "コパイロット"],
    },
    "gamma": {
        "name": "Gamma",
        "lead_kana": None,  # 既に（ガンマ）あり
        "alt": ["ガンマ"],
    },
    # カナ規約が抜けていたツール（読みが標準的で確実なもののみ。
    # Suno/Udio/Veo/Zapier/ElevenLabs 等、読みが曖昧なものは意図的に除外）。
    "claude": {"name": "Claude", "lead_kana": "クロード", "alt": ["クロード"]},
    "claude-code": {
        "name": "Claude Code",
        "lead_kana": "クロードコード",
        "alt": ["クロードコード"],
    },
    "descript": {"name": "Descript", "lead_kana": "ディスクリプト", "alt": ["ディスクリプト"]},
    "devin": {"name": "Devin", "lead_kana": "デビン", "alt": ["デビン"]},
    "heygen": {"name": "HeyGen", "lead_kana": "ヘイジェン", "alt": ["ヘイジェン"]},
    "pika": {"name": "Pika", "lead_kana": "ピカ", "alt": ["ピカ"]},
    "runway": {"name": "Runway", "lead_kana": "ランウェイ", "alt": ["ランウェイ"]},
    "whisper": {"name": "Whisper", "lead_kana": "ウィスパー", "alt": ["ウィスパー"]},
    "magnific": {"name": "Magnific", "lead_kana": "マグニフィック", "alt": ["マグニフィック"]},
    "manus": {"name": "Manus", "lead_kana": "マナス", "alt": ["マナス"]},
    "recraft": {"name": "Recraft", "lead_kana": "リクラフト", "alt": ["リクラフト"]},
    "warp": {"name": "Warp", "lead_kana": "ワープ", "alt": ["ワープ"]},
    "skywork": {"name": "Skywork", "lead_kana": "スカイワーク", "alt": ["スカイワーク"]},
    "sora-2": {"name": "Sora 2", "lead_kana": "ソラ", "alt": ["ソラ", "Sora"]},
}


def add_lead_kana(text: str, name: str, kana: str) -> tuple[str, bool]:
    """リード文先頭の <strong>{name}</strong> 直後にカナを挿入。"""
    lead_idx = text.find('<p class="tool-lead">')
    if lead_idx < 0:
        return text, False
    strong = f"<strong>{name}</strong>"
    s_idx = text.find(strong, lead_idx)
    if s_idx < 0:
        return text, False
    after = s_idx + len(strong)
    if text[after : after + 1] == "（":  # 既にカナ・注記あり
        return text, False
    insert = f"（{kana}）"
    return text[:after] + insert + text[after:], True


def add_alternate_name(text: str, name: str, alt: list[str]) -> tuple[str, bool]:
    """SoftwareApplication エンティティに alternateName を付与。"""
    # about 参照ではなく applicationCategory を持つ本体エンティティを対象にする。
    pattern = re.compile(
        r'("@type":\s*"SoftwareApplication",\n)(\s*)("name":\s*'
        + re.escape(json.dumps(name, ensure_ascii=False))
        + r",\n)"
    )
    m = pattern.search(text)
    if not m:
        return text, False
    indent = m.group(2)
    # 既に alternateName があるならスキップ（name 行の直後を確認）
    tail = text[m.end() : m.end() + 120]
    if '"alternateName"' in tail:
        return text, False
    alt_json = json.dumps(alt, ensure_ascii=False)
    injected = f'{indent}"alternateName": {alt_json},\n'
    idx = m.end()
    return text[:idx] + injected + text[idx:], True


def main() -> None:
    patched = 0
    for tool_id, info in TOOLS.items():
        path = TOOLS_DIR / tool_id / "index.html"
        if not path.is_file():
            print(f"skip (missing): {tool_id}")
            continue
        text = path.read_text(encoding="utf-8")
        changed = False

        if info["lead_kana"]:
            text, did = add_lead_kana(text, info["name"], info["lead_kana"])
            if did:
                print(f"lead kana: {tool_id} （{info['lead_kana']}）")
                changed = True

        text, did = add_alternate_name(text, info["name"], info["alt"])
        if did:
            print(f"alternateName: {tool_id} {info['alt']}")
            changed = True

        if changed:
            path.write_text(text, encoding="utf-8")
            patched += 1

    print(f"patched {patched} tool pages")


if __name__ == "__main__":
    main()
