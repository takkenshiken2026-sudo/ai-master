#!/usr/bin/env python3
"""キャリア記事用の図解画像を生成する。"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
FONT_PATH = ROOT / "assets" / "fonts" / "NotoSansJP-Variable.ttf"

BLUE = "#1A5CDB"
BLUE_SOFT = "#EEF3FC"
WHITE = "#FFFFFF"
DARK = "#0F172A"
MUTED = "#64748B"
BORDER = "#E2E8F0"
ARROW_MUTED = "#94A3B8"

STEPS = [
    ("01", "データ", "収集", ""),
    ("02", "前処理", "", "特徴量設計"),
    ("03", "モデル", "学習", ""),
    ("04", "評価", "", "精度・再現率"),
    ("05", "本番", "実装", ""),
    ("06", "運用", "・改善", ""),
]


def hex_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


def noto(size: int, weight: int = 700) -> ImageFont.FreeTypeFont:
    font = ImageFont.truetype(str(FONT_PATH), size)
    font.set_variation_by_axes([weight])
    return font


def draw_rounded_rect(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int, int, int],
    radius: int,
    fill: str,
    outline: str | None = None,
    width: int = 1,
) -> None:
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def make_role_flow(path: Path, width: int = 960, height: int = 300) -> None:
    img = Image.new("RGB", (width, height), hex_rgb(BLUE_SOFT))
    draw = ImageDraw.Draw(img)
    draw_rounded_rect(draw, (0, 0, width - 1, height - 1), 16, WHITE, BORDER, 1)

    title_font = noto(18, 700)
    sub_font = noto(12, 500)
    num_font = noto(13, 700)
    label_font = noto(14, 700)
    note_font = noto(12, 500)

    draw.text((width // 2, 28), "AIエンジニアの典型的な業務フロー", fill=hex_rgb(DARK), font=title_font, anchor="mm")
    draw.text((width // 2, 50), "PoCから本番運用まで、実装と改善を繰り返す", fill=hex_rgb(MUTED), font=sub_font, anchor="mm")

    box_w, box_h = 128, 88
    gap = 24
    total_w = len(STEPS) * box_w + (len(STEPS) - 1) * gap
    start_x = (width - total_w) // 2
    y = 88

    centers: list[int] = []
    for i, (num, line1, line2, note) in enumerate(STEPS):
        x = start_x + i * (box_w + gap)
        centers.append(x + box_w // 2)
        highlight = i == 4
        fill = hex_rgb(BLUE) if highlight else WHITE
        text_color = WHITE if highlight else hex_rgb(DARK)
        draw_rounded_rect(draw, (x, y, x + box_w, y + box_h), 12, fill, BLUE, 2)
        draw.text((x + box_w // 2, y + 24), num, fill=text_color if highlight else hex_rgb(BLUE), font=num_font, anchor="mm")
        draw.text((x + box_w // 2, y + 46), line1, fill=text_color, font=label_font, anchor="mm")
        if line2:
            draw.text((x + box_w // 2, y + 66), line2, fill=text_color, font=label_font, anchor="mm")
        elif note:
            draw.text((x + box_w // 2, y + 66), note, fill=hex_rgb(MUTED) if not highlight else WHITE, font=note_font, anchor="mm")

    arrow_y = y + box_h // 2
    for i in range(len(centers) - 1):
        x1 = centers[i] + box_w // 2 + 4
        x2 = centers[i + 1] - box_w // 2 - 4
        draw.line((x1, arrow_y, x2 - 8, arrow_y), fill=hex_rgb(BLUE), width=2)
        draw.polygon([(x2, arrow_y), (x2 - 10, arrow_y - 5), (x2 - 10, arrow_y + 5)], fill=hex_rgb(BLUE))

    loop_y = y + box_h + 36
    draw.arc((80, loop_y - 20, width - 80, loop_y + 70), 20, 160, fill=hex_rgb(ARROW_MUTED), width=2)
    draw.polygon([(88, loop_y + 8), (98, loop_y + 2), (98, loop_y + 14)], fill=hex_rgb(ARROW_MUTED))
    draw.text((width // 2, height - 22), "監視・再学習・A/Bテストで継続改善", fill=hex_rgb(MUTED), font=note_font, anchor="mm")

    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, format="PNG", optimize=True)


def main() -> None:
    out = ROOT / "assets" / "images" / "career" / "ai-engineer" / "role-flow.png"
    make_role_flow(out)
    print(f"Generated {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
