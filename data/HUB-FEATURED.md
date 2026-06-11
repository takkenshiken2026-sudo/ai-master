# ハブ人気カード — 運用ルール

用語辞典・学習ガイド・キャリアの「人気／注目」セクションの運用。アイコン資産一覧は [HUB-ICONS.md](./HUB-ICONS.md)。

## 用語辞典

### 人気記事

`data/glossary-featured.json` — ID を上から順に並べる。

```json
["claude-fable-5", "claude-mythos-5", "agi"]
```

反映: `python3 tools/build_glossary.py`

### アイコン

設定: `data/glossary-icon-aliases.json`

| 優先 | 条件 |
|------|------|
| 1 | `terms.{id}` 明示 |
| 2 | `glossary/{id}.svg` |
| 3 | CSV `notes` の開発元 → `vendors` |
| 4 | ID 接頭辞 `claude-` / `gpt-` / `gemini-` |
| 5 | `glossary/categories/{category}.svg` |

---

## 学習ガイド

### 人気記事

`data/guide-articles.csv` の **優先度「高」かつカテゴリ内先頭2件**が自動で `featured: true`（従来どおり）。

明示的に差し替えたい場合は将来 `guide-featured.json` を追加可能。

反映: `python3 tools/build_guide_index.py`

### アイコン

設定: `data/guide-icon-aliases.json`

| 優先 | 条件 |
|------|------|
| 1 | `terms.{id}` 明示 |
| 2 | `guide/{id}/icon.svg` |
| 3 | カテゴリが `g-kentei-*` → `guide/categories/g-kentei.svg` |
| 4 | カテゴリが `genai-*` → `guide/categories/genai.svg` |
| 5 | `guide/categories/{category}.svg` |

---

## キャリア

### 人気記事

`data/career-index.json` の各記事 `featured: true`（現状: 職種カテゴリ先頭3件など手動／JSON管理）。

### アイコン

設定: `data/career-icon-aliases.json`

| 優先 | 条件 |
|------|------|
| 1 | `terms.{id}` 明示 |
| 2 | `career/{id}/role*.png`（例: `role_flow.png`・47記事に既存） |
| 3 | `career/categories/{category}.svg` |

反映: `python3 tools/rebuild_career.py`

---

## 共通

- 解決実装: `tools/hub_icons.py`
- 表示: `assets/js/hub-featured-card.js`
- アイコンなしでもカードは表示される（テキストのみ）

## やらないこと

- 各ビルドスクリプトに icon パスを直書きしない
- hero.jpg をカードアイコンとして使わない（専用 icon / role-icon / カテゴリを使う）
