#!/usr/bin/env python3
"""公開済みツール記事のヒーロー画像・アイコン解像度を検証する。

使い方:
  python3 tools/check_article_images.py
  python3 tools/check_article_images.py --tool flux
  python3 tools/check_article_images.py --strict   # 警告も失敗扱い
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = ROOT / "tools"
IMAGES_DIR = ROOT / "assets" / "images" / "tools"

# 記事 HTML 上のヒーロー表示幅に対する最低ライン
MIN_APP_ICON_PX = 128
WARN_APP_ICON_PX = 180
MIN_OG_MAX_PX = 512
WARN_OG_WIDTH_PX = 800
MIN_SVG_BYTES = 150


@dataclass
class Issue:
    level: str  # ERROR | WARN
    tool_id: str
    asset: str
    message: str


@dataclass
class CheckResult:
    tool_id: str
    app_icon: Path | None = None
    og_hero: Path | None = None
    issues: list[Issue] = field(default_factory=list)


def article_ids() -> list[str]:
    return sorted(p.parent.name for p in TOOLS_DIR.glob("*/index.html"))


def url_to_local_path(url: str) -> Path | None:
    prefix = "https://ai-master.jp/assets/images/tools/"
    if url.startswith(prefix):
        return IMAGES_DIR / url.removeprefix(prefix)
    match = re.search(r"assets/images/tools/(.+)$", url)
    if match:
        return IMAGES_DIR / match.group(1)
    return None


def resolve_src(article_dir: Path, src: str) -> Path | None:
    src = src.strip()
    if src.startswith("../../assets/"):
        return ROOT / src.removeprefix("../../")
    if src.startswith("/"):
        return ROOT / src.lstrip("/")
    return (article_dir / src).resolve()


def parse_article(tool_id: str) -> tuple[Path | None, Path | None]:
    html_path = TOOLS_DIR / tool_id / "index.html"
    text = html_path.read_text(encoding="utf-8")

    app_icon: Path | None = None
    app_match = re.search(
        r'<img[^>]+class="[^"]*tool-hero-app-icon[^"]*"[^>]+src="([^"]+)"',
        text,
    )
    if not app_match:
        app_match = re.search(
            r'<img[^>]+src="([^"]+)"[^>]+class="[^"]*tool-hero-app-icon',
            text,
        )
    if app_match:
        app_icon = resolve_src(html_path.parent, app_match.group(1))

    og_hero: Path | None = None
    visual_match = re.search(
        r'<figure[^>]*class="[^"]*tool-hero-visual[^"]*"[^>]*>\s*<img[^>]+src="([^"]+)"',
        text,
        re.S,
    )
    if visual_match:
        og_hero = resolve_src(html_path.parent, visual_match.group(1))

    og_meta = re.search(
        r'<meta[^>]+property="og:image"[^>]+content="([^"]+)"',
        text,
        re.I,
    )
    if not og_meta:
        og_meta = re.search(
            r'<meta[^>]+content="([^"]+)"[^>]+property="og:image"',
            text,
            re.I,
        )
    if og_meta:
        meta_path = url_to_local_path(og_meta.group(1))
        if og_hero and meta_path and og_hero != meta_path:
            pass  # mismatch reported later
        elif meta_path and not og_hero:
            og_hero = meta_path

    return app_icon, og_hero


def is_html_payload(path: Path) -> bool:
    head = path.read_bytes()[:256].lstrip().lower()
    return head.startswith((b"<!doctype", b"<html"))


def check_raster(path: Path) -> tuple[int, int]:
    from PIL import Image

    with Image.open(path) as img:
        return img.size


def check_asset(
    result: CheckResult,
    label: str,
    path: Path | None,
    *,
    is_og: bool,
) -> None:
    if path is None:
        result.issues.append(
            Issue("ERROR", result.tool_id, label, f"{label} のパスが HTML から取得できません")
        )
        return

    rel = path.relative_to(ROOT)
    if not path.is_file():
        result.issues.append(
            Issue("ERROR", result.tool_id, label, f"ファイルがありません: {rel}")
        )
        return

    suffix = path.suffix.lower()
    if suffix == ".svg":
        size = path.stat().st_size
        if size < MIN_SVG_BYTES or "<svg" not in path.read_text(encoding="utf-8", errors="ignore").lower():
            result.issues.append(
                Issue("ERROR", result.tool_id, label, f"SVG が不正です: {rel} ({size}B)")
            )
        return

    if is_html_payload(path):
        result.issues.append(
            Issue("ERROR", result.tool_id, label, f"画像ではなく HTML です: {rel}")
        )
        return

    try:
        width, height = check_raster(path)
    except Exception as exc:
        result.issues.append(
            Issue("ERROR", result.tool_id, label, f"画像を開けません: {rel} ({exc})")
        )
        return

    max_px = max(width, height)
    kb = path.stat().st_size // 1024
    dim = f"{width}x{height} {kb}KB"

    if is_og:
        if max_px < MIN_OG_MAX_PX:
            result.issues.append(
                Issue(
                    "ERROR",
                    result.tool_id,
                    label,
                    f"解像度不足（最大辺 {max_px}px < {MIN_OG_MAX_PX}px）: {rel} {dim}",
                )
            )
        elif width < WARN_OG_WIDTH_PX:
            result.issues.append(
                Issue(
                    "WARN",
                    result.tool_id,
                    label,
                    f"ヒーロー表示 800px に対してやや小さい（幅 {width}px）: {rel} {dim}",
                )
            )
    else:
        if max_px < MIN_APP_ICON_PX:
            result.issues.append(
                Issue(
                    "ERROR",
                    result.tool_id,
                    label,
                    f"解像度不足（最大辺 {max_px}px < {MIN_APP_ICON_PX}px）: {rel} {dim}",
                )
            )
        elif max_px < WARN_APP_ICON_PX:
            result.issues.append(
                Issue(
                    "WARN",
                    result.tool_id,
                    label,
                    f"アイコンがやや小さい（最大辺 {max_px}px）: {rel} {dim}",
                )
            )


def check_tool(tool_id: str) -> CheckResult:
    result = CheckResult(tool_id=tool_id)
    app_icon, og_hero = parse_article(tool_id)
    result.app_icon = app_icon
    result.og_hero = og_hero

    check_asset(result, "app-icon", app_icon, is_og=False)
    check_asset(result, "og-hero", og_hero, is_og=True)

    html_path = TOOLS_DIR / tool_id / "index.html"
    text = html_path.read_text(encoding="utf-8")
    og_meta = re.search(
        r'<meta[^>]+property="og:image"[^>]+content="([^"]+)"',
        text,
        re.I,
    )
    if og_meta and og_hero:
        meta_path = url_to_local_path(og_meta.group(1))
        if meta_path and meta_path != og_hero:
            result.issues.append(
                Issue(
                    "ERROR",
                    tool_id,
                    "og-hero",
                    f"og:image とヒーロー画像が不一致: meta={meta_path.name} visual={og_hero.name}",
                )
            )

    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="ツール記事の画像解像度を検証")
    parser.add_argument("--tool", help="特定 ID のみ検証（例: flux）")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="警告もエラー扱いにする",
    )
    args = parser.parse_args()

    ids = [args.tool] if args.tool else article_ids()
    if args.tool and not (TOOLS_DIR / args.tool / "index.html").is_file():
        print(f"記事がありません: tools/{args.tool}/index.html", file=sys.stderr)
        return 1

    results = [check_tool(tool_id) for tool_id in ids]
    ok = 0

    for result in results:
        tool_errors = [i for i in result.issues if i.level == "ERROR"]
        if not result.issues:
            app = result.app_icon.name if result.app_icon else "?"
            og = result.og_hero.name if result.og_hero else "?"
            print(f"OK  {result.tool_id:22} {app} + {og}")
            ok += 1
            continue

        status = "NG" if tool_errors else "WARN"
        print(f"{status} {result.tool_id}")
        for issue in result.issues:
            prefix = "  !" if issue.level == "WARN" else "  x"
            print(f"{prefix} [{issue.level}] {issue.asset}: {issue.message}")

    errors = sum(
        1
        for r in results
        for i in r.issues
        if i.level == "ERROR" or (args.strict and i.level == "WARN")
    )
    warns = sum(
        1 for r in results for i in r.issues if i.level == "WARN" and not args.strict
    )

    print()
    print(f"記事 {len(ids)} 本 — OK {ok} / 警告 {warns} / エラー {errors}")
    if errors:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
