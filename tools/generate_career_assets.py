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
    "data-scientist": FlowSpec(
        title="データサイエンティストの典型的な業務フロー",
        subtitle="問いを立て、データで答え、意思決定につなげる",
        steps=[
            ("01", "課題", "整理", "仮説設定"),
            ("02", "探索", "分析", "EDA"),
            ("03", "モデル", "構築", "統計・ML"),
            ("04", "示唆", "抽出", ""),
            ("05", "施策", "提案", "意思決定"),
            ("06", "効果", "検証", "A/Bテスト"),
        ],
        highlight_index=4,
        loop_caption="結果をフィードバックし次の問いへ",
    ),
    "generative-ai-engineer": FlowSpec(
        title="生成AIエンジニアの典型的な業務フロー",
        subtitle="LLMを業務システムに安全に組み込む",
        steps=[
            ("01", "要件", "定義", "ユースケース"),
            ("02", "プロンプト", "設計", ""),
            ("03", "RAG", "構築", "検索連携"),
            ("04", "評価", "", "品質計測"),
            ("05", "本番", "実装", "API統合"),
            ("06", "監視", "・改善", ""),
        ],
        highlight_index=4,
        loop_caption="ログ分析でプロンプトと知識ベースを更新",
    ),
    "mlops-engineer": FlowSpec(
        title="MLOpsエンジニアの典型的な業務フロー",
        subtitle="モデルライフサイクルを継続的に回す",
        steps=[
            ("01", "実験", "管理", "再現性"),
            ("02", "学習", "CI/CD", ""),
            ("03", "モデル", "登録", "バージョン"),
            ("04", "デプロイ", "", "自動配信"),
            ("05", "監視", "", "ドリフト検知"),
            ("06", "再学習", "・改善", ""),
        ],
        highlight_index=4,
        loop_caption="劣化検知でパイプラインを再実行",
    ),
    "data-analyst": FlowSpec(
        title="データアナリストの典型的な業務フロー",
        subtitle="KPIを追い、可視化して意思決定を支える",
        steps=[
            ("01", "要件", "確認", "KPI定義"),
            ("02", "データ", "取得", "SQL"),
            ("03", "加工", "集計", ""),
            ("04", "可視化", "", "BI・グラフ"),
            ("05", "報告", "共有", "ストーリー"),
            ("06", "改善", "追跡", "フォロー"),
        ],
        highlight_index=4,
        loop_caption="フィードバックで指標と集計を更新",
    ),
    "data-scientist-vs-analyst": FlowSpec(
        title="DSとアナリストを選ぶときの整理フロー",
        subtitle="分析の深さと業務イメージで方向性を決める",
        steps=[
            ("01", "関心", "整理", "好きな作業"),
            ("02", "JD", "読解", "業務イメージ"),
            ("03", "スキル", "棚卸し", "SQL・統計"),
            ("04", "学習", "計画", "ギャップ"),
            ("05", "実践", "", "ポートフォリオ"),
            ("06", "応募", "戦略", "職種選定"),
        ],
        highlight_index=4,
        loop_caption="結果を見て学習と狙い職を調整",
    ),
    "ai-engineer-vs-mlops": FlowSpec(
        title="3職種を選ぶときの整理フロー",
        subtitle="実装・パイプライン・運用のどこに重心を置くか",
        steps=[
            ("01", "関心", "整理", "得意領域"),
            ("02", "JD", "読解", "業務範囲"),
            ("03", "スキル", "棚卸し", "Python/Infra"),
            ("04", "学習", "計画", "優先順位"),
            ("05", "実践", "", "ポートフォリオ"),
            ("06", "応募", "戦略", "職種選定"),
        ],
        highlight_index=4,
        loop_caption="実務フィードバックで方向を微調整",
    ),
    "prompt-engineer": FlowSpec(
        title="プロンプトエンジニアの典型的な業務フロー",
        subtitle="指示設計から評価・改善を繰り返す",
        steps=[
            ("01", "業務", "整理", "ユースケース"),
            ("02", "プロンプト", "設計", "Few-shot"),
            ("03", "テスト", "実行", ""),
            ("04", "評価", "", "品質指標"),
            ("05", "改善", "反復", ""),
            ("06", "展開", "", "業務組込"),
        ],
        highlight_index=4,
        loop_caption="ログと評価でプロンプトを更新",
    ),
    "ai-product-manager": FlowSpec(
        title="AI PMの典型的な業務フロー",
        subtitle="仮説からロードマップ、リリースまでを牽引する",
        steps=[
            ("01", "課題", "発見", "ユーザー調査"),
            ("02", "仮説", "設定", "AI適用"),
            ("03", "要件", "定義", "成功指標"),
            ("04", "PoC", "評価", "Go/No-Go"),
            ("05", "ロード", "マップ", "優先順位"),
            ("06", "リリース", "・改善", ""),
        ],
        highlight_index=3,
        loop_caption="指標とフィードバックでロードマップ更新",
    ),
    "beginner-ai-roles-top5": FlowSpec(
        title="未経験者の職種選びフロー",
        subtitle="興味と学習コストで最初の一歩を決める",
        steps=[
            ("01", "興味", "整理", "好きな作業"),
            ("02", "学習", "時間", "確認"),
            ("03", "スキル", "棚卸し", ""),
            ("04", "候補", "職種", "絞り込み"),
            ("05", "学習", "開始", "資格・実践"),
            ("06", "応募", "・実践", ""),
        ],
        highlight_index=3,
        loop_caption="結果を見て候補職種を調整",
    ),
    "g-kentei-career": FlowSpec(
        title="G検定取得後のキャリア設計フロー",
        subtitle="資格を職種選びとアピールに活かす",
        steps=[
            ("01", "学習", "", "G検定範囲"),
            ("02", "合格", "", "知識整理"),
            ("03", "職種", "候補", "整理"),
            ("04", "履歴書", "", "職務経歴"),
            ("05", "面接", "アピール", ""),
            ("06", "実務", "・継続", "学習"),
        ],
        highlight_index=4,
        loop_caption="実務ギャップを学習で埋める",
    ),
    "beginner-learning-roadmap": FlowSpec(
        title="未経験者のAI学習ロードマップ",
        subtitle="基礎から実践・資格まで段階的に進む",
        steps=[
            ("01", "環境", "準備", "Python/Git"),
            ("02", "基礎", "用語", "G検定"),
            ("03", "データ", "操作", "SQL"),
            ("04", "ML", "基礎", "実装"),
            ("05", "生成AI", "活用", ""),
            ("06", "応募", "・実践", ""),
        ],
        highlight_index=3,
        loop_caption="職種に応じて枝分かれ",
    ),
    "genai-passport-career": FlowSpec(
        title="生成AIパスポート取得後の学習ロードマップ",
        subtitle="資格を次のスキルとキャリアに接続する",
        steps=[
            ("01", "知識", "整理", "合格範囲"),
            ("02", "実務", "適用", "業務活用"),
            ("03", "深掘り", "", "RAG・倫理"),
            ("04", "実装", "基礎", "API連携"),
            ("05", "職種", "候補", "整理"),
            ("06", "継続", "学習", ""),
        ],
        highlight_index=3,
        loop_caption="G検定などと組み合わせて拡張",
    ),
    "ai-portfolio-guide": FlowSpec(
        title="AI職向けポートフォリオの作り方",
        subtitle="採用側が見るポイントを押さえる",
        steps=[
            ("01", "題材", "選定", "職種別"),
            ("02", "実装", "公開", "GitHub"),
            ("03", "説明", "整備", "README"),
            ("04", "見せ方", "", "Kaggle等"),
            ("05", "面接", "想定", "質問"),
            ("06", "改善", "継続", "更新"),
        ],
        highlight_index=2,
        loop_caption="フィードバックで磨き込む",
    ),
    "ai-side-job-prep": FlowSpec(
        title="AI副業を始める前の準備と時間の使い方",
        subtitle="本業と両立しながら案件獲得へ",
        steps=[
            ("01", "目的", "整理", "副業方針"),
            ("02", "就規", "確認", "競業避止"),
            ("03", "スキル", "整備", "成果物"),
            ("04", "時間", "確保", "週次計画"),
            ("05", "案件", "獲得", "小規模から"),
            ("06", "継続", "改善", "実績化"),
        ],
        highlight_index=3,
        loop_caption="本業を守りながら積み上げる",
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
