#!/usr/bin/env python3
"""キャリア記事用の図解画像を生成する。"""

from __future__ import annotations

from dataclasses import dataclass
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

DISPLAY_WIDTH = 960
DISPLAY_HEIGHT = 300
RENDER_SCALE = 3


@dataclass(frozen=True)
class FlowSpec:
    title: str
    subtitle: str
    steps: list[tuple[str, str, str, str]]
    highlight_index: int
    loop_caption: str


FLOWS: dict[str, FlowSpec] = {
    "ai-engineer": FlowSpec(
        title="AIエンジニアの典型的な業務フロー",
        subtitle="PoCから本番運用まで、実装と改善を繰り返す",
        steps=[
            ("01", "データ", "収集", ""),
            ("02", "前処理", "", "特徴量設計"),
            ("03", "モデル", "学習", ""),
            ("04", "評価", "", "精度・再現率"),
            ("05", "本番", "実装", ""),
            ("06", "運用", "・改善", ""),
        ],
        highlight_index=4,
        loop_caption="監視・再学習・A/Bテストで継続改善",
    ),
    "machine-learning-engineer": FlowSpec(
        title="機械学習エンジニアの典型的な業務フロー",
        subtitle="データパイプラインとモデル配信を一連で回す",
        steps=[
            ("01", "データ", "取得", "ETL・連携"),
            ("02", "特徴量", "設計", ""),
            ("03", "モデル", "学習", "検証"),
            ("04", "オフライン", "評価", ""),
            ("05", "デプロイ", "", "推論API"),
            ("06", "監視", "・再学習", ""),
        ],
        highlight_index=4,
        loop_caption="メトリクス劣化を検知しパイプラインを更新",
    ),
}


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


def make_role_flow(
    path: Path,
    spec: FlowSpec,
    width: int = DISPLAY_WIDTH,
    height: int = DISPLAY_HEIGHT,
    scale: int = RENDER_SCALE,
) -> None:
    s = scale
    img = Image.new("RGB", (width * s, height * s), hex_rgb(BLUE_SOFT))
    draw = ImageDraw.Draw(img)
    draw_rounded_rect(draw, (0, 0, width * s - 1, height * s - 1), 16 * s, WHITE, BORDER, s)

    title_font = noto(18 * s, 700)
    sub_font = noto(12 * s, 500)
    num_font = noto(13 * s, 700)
    label_font = noto(14 * s, 700)
    note_font = noto(11 * s, 500)

    draw.text((width * s // 2, 28 * s), spec.title, fill=hex_rgb(DARK), font=title_font, anchor="mm")
    draw.text((width * s // 2, 50 * s), spec.subtitle, fill=hex_rgb(MUTED), font=sub_font, anchor="mm")

    box_w, box_h = 128 * s, 88 * s
    gap = 24 * s
    total_w = len(spec.steps) * box_w + (len(spec.steps) - 1) * gap
    start_x = (width * s - total_w) // 2
    y = 88 * s

    centers: list[int] = []
    for i, (num, line1, line2, note) in enumerate(spec.steps):
        x = start_x + i * (box_w + gap)
        centers.append(x + box_w // 2)
        highlight = i == spec.highlight_index
        fill = hex_rgb(BLUE) if highlight else WHITE
        text_color = WHITE if highlight else hex_rgb(DARK)
        draw_rounded_rect(draw, (x, y, x + box_w, y + box_h), 12 * s, fill, BLUE, 2 * s)
        draw.text(
            (x + box_w // 2, y + 24 * s),
            num,
            fill=text_color if highlight else hex_rgb(BLUE),
            font=num_font,
            anchor="mm",
        )
        draw.text((x + box_w // 2, y + 44 * s), line1, fill=text_color, font=label_font, anchor="mm")
        if line2:
            draw.text((x + box_w // 2, y + 62 * s), line2, fill=text_color, font=label_font, anchor="mm")
        if note:
            draw.text(
                (x + box_w // 2, y + 78 * s),
                note,
                fill=hex_rgb(MUTED) if not highlight else WHITE,
                font=note_font,
                anchor="mm",
            )

    arrow_y = y + box_h // 2
    for i in range(len(centers) - 1):
        x1 = centers[i] + box_w // 2 + 4 * s
        x2 = centers[i + 1] - box_w // 2 - 4 * s
        draw.line((x1, arrow_y, x2 - 8 * s, arrow_y), fill=hex_rgb(BLUE), width=2 * s)
        draw.polygon(
            [(x2, arrow_y), (x2 - 10 * s, arrow_y - 5 * s), (x2 - 10 * s, arrow_y + 5 * s)],
            fill=hex_rgb(BLUE),
        )

    loop_y = y + box_h + 36 * s
    draw.arc((80 * s, loop_y - 20 * s, width * s - 80 * s, loop_y + 70 * s), 20, 160, fill=hex_rgb(ARROW_MUTED), width=2 * s)
    draw.polygon(
        [(88 * s, loop_y + 8 * s), (98 * s, loop_y + 2 * s), (98 * s, loop_y + 14 * s)],
        fill=hex_rgb(ARROW_MUTED),
    )
    draw.text((width * s // 2, height * s - 22 * s), spec.loop_caption, fill=hex_rgb(MUTED), font=note_font, anchor="mm")

    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, format="PNG", compress_level=3)


def main() -> None:
    for article_id, spec in FLOWS.items():
        out = ROOT / "assets" / "images" / "career" / article_id / "role-flow.png"
        make_role_flow(out, spec)
        with Image.open(out) as im:
            print(f"Generated {out.relative_to(ROOT)} ({im.size[0]}x{im.size[1]})")


if __name__ == "__main__":
    main()
