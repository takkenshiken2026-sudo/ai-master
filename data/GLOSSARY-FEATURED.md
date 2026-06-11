# 用語辞典「人気のページ」運用ルール

## 人気記事の追加・入れ替え

1. `data/glossary-featured.json` を編集する（**上から表示順**）
2. 用語 ID は `data/glossary-terms.csv` の `id` と一致させる
3. **公開済み**（`glossary/{id}/index.html` が存在）の用語だけ掲載される
4. 反映: `python3 tools/build_glossary.py`

```json
["claude-fable-5", "claude-mythos-5", "agi"]
```

## アイコンの決まり方（ビルド時に自動解決）

`build_glossary.py` が次の順で探す。最初に見つかったものを使う。

| 優先 | 条件 | 例 |
|------|------|-----|
| 1 | `data/glossary-icon-aliases.json` の `terms.{id}` | 例外だけここに書く |
| 2 | `assets/images/glossary/{id}.svg`（`.png` も可） | 概念用語の専用アイコン |
| 3 | CSV `notes` の `開発元:` → `vendors` マップ | Claude 系 → Anthropic |
| 4 | ID 接頭辞（`claude-` / `gpt-` / `gemini-`） | 開発元メモなしでも推定 |
| 5 | `assets/images/glossary/categories/{category}.svg` | AGI → `basics.svg` |
| — | いずれも無し | **アイコンなし**（テキストのみ） |

### ベンダーアイコン（`vendors`）

`tools/` 配下を再利用し、二重管理しない。

| 開発元 | パス |
|--------|------|
| Anthropic | `tools/anthropic.svg` |
| OpenAI | `tools/chatgpt/logo.svg` |
| Google | `tools/gemini/icon.svg` |

新ベンダーを足すときは `glossary-icon-aliases.json` の `vendors` に1行追加。

### カテゴリアイコン

`assets/images/glossary/categories/` に `{category}.svg` を置く。

- `basics` — 基礎・機械学習
- `models-tech` — モデル・技術
- `genai-use` — 生成AI活用
- `data-ops` — データ・運用
- `governance` — 倫理・ビジネス

## やらないこと

- `build_glossary.py` に ID と icon を直書きしない
- 1100行 CSV に icon 列を増やさない
- 人気に載せない用語のためにアイコンを大量追加しない

## チェックリスト

- [ ] `glossary-featured.json` の ID が typo していない
- [ ] 記事 HTML が公開済み
- [ ] 必要なら `glossary/{id}.svg` または `terms` alias を追加
- [ ] `python3 tools/build_glossary.py` 実行
- [ ] https://ai-master.jp/glossary/ で表示確認
