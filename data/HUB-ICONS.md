# ハブ人気カード — アイコン資産一覧

サイト内のカード用アイコンは `assets/images/` 以下に置き、ビルド時に `tools/hub_icons.py` がパスを解決します。運用手順は [HUB-FEATURED.md](./HUB-FEATURED.md) を参照。

## 1. AIツール（約96件）

`assets/images/tools/` — サービス・製品ロゴ

| 種類 | パス例 | 用途 |
|------|--------|------|
| ルート SVG | `anthropic.svg`, `openai.svg`, `google.svg`, `microsoft.svg` | ベンダー共通 |
| ツール別 | `{tool-id}/app-icon.png`, `logo.svg` | AIツール一覧・記事 |
| 共有 | `chatgpt/logo.svg`, `gemini/icon.svg` | 用語辞典の開発元マップ |

主なベンダー SVG: Anthropic, OpenAI, Google, Microsoft, Adobe, Vercel, Replit, Perplexity, Notion など。

## 2. 用語辞典

| 種類 | 場所 | ファイル |
|------|------|----------|
| カテゴリ | `glossary/categories/` | `basics`, `models-tech`, `genai-use`, `data-ops`, `governance` |
| 用語専用 | `glossary/{id}.svg` | 必要な概念用語のみ（例: 将来 `agi.svg`） |
| 設定 | `data/glossary-icon-aliases.json` | 例外・ベンダーマップ |

## 3. 学習ガイド

| 種類 | 場所 | ファイル |
|------|------|----------|
| 試験系 | `guide/categories/` | `g-kentei.svg`（G検定系カテゴリ共通）, `genai.svg`（生成AIパスポート系共通） |
| その他カテゴリ | `guide/categories/` | `compare`, `terms`, `audience`, `enterprise`, `trends`, `exam-tips`, `after-cert` |
| 記事専用 | `guide/{id}/icon.svg` | 任意（無ければカテゴリへフォールバック） |
| ヒーロー | `guide/{id}/hero.jpg` | **カードアイコンではない**（記事OG用） |
| 設定 | `data/guide-icon-aliases.json` | 例外 |

## 4. キャリア

| 種類 | 場所 | 件数 |
|------|------|------|
| 記事アイコン | `career/{id}/role-icon.png` | **47件**（職種・記事ごとの既存） |
| カテゴリ | `career/categories/` | `role`, `learn`, `move`, `market` |
| ヒーロー | `career/{id}/hero.jpg` | 記事ヘッダー用 |
| 設定 | `data/career-icon-aliases.json` | 例外 |

人気カードは **記事の role*.png を優先**し、無い記事はカテゴリアイコンを表示。

## 5. サイト共通

| ファイル | 用途 |
|----------|------|
| `assets/images/favicon.svg` | ブランド（汎用フォールバック向け） |
| `assets/images/og-default.jpg` | OGP デフォルト |

## 解決ロジック（共通）

`tools/hub_icons.py` — セクションごとに優先順が異なります。詳細は HUB-FEATURED.md。

```
例外 alias → 記事専用画像 → （用語のみ）開発元 → カテゴリ → なし
```

## 追加するとき

1. **カテゴリ単位で足りる** → `{section}/categories/{category}.svg` を置く
2. **1記事だけ差別化** → `{section}/{id}/icon.svg` または alias JSON
3. **ベンダー系用語** → `glossary-icon-aliases.json` の `vendors`（ツールロゴ再利用）
4. ビルド実行（下表）

| ハブ | コマンド |
|------|----------|
| 用語辞典 | `python3 tools/build_glossary.py` |
| 学習ガイド | `python3 tools/build_guide_index.py` |
| キャリア | `python3 tools/rebuild_career.py` |
