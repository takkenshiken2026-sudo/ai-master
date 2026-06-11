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
    "manufacturing-to-ai-engineer": FlowSpec(
        title="製造業からAIエンジニアへ転職",
        subtitle="現場知識を強みにキャリアチェンジ",
        steps=[
            ("01", "強み", "整理", "現場知識"),
            ("02", "ギャップ", "把握", "スキル"),
            ("03", "学習", "計画", "Python/ML"),
            ("04", "実績", "作る", "ポートフォリオ"),
            ("05", "求人", "探す", "製造×AI"),
            ("06", "面接", "準備", "ストーリー"),
        ],
        highlight_index=2,
        loop_caption="社内DX経由も有効",
    ),
    "finance-data-scientist-career": FlowSpec(
        title="金融業界からデータサイエンティストへ",
        subtitle="ドメイン知識を強みにキャリアチェンジ",
        steps=[
            ("01", "強み", "整理", "金融知識"),
            ("02", "ギャップ", "把握", "統計/ML"),
            ("03", "学習", "計画", "Python/SQL"),
            ("04", "実績", "作る", "分析案件"),
            ("05", "求人", "探す", "金融×DS"),
            ("06", "面接", "準備", "仮説説明"),
        ],
        highlight_index=2,
        loop_caption="アナリスト経由も有効",
    ),
    "liberal-arts-to-ai": FlowSpec(
        title="文系からAI職へキャリアチェンジ",
        subtitle="現実的な職種と学習ステップ",
        steps=[
            ("01", "職種", "選定", "現実路線"),
            ("02", "強み", "整理", "文系スキル"),
            ("03", "学習", "計画", "基礎から"),
            ("04", "資格", "活用", "リテラシー"),
            ("05", "実績", "作る", "成果物"),
            ("06", "転職", "準備", "応募"),
        ],
        highlight_index=2,
        loop_caption="アナリスト・PM入口も有効",
    ),
    "sier-to-ai-startup": FlowSpec(
        title="SIer・SESからAIスタートアップへ",
        subtitle="準備期間とリスクを踏まえて動く",
        steps=[
            ("01", "現状", "整理", "強み/弱み"),
            ("02", "ギャップ", "把握", "プロダクト"),
            ("03", "学習", "計画", "ML/生成AI"),
            ("04", "実績", "作る", "ポートフォリオ"),
            ("05", "企業", "選ぶ", "フェーズ"),
            ("06", "転職", "実行", "面接"),
        ],
        highlight_index=3,
        loop_caption="中規模企業経由も有効",
    ),
    "second-career-ai": FlowSpec(
        title="第二新卒でAI業界へ",
        subtitle="25〜29歳のタイムライン",
        steps=[
            ("01", "現状", "整理", "経験棚卸し"),
            ("02", "職種", "選定", "入口決め"),
            ("03", "学習", "並行", "週次計画"),
            ("04", "実績", "作る", "ポートフォリオ"),
            ("05", "応募", "開始", "転職活動"),
            ("06", "入社", "後", "定着"),
        ],
        highlight_index=2,
        loop_caption="前職の強みを言語化",
    ),
    "ai-career-outlook-2026": FlowSpec(
        title="AI関連職の将来性2026",
        subtitle="伸びる職種と持続するスキル",
        steps=[
            ("01", "市場", "整理", "2026現状"),
            ("02", "職種", "比較", "需給"),
            ("03", "スキル", "評価", "持続性"),
            ("04", "学習", "優先", "投資先"),
            ("05", "リスク", "把握", "過熱"),
            ("06", "行動", "計画", "個人"),
        ],
        highlight_index=2,
        loop_caption="職種名よりスキル軸で",
    ),
    "ai-engineer-salary-trend": FlowSpec(
        title="AIエンジニア年収の推移と相場",
        subtitle="企業規模・経験年数別の見方",
        steps=[
            ("01", "相場", "把握", "全体レンジ"),
            ("02", "要因", "分解", "規模・地域"),
            ("03", "推移", "理解", "生成AI影響"),
            ("04", "求人", "読む", "JD・総額"),
            ("05", "交渉", "準備", "株式含む"),
            ("06", "記事", "使い分け", "職種ガイド"),
        ],
        highlight_index=2,
        loop_caption="総額で比較する",
    ),
    "overseas-ai-engineer-salary": FlowSpec(
        title="海外AIエンジニア年収と日本",
        subtitle="米国・欧州比較とリモートの現実",
        steps=[
            ("01", "日本", "相場", "把握"),
            ("02", "米国", "比較", "レンジ"),
            ("03", "欧州", "比較", "特徴"),
            ("04", "リモート", "検討", "日本居住"),
            ("05", "総額", "計算", "税・生活費"),
            ("06", "キャリア", "設計", "個人"),
        ],
        highlight_index=3,
        loop_caption="名目だけで比較しない",
    ),
    "ai-freelance-market": FlowSpec(
        title="AIフリーランス単価と案件",
        subtitle="スキル別相場と案件の取り方",
        steps=[
            ("01", "副業", "準備", "整備"),
            ("02", "単価", "把握", "スキル別"),
            ("03", "案件", "種類", "選ぶ"),
            ("04", "獲得", "チャネル", "探す"),
            ("05", "交渉", "実務", "契約"),
            ("06", "独立", "判断", "継続"),
        ],
        highlight_index=3,
        loop_caption="実績で単価を上げる",
    ),
    "grad-school-ai-worth": FlowSpec(
        title="大学院AI・ML進学の判断",
        subtitle="修士・博士と就職への影響",
        steps=[
            ("01", "目的", "明確化", "進学理由"),
            ("02", "修士", "検討", "2年コスト"),
            ("03", "博士", "検討", "研究志向"),
            ("04", "就職", "影響", "職種別"),
            ("05", "代替", "比較", "実務・資格"),
            ("06", "決断", "整理", "個人"),
        ],
        highlight_index=2,
        loop_caption="目的なく進むと損しやすい",
    ),
    "beginner-ai-certs-compare": FlowSpec(
        title="AI初心者の資格選びフロー",
        subtitle="目的と職種で第1候補を決める",
        steps=[
            ("01", "目的", "整理", "業務か転職か"),
            ("02", "職種", "確認", "エンジニアか"),
            ("03", "3資格", "比較", "特徴把握"),
            ("04", "第1候補", "決定", "学習開始"),
            ("05", "合格", "・活用", "履歴書"),
            ("06", "次の", "資格", "必要なら"),
        ],
        highlight_index=3,
        loop_caption="目的が変われば次の資格も見直す",
    ),
    "non-engineer-ai-certs": FlowSpec(
        title="非エンジニアのAI資格選び",
        subtitle="文系・ビジネス職が第1候補を決める",
        steps=[
            ("01", "目的", "整理", "業務か転職か"),
            ("02", "職種", "確認", "営業・事務等"),
            ("03", "候補", "比較", "3〜4資格"),
            ("04", "第1資格", "学習", "開始"),
            ("05", "業務", "試行", "成果記録"),
            ("06", "2つ目", "検討", "必要なら"),
        ],
        highlight_index=3,
        loop_caption="業務成果を見て次の資格を選ぶ",
    ),
    "ai-certs-career-value": FlowSpec(
        title="AI資格のキャリア活用フロー",
        subtitle="目的と職種で活かし方を決める",
        steps=[
            ("01", "目的", "整理", "4類型"),
            ("02", "資格", "選定", "第1候補"),
            ("03", "学習", "・合格", "区切り"),
            ("04", "業務", "接続", "成果物"),
            ("05", "アピール", "", "履歴書等"),
            ("06", "次の", "一手", "継続"),
        ],
        highlight_index=3,
        loop_caption="成果を見て次の学習を決める",
    ),
    "ai-certs-for-sales": FlowSpec(
        title="営業職のAI資格活用フロー",
        subtitle="提案力・資料作成に接続する",
        steps=[
            ("01", "業務", "整理", "活用箇所"),
            ("02", "第1", "資格", "選定"),
            ("03", "学習", "・合格", ""),
            ("04", "提案", "・資料", "試行"),
            ("05", "顧客", "対応", "品質確認"),
            ("06", "キャリア", "記録", "アピール"),
        ],
        highlight_index=3,
        loop_caption="成果を記録し次の学習へ",
    ),
    "ai-certs-for-planning": FlowSpec(
        title="企画職のAI資格活用フロー",
        subtitle="事業企画・業務改善に接続する",
        steps=[
            ("01", "企画", "課題", "整理"),
            ("02", "第1", "資格", "選定"),
            ("03", "学習", "・合格", ""),
            ("04", "企画書", "・分析", "試行"),
            ("05", "検証", "PDCA", ""),
            ("06", "キャリア", "記録", "アピール"),
        ],
        highlight_index=3,
        loop_caption="検証結果で次の学習を決める",
    ),
    "ai-certs-for-marketing": FlowSpec(
        title="マーケのAI資格活用フロー",
        subtitle="生成AIとデータ分析に接続する",
        steps=[
            ("01", "施策", "整理", "KPI確認"),
            ("02", "第1", "資格", "選定"),
            ("03", "学習", "・合格", ""),
            ("04", "コンテンツ", "・分析", "試行"),
            ("05", "効果", "測定", "改善"),
            ("06", "キャリア", "記録", "アピール"),
        ],
        highlight_index=3,
        loop_caption="効果測定で次の学習へ",
    ),
    "ai-certs-for-admin": FlowSpec(
        title="事務職のAI資格活用フロー",
        subtitle="文書作成・業務効率化に接続する",
        steps=[
            ("01", "業務", "棚卸", "整理"),
            ("02", "第1", "資格", "選定"),
            ("03", "学習", "・合格", ""),
            ("04", "文書", "・定型", "試行"),
            ("05", "品質", "確認", "改善"),
            ("06", "キャリア", "記録", "アピール"),
        ],
        highlight_index=3,
        loop_caption="品質確認で次の学習へ",
    ),
    "ai-certs-for-hr": FlowSpec(
        title="人事総務のAI資格活用フロー",
        subtitle="採用・研修・ルール整備に接続する",
        steps=[
            ("01", "人事", "課題", "整理"),
            ("02", "第1", "資格", "選定"),
            ("03", "学習", "・合格", ""),
            ("04", "採用", "・研修", "試行"),
            ("05", "ルール", "確認", "改善"),
            ("06", "キャリア", "記録", "アピール"),
        ],
        highlight_index=3,
        loop_caption="ルール確認で次の学習へ",
    ),
    "ai-certs-for-accounting": FlowSpec(
        title="経理財務のAI資格活用フロー",
        subtitle="文案・要約と内部統制に接続する",
        steps=[
            ("01", "業務", "リスク", "整理"),
            ("02", "第1", "資格", "選定"),
            ("03", "学習", "・合格", ""),
            ("04", "文案", "・要約", "試行"),
            ("05", "数値", "確認", "改善"),
            ("06", "キャリア", "記録", "アピール"),
        ],
        highlight_index=3,
        loop_caption="数値確認で次の学習へ",
    ),
    "ai-certs-for-cs": FlowSpec(
        title="CSのAI資格活用フロー",
        subtitle="オンボーディング・解約防止に接続する",
        steps=[
            ("01", "顧客", "課題", "整理"),
            ("02", "第1", "資格", "選定"),
            ("03", "学習", "・合格", ""),
            ("04", "CS", "資料", "試行"),
            ("05", "品質", "確認", "改善"),
            ("06", "キャリア", "記録", "アピール"),
        ],
        highlight_index=3,
        loop_caption="品質確認で次の学習へ",
    ),
    "ai-certs-for-support": FlowSpec(
        title="サポートのAI資格活用フロー",
        subtitle="問合せ対応・FAQ整備に接続する",
        steps=[
            ("01", "問合せ", "業務", "整理"),
            ("02", "第1", "資格", "選定"),
            ("03", "学習", "・合格", ""),
            ("04", "回答", "文案", "試行"),
            ("05", "品質", "確認", "改善"),
            ("06", "キャリア", "記録", "アピール"),
        ],
        highlight_index=3,
        loop_caption="品質確認で次の学習へ",
    ),
    "ai-certs-for-pr": FlowSpec(
        title="広報のAI資格活用フロー",
        subtitle="プレスリリース・危機対応に接続する",
        steps=[
            ("01", "広報", "課題", "整理"),
            ("02", "第1", "資格", "選定"),
            ("03", "学習", "・合格", ""),
            ("04", "文案", "・素材", "試行"),
            ("05", "事実", "確認", "改善"),
            ("06", "キャリア", "記録", "アピール"),
        ],
        highlight_index=3,
        loop_caption="事実確認で次の学習へ",
    ),
    "ai-certs-for-newgrad": FlowSpec(
        title="新入社員のAI資格活用フロー",
        subtitle="入社前から配属後の業務へ接続する",
        steps=[
            ("01", "目的", "職種", "整理"),
            ("02", "第1", "資格", "選定"),
            ("03", "学習", "・合格", ""),
            ("04", "業務", "・研修", "試行"),
            ("05", "振り", "返", "改善"),
            ("06", "キャリア", "記録", "アピール"),
        ],
        highlight_index=3,
        loop_caption="振り返りで次の学習へ",
    ),
    "ai-certs-for-30s": FlowSpec(
        title="30代社会人のAI資格活用フロー",
        subtitle="本業と両立しながら業務・キャリアへ接続する",
        steps=[
            ("01", "目的", "整理", "現職か転職か"),
            ("02", "第1", "資格", "選定"),
            ("03", "学習", "・合格", "週次計画"),
            ("04", "業務", "試行", "成果記録"),
            ("05", "振り", "返", "改善"),
            ("06", "キャリア", "記録", "アピール"),
        ],
        highlight_index=3,
        loop_caption="振り返りで次の学習へ",
    ),
    "ai-certs-for-managers": FlowSpec(
        title="管理職のAI資格活用フロー",
        subtitle="チーム推進・ガバナンス・キャリアへ接続する",
        steps=[
            ("01", "役割", "整理", "推進か判断か"),
            ("02", "第1", "資格", "選定"),
            ("03", "学習", "・合格", ""),
            ("04", "チーム", "展開", "ルール整備"),
            ("05", "振り", "返", "改善"),
            ("06", "キャリア", "記録", "アピール"),
        ],
        highlight_index=3,
        loop_caption="振り返りで組織展開を更新",
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
