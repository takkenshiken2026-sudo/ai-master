#!/usr/bin/env python3
"""AI Master ブランド用 OG 画像・ファビコンを生成する。"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
IMG = ROOT / "assets" / "images"
FONT_PATH = ROOT / "assets" / "fonts" / "NotoSansJP-Variable.ttf"

BLUE = "#1A5CDB"
BLUE_SOFT = "#EEF3FC"
WHITE = "#FFFFFF"
DARK = "#0F172A"
MUTED = "#64748B"


def hex_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


def draw_rounded_rect(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int, int, int],
    radius: int,
    fill: str,
) -> None:
    draw.rounded_rectangle(xy, radius=radius, fill=fill)


def noto_font(size: int, weight: int = 700) -> ImageFont.FreeTypeFont:
    font = ImageFont.truetype(str(FONT_PATH), size)
    font.set_variation_by_axes([weight])
    return font


def make_og_image(path: Path, width: int = 1200, height: int = 630) -> None:
    img = Image.new("RGB", (width, height), hex_rgb(BLUE_SOFT))
    draw = ImageDraw.Draw(img)

    draw_rounded_rect(draw, (56, 56, width - 56, height - 56), 32, WHITE)

    cx = width // 2
    cy = height // 2

    badge_w, badge_h = 96, 96
    badge_x = cx - 220
    badge_y = cy - 72
    draw_rounded_rect(
        draw,
        (badge_x, badge_y, badge_x + badge_w, badge_y + badge_h),
        24,
        hex_rgb(BLUE),
    )

    badge_font = noto_font(42, 700)
    draw.text(
        (badge_x + badge_w // 2, badge_y + badge_h // 2),
        "AI",
        fill=WHITE,
        font=badge_font,
        anchor="mm",
    )

    title_font = noto_font(88, 700)
    sub_font = noto_font(40, 500)

    title_y = badge_y + badge_h // 2
    draw.text((badge_x + badge_w + 32, title_y), "AI", fill=hex_rgb(DARK), font=title_font, anchor="lm")
    ai_bbox = draw.textbbox((0, 0), "AI", font=title_font)
    ai_w = ai_bbox[2] - ai_bbox[0]
    draw.text(
        (badge_x + badge_w + 32 + ai_w + 8, title_y),
        "マスター",
        fill=hex_rgb(BLUE),
        font=title_font,
        anchor="lm",
    )

    draw.text((cx, cy + 72), "AIスキルを、キャリアの武器に。", fill=hex_rgb(MUTED), font=sub_font, anchor="mm")

    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, format="JPEG", quality=92, optimize=True)
    img.save(path.with_suffix(".png"), format="PNG", optimize=True)


def make_icon(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    margin = max(2, size // 8)
    draw_rounded_rect(draw, (margin, margin, size - margin, size - margin), size // 5, hex_rgb(BLUE))
    font = noto_font(max(12, size // 3), 700)
    draw.text((size // 2, size // 2), "AI", fill=WHITE, font=font, anchor="mm")
    return img


def make_favicon_svg(path: Path) -> None:
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" role="img" aria-label="AI Master">
  <rect width="32" height="32" rx="7" fill="{BLUE}"/>
  <text x="16" y="21" text-anchor="middle" font-family="'Noto Sans JP', sans-serif" font-size="13" font-weight="700" fill="{WHITE}">AI</text>
</svg>
"""
    path.write_text(svg, encoding="utf-8")


def make_webmanifest(path: Path) -> None:
    content = """{
  "name": "AI Master",
  "short_name": "AI Master",
  "description": "AI関連資格の対策と学習プラットフォーム",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#EEF3FC",
  "theme_color": "#1A5CDB",
  "icons": [
    {
      "src": "/assets/images/icon-512.png",
      "sizes": "512x512",
      "type": "image/png"
    },
    {
      "src": "/assets/images/apple-touch-icon.png",
      "sizes": "180x180",
      "type": "image/png"
    }
  ]
}
"""
    path.write_text(content, encoding="utf-8")


def main() -> None:
    IMG.mkdir(parents=True, exist_ok=True)
    make_og_image(IMG / "og-default.jpg")
    make_icon(16).save(IMG / "favicon-16x16.png")
    make_icon(32).save(IMG / "favicon-32x32.png")
    make_icon(180).save(IMG / "apple-touch-icon.png")
    make_icon(512).save(IMG / "icon-512.png")
    make_favicon_svg(IMG / "favicon.svg")

    ico_sizes = [(16, 16), (32, 32), (48, 48)]
    icons = [make_icon(s).convert("RGBA") for s, _ in ico_sizes]
    icons[0].save(ROOT / "favicon.ico", format="ICO", sizes=ico_sizes)

    make_webmanifest(ROOT / "site.webmanifest")
    print("Generated brand assets in assets/images/ and site.webmanifest")


if __name__ == "__main__":
    main()
